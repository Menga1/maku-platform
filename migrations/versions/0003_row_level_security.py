"""PostgreSQL row-level security for every organization-owned table.

Revision ID: 0003_row_level_security
Revises: 0002_tenancy
Create Date: 2026-10-14

Pre-launch audit mandate, parts B3/B5 (defence in depth for finding F2).
tenancy.py already decides access in the application. This revision makes
PostgreSQL enforce the same rules, so a query that forgets its
organization filter (or an IDOR through a changed id) still cannot read or
change another organization's rows.

How identity reaches the database
---------------------------------
The application never trusts an organization id from the browser. For every
transaction, analytics._get_connection() sets two transaction-local settings
from the SERVER-SIDE session established by auth.require_login():

    maku.username        the signed-in username ('' when anonymous)
    maku.platform_admin  'on' for a platform administrator, else 'off'

Policies derive the organization role from organization_members (through the
SECURITY DEFINER function maku_org_role) - never from the request.

Roles
-----
Tables are owned by the migration role. The application must connect as a
separate role that does NOT own the tables and is neither superuser nor
BYPASSRLS (otherwise PostgreSQL skips RLS). analytics refuses to start in
strict mode if it is connected as such a role. scripts/init_db.py creates
the application role and passes its name in MAKU_APP_DB_ROLE; this revision
grants it table privileges.

audit_log is not tenant-filtered (it is read only by operators' scripts), but
the application role loses UPDATE, DELETE and TRUNCATE on it: at the database
level the hash-chained ledger becomes append-only.

SQLite (development only) has no row-level security; this revision is a
no-op there.
"""
import os
import re

from alembic import op

revision = "0003_row_level_security"
down_revision = "0002_tenancy"
branch_labels = None
depends_on = None

TENANT_TABLES = ("organizations", "organization_members", "projects", "sites",
                 "assessment_log", "site_alert_log", "device_tokens")
ALL_TABLES = TENANT_TABLES + ("audit_log", "users", "login_attempts", "user_consents",
                              "account_deletions")

FUNCTIONS = """
CREATE OR REPLACE FUNCTION maku_current_user() RETURNS text
    LANGUAGE sql STABLE
    AS $$ SELECT NULLIF(current_setting('maku.username', true), '') $$;

CREATE OR REPLACE FUNCTION maku_is_platform_admin() RETURNS boolean
    LANGUAGE sql STABLE
    AS $$ SELECT maku_current_user() IS NOT NULL
                 AND coalesce(current_setting('maku.platform_admin', true), '') = 'on' $$;

-- Organization role of the CURRENT user, read with the owner's rights so the
-- policies on organization_members do not recurse into themselves.
CREATE OR REPLACE FUNCTION maku_org_role(org integer) RETURNS text
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = {schema}, pg_temp
    AS $$ SELECT m.role FROM organization_members m
          WHERE m.organization_id = org AND m.username = maku_current_user() $$;

-- Same permission table as tenancy.PERMISSIONS.
CREATE OR REPLACE FUNCTION maku_can(org integer, action text) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = {schema}, pg_temp
    AS $$ SELECT CASE
            WHEN maku_current_user() IS NULL THEN false
            WHEN maku_is_platform_admin() THEN true
            WHEN org IS NULL THEN false
            ELSE coalesce(
                CASE maku_org_role(org)
                    WHEN 'viewer'     THEN action = 'read'
                    WHEN 'supervisor' THEN action IN ('read', 'write')
                    WHEN 'org_admin'  THEN action IN ('read', 'write', 'manage')
                END, false)
          END $$;

CREATE OR REPLACE FUNCTION maku_project_org(project integer) RETURNS integer
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = {schema}, pg_temp
    AS $$ SELECT p.organization_id FROM projects p WHERE p.id = project $$;

-- A push token belongs to whoever registers it last on the phone (the phone
-- proves possession of the token). Lets the registering or alert-sending user
-- drop the previous row even when it belonged to another account they cannot
-- otherwise see. Requires a signed-in caller.
CREATE OR REPLACE FUNCTION maku_release_device_token(tok text) RETURNS integer
    LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = {schema}, pg_temp
    AS $$
    DECLARE n integer;
    BEGIN
        IF maku_current_user() IS NULL THEN
            RAISE EXCEPTION 'maku_release_device_token requires a signed-in user'
                USING ERRCODE = 'insufficient_privilege';
        END IF;
        DELETE FROM device_tokens WHERE token = tok;
        GET DIAGNOSTICS n = ROW_COUNT;
        RETURN n;
    END $$;

-- Organization ownership of a row never changes after it is written.
CREATE OR REPLACE FUNCTION maku_keep_organization() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        IF NEW.organization_id IS DISTINCT FROM OLD.organization_id THEN
            RAISE EXCEPTION 'organization_id of % cannot be changed', TG_TABLE_NAME
                USING ERRCODE = 'insufficient_privilege';
        END IF;
        RETURN NEW;
    END $$;
"""

