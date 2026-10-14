"""Tenant isolation (review finding F2, P0): one organization can never see,
create, change or receive another organization's data. These tests use real
memberships and real sessions - no administrator shortcut."""
import io
import os
import subprocess
import sys

import pandas as pd
import pytest
import streamlit as st

import accounts
import analytics
import db
import push
import tenancy
from risk_engine import calculate_solar_albedo_heat_risk

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ADMIN = tenancy.Principal("platform.admin", platform_admin=True)


def sign_in(username, role="supervisor"):
    """What auth.require_login() leaves in the session after a real login."""
    st.session_state.clear()
    st.session_state.update({"authenticated": True, "_auth_username": username, "_auth_role": role})


def result(temp=42):
    return calculate_solar_albedo_heat_risk(950, 9, temp, "silicon_pv_panels")


@pytest.fixture
def two_tenants(fresh_db):
    """ACME and Beta, each with a supervisor; ACME also has a viewer."""
    acme = tenancy.create_organization(ADMIN, "ACME")
    beta = tenancy.create_organization(ADMIN, "Beta")
    tenancy.set_membership(ADMIN, "alice", acme, "supervisor")
    tenancy.set_membership(ADMIN, "bob", beta, "supervisor")
    tenancy.set_membership(ADMIN, "victor", acme, "viewer")
    return {"acme": acme, "beta": beta}


def audit_events(event_type):
    df = analytics.get_audit_log_dataframe()
    return df[df["event_type"] == event_type]


class TestVisibility:
    def test_member_sees_only_their_organizations(self, two_tenants):
        sign_in("alice")
        assert analytics.list_organizations(st) == ["ACME"]
        sign_in("bob")
        assert analytics.list_organizations(st) == ["Beta"]

    def test_unauthenticated_session_sees_nothing(self, two_tenants):
        st.session_state.clear()
        assert analytics.list_organizations(st) == []
        assert analytics.get_org_context(st)["organization_id"] is None

    def test_platform_admin_sees_all(self, two_tenants):
        sign_in("root", role="admin")
        assert analytics.list_organizations(st) == ["ACME", "Beta"]

    def test_user_in_several_organizations(self, two_tenants):
        tenancy.set_membership(ADMIN, "consultant", two_tenants["acme"], "viewer")
        tenancy.set_membership(ADMIN, "consultant", two_tenants["beta"], "supervisor")
        sign_in("consultant")
        assert analytics.list_organizations(st) == ["ACME", "Beta"]
        assert analytics.set_org_context(st, organization="ACME")["role"] == "viewer"
        assert analytics.set_org_context(st, organization="Beta")["role"] == "supervisor"


class TestSelectingAnotherTenant:
    def test_cannot_select_another_organization_by_name(self, two_tenants):
        sign_in("bob")
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.set_org_context(st, organization="ACME")
        assert len(audit_events(tenancy.AUDIT_EVENT_ACCESS_DENIED)) == 1

    def test_cannot_select_another_organization_by_id(self, two_tenants):
        sign_in("bob")
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.set_org_context(st, organization_id=two_tenants["acme"])

    def test_typing_a_new_name_does_not_create_a_tenant(self, two_tenants):
        sign_in("bob")
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.set_org_context(st, organization="Brand New Corp")
        assert tenancy.organization_id_by_name("Brand New Corp") is None

    def test_tampered_session_context_is_rechecked_on_every_access(self, two_tenants):
        """Even if the stored context pointed at another tenant, every data
        function re-checks membership in the database."""
        sign_in("bob")
        analytics.set_org_context(st)
        st.session_state[analytics.ORG_CONTEXT_KEY] = {
            **st.session_state[analytics.ORG_CONTEXT_KEY], "organization": "ACME",
            "organization_id": two_tenants["acme"]}
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.log_assessment(st, result())
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.get_all_time_log_dataframe(st)
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.get_site_alert_log_dataframe(st)

    def test_removed_member_loses_access_immediately(self, two_tenants):
        sign_in("alice")
        analytics.set_org_context(st)
        analytics.log_assessment(st, result())
        tenancy.remove_membership(ADMIN, "alice", two_tenants["acme"])
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.log_assessment(st, result())   # same session, cached context

    def test_user_without_any_organization(self, two_tenants):
        sign_in("nobody")
        assert analytics.get_org_context(st)["organization_id"] is None
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.log_assessment(st, result())


