"""Tenant-isolation matrix - pre-launch audit mandate C5 / B2 / B3.

Two synthetic organizations, A ("Org A") and B ("Org B"), each with its own
users and records. Every row of the mandate's matrix is a separately named
test, run at two layers:

  1. APPLICATION layer (SQLite and PostgreSQL): the functions the Streamlit
     pages call, with a real signed-in session (auth.require_login leaves the
     same session_state keys used by sign_in below).
  2. DATABASE layer (PostgreSQL only, MAKU_TEST_BACKEND=postgres): raw SQL
     sent as the APPLICATION role with A's identity, bypassing every Python
     check - proves row-level security (migration 0003) holds on its own.

scripts/audit_evidence.py turns the JUnit output of this file into
docs/audit/tenant_isolation_matrix.csv.
"""
import io
import os

import pandas as pd
import pytest
import streamlit as st

import analytics
import db
import push
import tenancy
from risk_engine import calculate_solar_albedo_heat_risk

PG_URL = os.environ.get("MAKU_TEST_PG_URL", "")
PG_OWNER_URL = os.environ.get("MAKU_TEST_PG_OWNER_URL", "")
USE_PG = os.environ.get("MAKU_TEST_BACKEND") == "postgres" and bool(PG_URL) and bool(PG_OWNER_URL)
ADMIN = tenancy.Principal("platform.admin", platform_admin=True)


def sign_in(username, role="supervisor"):
    st.session_state.clear()
    st.session_state.update({"authenticated": True, "_auth_username": username, "_auth_role": role})
    analytics.set_org_context(st)


def assessment(temp=42):
    return calculate_solar_albedo_heat_risk(950, 9, temp, "silicon_pv_panels")


@pytest.fixture
def orgs(fresh_db):
    """Org A (alice supervisor, ada viewer, amy org_admin) and Org B (bob
    supervisor), each with one assessment, one site alert, one device."""
    a = tenancy.create_organization(ADMIN, "Org A")
    b = tenancy.create_organization(ADMIN, "Org B")
    tenancy.set_membership(ADMIN, "alice", a, "supervisor")
    tenancy.set_membership(ADMIN, "ada", a, "viewer")
    tenancy.set_membership(ADMIN, "amy", a, "org_admin")
    tenancy.set_membership(ADMIN, "bob", b, "supervisor")
    for user, org in (("alice", a), ("bob", b)):
        sign_in(user)
        analytics.set_org_context(st, site=f"{user} site")   # creates a project and a site
        analytics.log_assessment(st, assessment())
        assert analytics.log_site_alert(f"{user}-w1", "physiological_strain", "CRITICAL", "Heat",
                                        **analytics.get_org_context(st))
        push.register_device(user, f"token-{user}", "android", org)
    st.session_state.clear()
    return {"A": a, "B": b}


