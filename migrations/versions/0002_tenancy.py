"""Tenant isolation: organization membership and organization ids everywhere.

Revision ID: 0002_tenancy
Revises: 0001_baseline
Create Date: 2026-10-14

Review finding F2 (P0).
  * organization_members(username, organization_id, role)
  * device_tokens.organization_id (push alerts are routed by id, not by name)
  * Backfill: every log row that only carried an organization NAME gets the
    matching organization_id (organizations are created for names that do
    not exist yet). Users who logged assessments for an organization become
    'supervisor' members of it, so nobody loses access to their own history.
Idempotent: safe to re-run on a partially migrated database.
"""
from datetime import datetime, timezone

from alembic import op

revision = "0002_tenancy"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None

MEMBERS_DDL = """CREATE TABLE IF NOT EXISTS organization_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    organization_id INTEGER NOT NULL,
    role TEXT NOT NULL DEFAULT 'supervisor',
    created_at TEXT NOT NULL,
    created_by TEXT,
    UNIQUE(username, organization_id)
)"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_device_tokens_org_id ON device_tokens(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_members_user ON organization_members(username)",
    "CREATE INDEX IF NOT EXISTS idx_members_org ON organization_members(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_audit_org ON audit_log(organization_id)",
]

NAMED_TABLES = ["assessment_log", "site_alert_log", "audit_log", "device_tokens"]


def _columns(bind, table):
    if bind.dialect.name == "postgresql":
        rows = bind.exec_driver_sql(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %(t)s AND table_schema = current_schema()", {"t": table})
        return {r[0] for r in rows}
    return {r[1] for r in bind.exec_driver_sql(f"PRAGMA table_info({table})")}


def upgrade() -> None:
    bind = op.get_bind()
    pg = bind.dialect.name == "postgresql"

    def run(sql, **params):
        if pg:
            sql = sql.replace(":v", "%(v)s").replace(":w", "%(w)s").replace(":x", "%(x)s")
        return bind.exec_driver_sql(sql, params) if params else bind.exec_driver_sql(sql)

    run(MEMBERS_DDL.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY") if pg else MEMBERS_DDL)
    if "organization_id" not in _columns(bind, "device_tokens"):
        run("ALTER TABLE device_tokens ADD COLUMN organization_id INTEGER")
    for stmt in INDEXES:
        run(stmt)

    # 1. Organizations for every name used anywhere.
    names = set()
    for table in NAMED_TABLES:
        for (name,) in run(f"SELECT DISTINCT organization FROM {table} "
                           "WHERE organization IS NOT NULL AND organization <> ''"):
            names.add(name)
    existing = {n for (n,) in run("SELECT name FROM organizations")}
    for name in sorted(names - existing):
        run("INSERT INTO organizations (name) VALUES (:v)", v=name)

    # 2. organization_id from the name, where it is missing.
    for table in NAMED_TABLES:
        run(f"UPDATE {table} SET organization_id = "
            "(SELECT o.id FROM organizations o WHERE o.name = " + table + ".organization) "
            "WHERE organization_id IS NULL AND organization IS NOT NULL AND organization <> ''")

    # 3. Keep every user's access to the organizations they already worked in.
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    pairs = set()
    for table in ("assessment_log", "device_tokens"):
        for user, org_id in run(f"SELECT DISTINCT username, organization_id FROM {table} "
                                "WHERE username IS NOT NULL AND username <> '' AND organization_id IS NOT NULL"):
            pairs.add((user, org_id))
    present = {(u, o) for u, o in run("SELECT username, organization_id FROM organization_members")}
    for user, org_id in sorted(pairs - present):
        run("INSERT INTO organization_members (username, organization_id, role, created_at, created_by) "
            "VALUES (:v, :w, 'supervisor', :x, 'migration 0002_tenancy')", v=user, w=org_id, x=now)


def downgrade() -> None:
    op.get_bind().exec_driver_sql("DROP TABLE IF EXISTS organization_members")