POLICIES = {
    "organizations": [
        "CREATE POLICY org_select ON organizations FOR SELECT USING (maku_can(id, 'read'))",
        "CREATE POLICY org_insert ON organizations FOR INSERT WITH CHECK (maku_is_platform_admin())",
        "CREATE POLICY org_update ON organizations FOR UPDATE USING (maku_is_platform_admin()) "
        "WITH CHECK (maku_is_platform_admin())",
        "CREATE POLICY org_delete ON organizations FOR DELETE USING (maku_is_platform_admin())",
    ],
    "organization_members": [
        "CREATE POLICY members_select ON organization_members FOR SELECT USING ("
        "maku_is_platform_admin() OR username = maku_current_user() OR maku_can(organization_id, 'manage'))",
        # An org_admin manages their organization but cannot appoint another org_admin.
        "CREATE POLICY members_insert ON organization_members FOR INSERT WITH CHECK ("
        "maku_is_platform_admin() OR (maku_can(organization_id, 'manage') AND role <> 'org_admin'))",
        "CREATE POLICY members_update ON organization_members FOR UPDATE USING ("
        "maku_is_platform_admin() OR (maku_can(organization_id, 'manage') AND role <> 'org_admin')) "
        "WITH CHECK (maku_is_platform_admin() OR (maku_can(organization_id, 'manage') AND role <> 'org_admin'))",
        # Own rows: account erasure removes the user's memberships.
        "CREATE POLICY members_delete ON organization_members FOR DELETE USING ("
        "maku_is_platform_admin() OR maku_can(organization_id, 'manage') OR username = maku_current_user())",
    ],
    "projects": [
        "CREATE POLICY projects_select ON projects FOR SELECT USING (maku_can(organization_id, 'read'))",
        "CREATE POLICY projects_insert ON projects FOR INSERT WITH CHECK (maku_can(organization_id, 'write'))",
        "CREATE POLICY projects_update ON projects FOR UPDATE USING (maku_can(organization_id, 'manage')) "
        "WITH CHECK (maku_can(organization_id, 'manage'))",
        "CREATE POLICY projects_delete ON projects FOR DELETE USING (maku_can(organization_id, 'manage'))",
    ],
    "sites": [
        "CREATE POLICY sites_select ON sites FOR SELECT USING (maku_can(maku_project_org(project_id), 'read'))",
        "CREATE POLICY sites_insert ON sites FOR INSERT WITH CHECK (maku_can(maku_project_org(project_id), 'write'))",
        "CREATE POLICY sites_update ON sites FOR UPDATE USING (maku_can(maku_project_org(project_id), 'manage')) "
        "WITH CHECK (maku_can(maku_project_org(project_id), 'manage'))",
        "CREATE POLICY sites_delete ON sites FOR DELETE USING (maku_can(maku_project_org(project_id), 'manage'))",
    ],
    # Assessment records are immutable: no UPDATE policy except for the
    # platform administrator. A user writes rows only under their own name.
    "assessment_log": [
        "CREATE POLICY assessments_select ON assessment_log FOR SELECT USING (maku_can(organization_id, 'read'))",
        "CREATE POLICY assessments_insert ON assessment_log FOR INSERT WITH CHECK ("
        "maku_can(organization_id, 'write') AND (username = maku_current_user() OR maku_is_platform_admin()))",
        "CREATE POLICY assessments_update ON assessment_log FOR UPDATE USING (maku_is_platform_admin()) "
        "WITH CHECK (maku_is_platform_admin())",
        "CREATE POLICY assessments_delete ON assessment_log FOR DELETE USING ("
        "maku_is_platform_admin() OR maku_can(organization_id, 'manage') OR username = maku_current_user())",
    ],
    # Safety alerts: anyone who can see the organization may record one (a
    # viewer's screen can raise a stop-work alert); alerts without an
    # organization are visible to platform administrators only.
    "site_alert_log": [
        "CREATE POLICY alerts_select ON site_alert_log FOR SELECT USING (maku_can(organization_id, 'read'))",
        "CREATE POLICY alerts_insert ON site_alert_log FOR INSERT WITH CHECK ("
        "maku_current_user() IS NOT NULL AND (organization_id IS NULL OR maku_can(organization_id, 'read')))",
        "CREATE POLICY alerts_update ON site_alert_log FOR UPDATE USING (maku_is_platform_admin()) "
        "WITH CHECK (maku_is_platform_admin())",
        "CREATE POLICY alerts_delete ON site_alert_log FOR DELETE USING (maku_is_platform_admin())",
    ],
    "device_tokens": [
        # Members' tokens are readable inside the organization so an alert
        # raised by one member reaches the others (push._tokens_for_organization).
        "CREATE POLICY tokens_select ON device_tokens FOR SELECT USING ("
        "maku_is_platform_admin() OR username = maku_current_user() OR maku_can(organization_id, 'read'))",
        "CREATE POLICY tokens_insert ON device_tokens FOR INSERT WITH CHECK ("
        "maku_is_platform_admin() OR (username = maku_current_user() AND maku_can(organization_id, 'read')))",
        "CREATE POLICY tokens_update ON device_tokens FOR UPDATE USING ("
        "maku_is_platform_admin() OR username = maku_current_user()) WITH CHECK ("
        "maku_is_platform_admin() OR (username = maku_current_user() AND maku_can(organization_id, 'read')))",
        "CREATE POLICY tokens_delete ON device_tokens FOR DELETE USING ("
        "maku_is_platform_admin() OR username = maku_current_user())",
    ],
}