# =========================================================================
# 1. Application layer
# =========================================================================
class TestApplicationMatrix:
    def test_read_own_record(self, orgs):
        sign_in("alice")
        rows = analytics.get_all_time_log_dataframe(st)
        assert len(rows) == 1 and set(rows["organization"]) == {"Org A"}
        sign_in("ada")   # viewer: read allowed by role
        assert len(analytics.get_all_time_log_dataframe(st)) == 1

    def test_cross_tenant_read_by_id(self, orgs):
        sign_in("alice")
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.set_org_context(st, organization_id=orgs["B"])
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.set_org_context(st, organization="Org B")

    def test_cross_tenant_read_with_tampered_session_context(self, orgs):
        sign_in("alice")
        st.session_state[analytics.ORG_CONTEXT_KEY] = {
            **st.session_state[analytics.ORG_CONTEXT_KEY], "organization_id": orgs["B"], "organization": "Org B"}
        for read in (analytics.get_all_time_log_dataframe, analytics.get_site_alert_log_dataframe,
                     analytics.get_log_dataframe):
            with pytest.raises(tenancy.TenantAccessDenied):
                read(st)

    def test_spoof_tenant_id_on_create(self, orgs):
        sign_in("alice")
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.log_assessment(st, assessment(), organization="Org B")
        csv = pd.DataFrame([{"timestamp": "2026-10-01T08:00:00+00:00", "module": "Solar (Desert)",
                             "risk_band": "HIGH", "safety_override": True, "key_metric": 50.0,
                             "primary_hazard": "Heat", "organization": "Org B", "project": "B project"}])
        analytics.merge_uploaded_csv(st, io.BytesIO(csv.to_csv(index=False).encode()))
        sign_in("bob")
        assert len(analytics.get_all_time_log_dataframe(st)) == 1   # B unchanged: the row went to A

    def test_spoof_tenant_id_on_device_registration(self, orgs):
        sign_in("alice")
        with pytest.raises(tenancy.TenantAccessDenied):
            push.register_device("alice", "token-alice-2", "ios", orgs["B"])

    def test_insufficient_role_cannot_write(self, orgs):
        sign_in("ada")
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.log_assessment(st, assessment())

    def test_ownership_update_is_impossible(self, orgs):
        """No application function changes the organization of a stored
        record: a membership change is the only way rows move between
        views, and it moves nothing."""
        sign_in("alice")
        before = analytics.get_all_time_log_dataframe(st)
        tenancy.set_membership(ADMIN, "alice", orgs["B"], "supervisor")
        sign_in("alice")
        analytics.set_org_context(st, organization="Org B")
        assert len(analytics.get_all_time_log_dataframe(st)) == 1    # still only B's own row
        analytics.set_org_context(st, organization="Org A")
        assert len(analytics.get_all_time_log_dataframe(st)) == len(before)

    def test_cross_tenant_delete(self, orgs):
        """The only delete path (CSV merge) is scoped to the session's own
        organization: merging an empty file in A leaves B's rows intact."""
        sign_in("alice")
        empty = pd.DataFrame(columns=[c for c in analytics.LOG_COLUMNS]).to_csv(index=False).encode()
        analytics.merge_uploaded_csv(st, io.BytesIO(empty))
        sign_in("bob")
        assert len(analytics.get_all_time_log_dataframe(st)) == 1

    def test_export_across_tenants(self, orgs):
        sign_in("alice")
        excel = analytics.build_monthly_excel(analytics.get_all_time_log_dataframe(st))
        assert b"Org B" not in excel
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.get_site_alert_log_dataframe(st, all_organizations=True)
        with analytics.acting_as(tenancy.Principal("alice")):
            assert push._tokens_for_organization(orgs["A"]) == ["token-alice"]

    def test_membership_revoked(self, orgs):
        sign_in("alice")
        tenancy.remove_membership(ADMIN, "alice", orgs["A"])
        with pytest.raises(tenancy.TenantAccessDenied):          # same session, next request
            analytics.get_all_time_log_dataframe(st)
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.log_assessment(st, assessment())

    def test_unauthenticated_has_no_access(self, orgs):
        st.session_state.clear()
        assert analytics.list_organizations(st) == []
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.get_all_time_log_dataframe(st)

    def test_org_admin_cannot_escalate(self, orgs):
        amy = tenancy.Principal("amy")
        with pytest.raises(tenancy.TenantAccessDenied):
            tenancy.set_membership(amy, "alice", orgs["A"], "org_admin")
        with pytest.raises(tenancy.TenantAccessDenied):
            tenancy.set_membership(amy, "amy", orgs["B"], "supervisor")
        with pytest.raises(tenancy.TenantAccessDenied):
            tenancy.create_organization(amy, "Amy Corp")


# =========================================================================
# 2. Database layer - PostgreSQL row-level security, no Python checks
# =========================================================================
TENANT_TABLES = ("organizations", "organization_members", "projects", "sites",
                 "assessment_log", "site_alert_log", "device_tokens")
IN_ORG = {"organizations": "id = %s",
          "sites": "project_id IN (SELECT id FROM projects WHERE organization_id = %s)"}


def in_org(table):
    return IN_ORG.get(table, "organization_id = %s")