class TestDataIsolation:
    def test_assessments_are_invisible_to_other_tenants(self, two_tenants):
        sign_in("alice")
        analytics.set_org_context(st)
        analytics.log_assessment(st, result(44))
        sign_in("bob")
        analytics.set_org_context(st)
        analytics.log_assessment(st, result(30))
        bob_view = analytics.get_all_time_log_dataframe(st)
        assert len(bob_view) == 1 and set(bob_view["organization"]) == {"Beta"}
        sign_in("alice")
        analytics.set_org_context(st)
        alice_view = analytics.get_all_time_log_dataframe(st)
        assert len(alice_view) == 1 and set(alice_view["organization"]) == {"ACME"}

    def test_log_assessment_refuses_an_organization_override(self, two_tenants):
        sign_in("alice")
        analytics.set_org_context(st)
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.log_assessment(st, result(), organization="Beta")

    def test_site_alerts_are_isolated(self, two_tenants):
        for user in ("alice", "bob"):
            sign_in(user)
            analytics.log_site_alert(f"{user}-worker", "physiological_strain", "CRITICAL", "Heat",
                                     **analytics.set_org_context(st))
        sign_in("alice")
        analytics.set_org_context(st)
        assert list(analytics.get_site_alert_log_dataframe(st)["worker_or_site_id"]) == ["alice-worker"]
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.get_site_alert_log_dataframe(st, all_organizations=True)

    def test_csv_import_cannot_write_into_another_tenant(self, two_tenants):
        sign_in("bob")
        analytics.set_org_context(st)
        csv = pd.DataFrame([{
            "timestamp": "2026-10-01T08:00:00+00:00", "module": "Solar (Desert)", "risk_band": "HIGH",
            "safety_override": True, "key_metric": 50.0, "primary_hazard": "Heat",
            "organization": "ACME", "project": "ACME secret project", "site": "Roof",
        }]).to_csv(index=False).encode()
        assert analytics.merge_uploaded_csv(st, io.BytesIO(csv)) == 1
        imported = analytics.get_all_time_log_dataframe(st)
        assert set(imported["organization"]) == {"Beta"}
        assert "ACME secret project" not in set(imported["project"])
        sign_in("alice")
        analytics.set_org_context(st)
        assert analytics.get_all_time_log_dataframe(st).empty

    def test_csv_merge_never_deletes_rows_of_another_organization(self, two_tenants):
        tenancy.set_membership(ADMIN, "consultant", two_tenants["acme"], "supervisor")
        tenancy.set_membership(ADMIN, "consultant", two_tenants["beta"], "supervisor")
        sign_in("consultant")
        analytics.set_org_context(st, organization="ACME")
        analytics.log_assessment(st, result())
        analytics.set_org_context(st, organization="Beta")
        csv = analytics.get_log_dataframe(st).to_csv(index=False).encode()  # empty Beta log
        analytics.merge_uploaded_csv(st, io.BytesIO(csv))
        analytics.set_org_context(st, organization="ACME")
        assert len(analytics.get_all_time_log_dataframe(st)) == 1

    def test_csv_import_row_limit(self, two_tenants, monkeypatch):
        monkeypatch.setattr("analytics.MAX_CSV_IMPORT_ROWS", 2)
        sign_in("alice")
        analytics.set_org_context(st)
        rows = [{"timestamp": f"2026-10-0{i}T08:00:00", "module": "Solar (Desert)", "risk_band": "LOW",
                 "safety_override": False, "key_metric": 1.0, "primary_hazard": "x"} for i in range(1, 4)]
        with pytest.raises(ValueError):
            analytics.merge_uploaded_csv(st, io.BytesIO(pd.DataFrame(rows).to_csv(index=False).encode()))


