"""Self-service sign-up ("Create a free account"): a new account gets its
own private workspace, can only see that workspace, is rate-limited per
network, can be turned off, and is fully removed by account deletion."""
import pytest
import streamlit as st

import accounts
import analytics
import tenancy

STRONG = "Safe-Work-2026!"


def sign_in(username):
    st.session_state.clear()
    st.session_state.update({"authenticated": True, "_auth_username": username, "_auth_role": "supervisor"})


def test_signup_creates_user_with_private_workspace(fresh_db):
    name = accounts.register_self_service("new.user", STRONG, "new@example.com", "10.0.0.1")
    org_id = tenancy.create_personal_workspace(name)

    user = accounts.get_user("new.user")
    assert user["role"] == "supervisor" and user["email"] == "new@example.com"
    assert accounts.verify_password(user["password_hash"], STRONG)
    assert tenancy.membership_role("new.user", org_id) == "org_admin"

    sign_in("new.user")
    orgs = analytics.list_organizations(st)
    assert len(orgs) == 1 and orgs[0].startswith("Personal workspace ")
    assert "new.user" not in orgs[0]          # no personal data in the workspace name


def test_two_signups_never_share_a_workspace(fresh_db):
    a = tenancy.create_personal_workspace(accounts.register_self_service("user.a", STRONG, None, "10.0.0.2"))
    b = tenancy.create_personal_workspace(accounts.register_self_service("user.b", STRONG, None, "10.0.0.3"))
    assert a != b
    assert tenancy.membership_role("user.a", b) is None
    assert tenancy.membership_role("user.b", a) is None


def test_signup_rejects_weak_password_and_duplicate(fresh_db):
    with pytest.raises(accounts.AccountError):
        accounts.register_self_service("weak.user", "short", None, "10.0.0.4")
    accounts.register_self_service("taken", STRONG, None, "10.0.0.4")
    with pytest.raises(accounts.AccountError):
        accounts.register_self_service("taken", STRONG, None, "10.0.0.5")


def test_signup_is_rate_limited_per_address(fresh_db, monkeypatch):
    monkeypatch.setattr(accounts, "SIGNUP_MAX_PER_IP", 2)
    accounts.register_self_service("rate.one", STRONG, None, "10.9.9.9")
    accounts.register_self_service("rate.two", STRONG, None, "10.9.9.9")
    with pytest.raises(accounts.AccountError):
        accounts.register_self_service("rate.three", STRONG, None, "10.9.9.9")
    accounts.register_self_service("rate.four", STRONG, None, "10.9.9.8")   # another address is fine
    # sign-ups never count toward the sign-in lockout of that address
    assert accounts.lockout_status("someone", "10.9.9.9") == (False, 0)


def test_signup_can_be_turned_off(fresh_db, monkeypatch):
    monkeypatch.setenv("MAKU_ALLOW_SIGNUP", "0")
    assert not accounts.self_signup_enabled()
    with pytest.raises(accounts.AccountError):
        accounts.register_self_service("blocked", STRONG, None, "10.0.0.6")


def test_deleting_a_signed_up_account_removes_it_and_its_membership(fresh_db):
    name = accounts.register_self_service("leaving", STRONG, None, "10.0.0.7")
    org_id = tenancy.create_personal_workspace(name)
    accounts.delete_account("leaving", STRONG)
    assert accounts.get_user("leaving") is None
    assert tenancy.membership_role("leaving", org_id) is None