class _Sql:
    """Raw SQL as the APPLICATION role with a given identity."""

    def __init__(self, url, username, admin=False):
        self.raw = db.raw_connection(url)
        self.cur = self.raw.cursor()
        if username is not None:
            self.cur.execute("SELECT set_config('maku.username', %s, false), "
                             "set_config('maku.platform_admin', %s, false)", (username, "on" if admin else "off"))

    def one(self, sql, params=()):
        self.cur.execute(sql, params)
        return self.cur.fetchone()

    def rows(self, sql, params=()):
        self.cur.execute(sql, params)
        return self.cur.fetchall()

    def fails(self, sql, params=()):
        import psycopg2
        try:
            self.cur.execute("SAVEPOINT t")
            self.cur.execute(sql, params)
        except psycopg2.Error as exc:
            self.cur.execute("ROLLBACK TO SAVEPOINT t")
            return exc.pgcode
        self.cur.execute("RELEASE SAVEPOINT t")
        return None

    def close(self):
        self.raw.rollback()
        # identity was set at session level for this test connection
        self.cur.execute("RESET maku.username")
        self.cur.execute("RESET maku.platform_admin")
        self.raw.commit()
        self.raw.close()


@pytest.fixture
def sql(orgs):
    opened = []

    def open_as(username, admin=False, url=PG_URL):
        conn = _Sql(url, username, admin)
        opened.append(conn)
        return conn

    yield open_as
    for conn in opened:
        conn.close()


def owner_count(table, where="TRUE", params=()):
    raw = db.raw_connection(PG_OWNER_URL)
    try:
        cur = raw.cursor()
        cur.execute(f"SELECT count(*) FROM {table} WHERE {where}", params)
        return cur.fetchone()[0]
    finally:
        raw.rollback()
        raw.close()


@pytest.mark.skipif(not USE_PG, reason="row-level security exists on PostgreSQL only "
                                        "(MAKU_TEST_BACKEND=postgres, MAKU_TEST_PG_URL, MAKU_TEST_PG_OWNER_URL)")