OWNERSHIP_TRIGGERS = ("projects", "assessment_log", "site_alert_log", "device_tokens", "organization_members")

_ROLE_NAME = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


def _app_role() -> str | None:
    role = (os.environ.get("MAKU_APP_DB_ROLE") or "").strip()
    if not role:
        return None
    if not _ROLE_NAME.match(role):
        raise ValueError("MAKU_APP_DB_ROLE must be a plain lower-case PostgreSQL role name")
    return role


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    schema = bind.exec_driver_sql("SELECT current_schema()").scalar()
    if not _ROLE_NAME.match(schema):
        raise ValueError(f"unexpected schema name {schema!r}")
    op.execute(FUNCTIONS.replace("{schema}", schema))
    op.execute("REVOKE ALL ON FUNCTION maku_release_device_token(text) FROM PUBLIC")

    for table, policies in POLICIES.items():
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        for name in [p.split()[2] for p in policies]:
            op.execute(f"DROP POLICY IF EXISTS {name} ON {table}")
        for policy in policies:
            op.execute(policy)
    for table in OWNERSHIP_TRIGGERS:
        op.execute(f"DROP TRIGGER IF EXISTS keep_organization ON {table}")
        op.execute(f"CREATE TRIGGER keep_organization BEFORE UPDATE ON {table} "
                   f"FOR EACH ROW EXECUTE FUNCTION maku_keep_organization()")

    role = _app_role()
    if role:
        for statement in grant_statements(role, schema):
            op.execute(statement)


def grant_statements(role: str, schema: str) -> list[str]:
    """Least privilege for the application role. scripts/init_db.py also runs
    these on every start, so a re-created role always gets its grants back."""
    if not _ROLE_NAME.match(role) or not _ROLE_NAME.match(schema):
        raise ValueError("invalid role or schema name")
    return [
        f"GRANT USAGE ON SCHEMA {schema} TO {role}",
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON {', '.join(ALL_TABLES)} TO {role}",
        f"REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM {role}",
        f"REVOKE TRUNCATE ON {', '.join(ALL_TABLES)} FROM {role}",
        f"GRANT SELECT ON alembic_version TO {role}",
        f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema} TO {role}",
        f"GRANT EXECUTE ON FUNCTION maku_release_device_token(text) TO {role}",
    ]


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for table in OWNERSHIP_TRIGGERS:
        op.execute(f"DROP TRIGGER IF EXISTS keep_organization ON {table}")
    for table, policies in POLICIES.items():
        for name in [p.split()[2] for p in policies]:
            op.execute(f"DROP POLICY IF EXISTS {name} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    for fn in ("maku_keep_organization()", "maku_release_device_token(text)", "maku_project_org(integer)",
               "maku_can(integer, text)", "maku_org_role(integer)", "maku_is_platform_admin()",
               "maku_current_user()"):
        op.execute(f"DROP FUNCTION IF EXISTS {fn}")