class TestRoles:
    def test_viewer_reads_but_cannot_write(self, two_tenants):
        sign_in("alice")
        analytics.set_org_context(st)
        analytics.log_assessment(st, result())
        sign_in("victor")
        analytics.set_org_context(st)
        assert len(analytics.get_all_time_log_dataframe(st)) == 1
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.log_assessment(st, result())
        with pytest.raises(tenancy.TenantAccessDenied):
            analytics.merge_uploaded_csv(st, io.BytesIO(b"timestamp\n"))

    def test_viewer_cannot_create_projects(self, two_tenants):
        sign_in("victor")
        ctx = analytics.set_org_context(st, project="Viewer-invented project")
        assert ctx["project_id"] is None

    def test_org_admin_manages_only_their_organization(self, two_tenants):
        tenancy.set_membership(ADMIN, "olga", two_tenants["acme"], "org_admin")
        olga = tenancy.Principal("olga")
        tenancy.set_membership(olga, "newhire", two_tenants["acme"], "supervisor")
        with pytest.raises(tenancy.TenantAccessDenied):
            tenancy.set_membership(olga, "newhire", two_tenants["beta"], "supervisor")
        with pytest.raises(tenancy.TenantAccessDenied):
            tenancy.set_membership(olga, "newhire", two_tenants["acme"], "org_admin")
        with pytest.raises(tenancy.TenantAccessDenied):
            tenancy.create_organization(olga, "Olga Inc")

    def test_supervisor_cannot_manage_members(self, two_tenants):
        with pytest.raises(tenancy.TenantAccessDenied):
            tenancy.set_membership(tenancy.Principal("alice"), "friend", two_tenants["acme"], "viewer")

    def test_invalid_role_rejected(self, two_tenants):
        with pytest.raises(tenancy.TenancyError):
            tenancy.set_membership(ADMIN, "x", two_tenants["acme"], "superuser")


class TestPushIsolation:
    def test_alerts_only_reach_current_members_of_that_organization(self, two_tenants):
        push.register_device("alice", "tok-alice", "android", two_tenants["acme"])
        push.register_device("bob", "tok-bob", "ios", two_tenants["beta"])
        assert push._tokens_for_organization(two_tenants["acme"]) == ["tok-alice"]
        assert push._tokens_for_organization(two_tenants["beta"]) == ["tok-bob"]
        with pytest.raises(tenancy.TenantAccessDenied):
            push.register_device("bob", "tok-bob-2", "ios", two_tenants["acme"])


class TestAccountDeletion:
    def test_memberships_are_erased_with_the_account(self, two_tenants):
        accounts.create_user("alice", "Alice-Password-1")
        accounts.erase_account_data("alice", requested_via="test")
        assert tenancy.list_memberships("alice") == []


class TestMigration0002:
    def test_backfills_ids_and_keeps_users_access(self, tmp_path):
        """A database from before tenancy: rows carry only organization NAMES."""
        path = tmp_path / "legacy.db"
        env = {k: v for k, v in os.environ.items() if k not in ("DATABASE_URL", "MAKU_ENV")}
        env["MAKU_DB_PATH"] = str(path)
        up = lambda rev: subprocess.run([sys.executable, "-m", "alembic", "upgrade", rev], cwd=ROOT,  # noqa: E731
                                         env=env, capture_output=True, text=True)
        assert up("0001_baseline").returncode == 0
        conn = analytics._Connection(db.raw_connection(db.sqlite_url(str(path))), "sqlite")
        with conn:
            for org, user in (("Legacy A", "ann"), ("Legacy B", "ben"), ("Legacy A", None)):
                conn.execute("INSERT INTO assessment_log (session_id, timestamp, module, organization, username) "
                             "VALUES ('s', '2026-01-01', 'Solar (Desert)', ?, ?)", (org, user))
            conn.execute("INSERT INTO site_alert_log (timestamp, alert_type, severity, message, organization) "
                         "VALUES ('2026-01-01', 'x', 'CRITICAL', 'm', 'Legacy B')")
        out = up("head")
        assert out.returncode == 0, out.stderr
        conn = analytics._Connection(db.raw_connection(db.sqlite_url(str(path))), "sqlite")
        with conn:
            assert conn.execute("SELECT COUNT(*) FROM assessment_log WHERE organization_id IS NULL").fetchone()[0] == 0
            assert conn.execute("SELECT COUNT(*) FROM site_alert_log WHERE organization_id IS NULL").fetchone()[0] == 0
            members = conn.execute("SELECT m.username, o.name FROM organization_members m "
                                   "JOIN organizations o ON o.id = m.organization_id ORDER BY 1").fetchall()
            assert [tuple(m) for m in members] == [("ann", "Legacy A"), ("ben", "Legacy B")]
        assert up("head").returncode == 0   # idempotent re-run