class TestDatabaseRowLevelSecurity:
    @pytest.mark.parametrize("table", TENANT_TABLES)
    def test_read_own_record(self, sql, orgs, table):
        a = sql("alice")
        assert a.one(f"SELECT count(*) FROM {table} WHERE {in_org(table)}", (orgs["A"],))[0] >= 1

    @pytest.mark.parametrize("table", TENANT_TABLES)
    def test_cross_tenant_read(self, sql, orgs, table):
        a = sql("alice")
        # Org B's rows exist (owner view) but are invisible to alice even with
        # an explicit WHERE on B's id - a classic IDOR attempt.
        assert owner_count(table, in_org(table), (orgs["B"],)) >= 1
        assert a.one(f"SELECT count(*) FROM {table} WHERE {in_org(table)}", (orgs["B"],))[0] == 0

    @pytest.mark.parametrize("table", TENANT_TABLES)
    def test_no_identity_sees_nothing(self, sql, table):
        anonymous = sql(None)
        assert anonymous.one(f"SELECT count(*) FROM {table}")[0] == 0

    def test_spoof_tenant_id_on_insert(self, sql, orgs):
        a = sql("alice")
        assert a.fails("INSERT INTO assessment_log (session_id, timestamp, module, organization_id, username) "
                       "VALUES ('x', '2026-10-14', 'Solar (Desert)', %s, 'alice')", (orgs["B"],)) == "42501"
        assert a.fails("INSERT INTO projects (organization_id, name) VALUES (%s, 'planted')", (orgs["B"],)) == "42501"
        assert a.fails("INSERT INTO site_alert_log (timestamp, alert_type, severity, message, organization_id) "
                       "VALUES ('2026-10-14', 'x', 'CRITICAL', 'x', %s)", (orgs["B"],)) == "42501"
        assert a.fails("INSERT INTO device_tokens (username, token, platform, organization_id, created_at, "
                       "updated_at) VALUES ('alice', 't', 'ios', %s, 'n', 'n')", (orgs["B"],)) == "42501"
        assert a.fails("INSERT INTO organization_members (username, organization_id, role, created_at) "
                       "VALUES ('alice', %s, 'org_admin', 'n')", (orgs["B"],)) == "42501"
        assert a.fails("INSERT INTO organizations (name) VALUES ('Alice Corp')") == "42501"

    def test_spoof_author_on_insert(self, sql, orgs):
        a = sql("alice")
        assert a.fails("INSERT INTO assessment_log (session_id, timestamp, module, organization_id, username) "
                       "VALUES ('x', '2026-10-14', 'Solar (Desert)', %s, 'bob')", (orgs["A"],)) == "42501"

    def test_ownership_update(self, sql, orgs):
        a = sql("alice")
        a.cur.execute("UPDATE assessment_log SET organization_id = %s WHERE organization_id = %s",
                      (orgs["B"], orgs["A"]))
        assert a.cur.rowcount == 0                       # records are immutable for members
        a.cur.execute("UPDATE assessment_log SET risk_band = 'LOW'")
        assert a.cur.rowcount == 0
        admin = sql("root", admin=True)
        assert admin.fails("UPDATE assessment_log SET organization_id = %s WHERE organization_id = %s",
                           (orgs["B"], orgs["A"])) == "42501"   # trigger: not even the platform admin

    def test_cross_tenant_delete(self, sql, orgs):
        a = sql("alice")
        for table in ("assessment_log", "site_alert_log", "device_tokens", "organization_members", "projects"):
            a.cur.execute(f"DELETE FROM {table} WHERE organization_id = %s", (orgs["B"],))
            assert a.cur.rowcount == 0, table
        a.raw.commit()
        assert owner_count("assessment_log", "organization_id = %s", (orgs["B"],)) == 1

    def test_insufficient_role(self, sql, orgs):
        viewer = sql("ada")
        assert viewer.fails("INSERT INTO assessment_log (session_id, timestamp, module, organization_id, "
                            "username) VALUES ('x', '2026-10-14', 'Solar (Desert)', %s, 'ada')", (orgs["A"],)) == "42501"
        org_admin = sql("amy")
        assert org_admin.fails("INSERT INTO organization_members (username, organization_id, role, created_at) "
                               "VALUES ('mallory', %s, 'org_admin', 'n')", (orgs["A"],)) == "42501"
        assert org_admin.fails("UPDATE organization_members SET role = 'org_admin' WHERE username = 'alice'") \
            in (None, "42501")
        assert owner_count("organization_members", "username = 'alice' AND role = 'org_admin'") == 0

    def test_membership_revoked(self, sql, orgs):
        tenancy.remove_membership(ADMIN, "alice", orgs["A"])
        a = sql("alice")
        assert a.one("SELECT count(*) FROM assessment_log")[0] == 0
        assert a.one("SELECT count(*) FROM organizations")[0] == 0

    def test_audit_log_is_append_only_for_the_application(self, sql):
        a = sql("alice")
        analytics.log_audit_event("TEST", actor="alice")
        assert a.fails("UPDATE audit_log SET detail = 'rewritten'") == "42501"
        assert a.fails("DELETE FROM audit_log") == "42501"
        assert a.fails("TRUNCATE audit_log") == "42501"

    def test_release_token_requires_identity(self, sql):
        anonymous = sql(None)
        assert anonymous.fails("SELECT maku_release_device_token('token-bob')") == "42501"
        assert owner_count("device_tokens", "token = 'token-bob'") == 1

    def test_application_role_cannot_bypass(self, sql):
        a = sql("alice")
        assert a.fails("SET row_security = off; SELECT count(*) FROM assessment_log") is not None \
            or a.one("SELECT count(*) FROM assessment_log")[0] == 1
        superuser, bypass = a.one("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
        assert not superuser and not bypass
        assert a.fails("ALTER TABLE assessment_log DISABLE ROW LEVEL SECURITY") == "42501"
