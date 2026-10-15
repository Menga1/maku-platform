"""Passwords and sessions (review finding F3, P0)."""
import os
import subprocess
import sys
import time

import bcrypt
import pytest
import streamlit as st

import accounts
import auth

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STRONG = "Correct-Horse-Battery-9"


def legacy_bcrypt(password: str) -> str:
    return "bcrypt:" + bcrypt.hashpw(password.encode(), bcrypt.gensalt(4)).decode()


class TestHashing:
    def test_new_hashes_are_argon2id_with_rfc9106_parameters(self):
        stored = accounts.hash_password(STRONG)
        assert stored.startswith("argon2:$argon2id$v=19$m=65536,t=3,p=4$")
        assert accounts.verify_password(stored, STRONG)
        assert not accounts.verify_password(stored, STRONG + "x")
        assert not accounts.needs_rehash(stored)

    def test_each_hash_is_salted(self):
        assert accounts.hash_password(STRONG) != accounts.hash_password(STRONG)

    def test_bcrypt_is_verified_and_flagged_for_upgrade(self):
        stored = legacy_bcrypt(STRONG)
        assert accounts.verify_password(stored, STRONG)
        assert accounts.needs_rehash(stored)

    @pytest.mark.parametrize("stored", ["plain", "sha256:" + "a" * 64, "", "argon2:not-a-hash", "bcrypt:junk"])
    def test_anything_else_fails_closed(self, stored):
        assert accounts.verify_password(stored, "plain") is False

    def test_passwords_longer_than_72_bytes_work(self):
        """bcrypt crashed account creation for these (ValueError)."""
        long_pw = "Aa1!" + "x" * 96
        stored = accounts.hash_password(long_pw)
        assert accounts.verify_password(stored, long_pw)
        assert not accounts.verify_password(stored, long_pw[:72])   # no silent truncation

    def test_maximum_length(self):
        with pytest.raises(accounts.AccountError):
            accounts.hash_password("Aa1!" + "x" * 300)
        assert not accounts.verify_password(accounts.hash_password(STRONG), "x" * 5000)

    @pytest.mark.parametrize("password,ok", [
        (STRONG, True), ("Magni109", False), ("alllowercaseletters", False), ("Aa1!" * 70, False)])
    def test_policy(self, password, ok):
        assert (accounts.password_policy_problems(password) == []) is ok


class TestUpgradeOnSignIn:
    def test_database_bcrypt_account_is_upgraded_at_next_sign_in(self, fresh_db, monkeypatch):
        monkeypatch.setattr(auth.st, "secrets", {})
        accounts.create_user("legacy.user", STRONG)
        with accounts._conn() as conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE username = 'legacy.user'",
                         (legacy_bcrypt(STRONG),))
        assert auth._verify_credentials("legacy.user", STRONG)
        stored = accounts.get_user("legacy.user")["password_hash"]
        assert stored.startswith("argon2:")
        assert auth._verify_credentials("legacy.user", STRONG)   # still signs in after the upgrade

    def test_failed_sign_in_does_not_upgrade(self, fresh_db, monkeypatch):
        monkeypatch.setattr(auth.st, "secrets", {})
        accounts.create_user("legacy.user", STRONG)
        old = legacy_bcrypt(STRONG)
        with accounts._conn() as conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE username = 'legacy.user'", (old,))
        assert not auth._verify_credentials("legacy.user", "wrong")
        assert accounts.get_user("legacy.user")["password_hash"] == old


class TestDeploymentAccounts:
    def test_bcrypt_deployment_account_still_signs_in(self, fresh_db, monkeypatch):
        monkeypatch.setattr(auth.st, "secrets", {"auth": {"users": {"ops": legacy_bcrypt(STRONG)}}})
        assert auth._verify_credentials("ops", STRONG)
        assert st.session_state["_auth_role"] == "admin"

    def test_weak_password_is_a_warning_outside_production(self, fresh_db, monkeypatch):
        monkeypatch.setattr(auth.st, "secrets", {"auth": {"users": {"MENGA": accounts.hash_password("Magni109")}}})
        assert auth._verify_credentials("MENGA", "Magni109")
        assert "at least 12" in st.session_state["_auth_weak_password_warning"]

    def test_weak_password_is_refused_in_production(self, fresh_db, monkeypatch):
        monkeypatch.setenv("MAKU_ENV", "production")
        monkeypatch.setattr(auth.st, "secrets", {"auth": {"users": {"MENGA": accounts.hash_password("Magni109")}}})
        assert not auth._verify_credentials("MENGA", "Magni109")
        assert st.session_state["_auth_refused_reason"] == "weak_deployment_password"

    def test_strong_password_accepted_in_production(self, fresh_db, monkeypatch):
        monkeypatch.setenv("MAKU_ENV", "production")
        monkeypatch.setattr(auth.st, "secrets", {"auth": {"users": {"ops": accounts.hash_password(STRONG)}}})
        assert auth._verify_credentials("ops", STRONG)


class TestSessions:
    def _signed_in(self, last_seen_minutes_ago, login_minutes_ago=1):
        now = time.time()
        st.session_state.update({"authenticated": True, "_auth_username": "u", "_auth_role": "supervisor",
                                 "_auth_login_at": now - login_minutes_ago * 60,
                                 "_auth_last_seen": now - last_seen_minutes_ago * 60})

    def test_idle_detection(self, fresh_db):
        self._signed_in(last_seen_minutes_ago=auth.SESSION_IDLE_MINUTES + 1)
        assert auth._session_idle()
        self._signed_in(last_seen_minutes_ago=1)
        assert not auth._session_idle()

    def test_idle_session_is_signed_out(self, fresh_db, monkeypatch):
        self._signed_in(last_seen_minutes_ago=auth.SESSION_IDLE_MINUTES + 5)
        monkeypatch.setattr(auth.st, "secrets", {})

        class Stopped(Exception):
            pass

        def stop():
            raise Stopped

        monkeypatch.setattr(auth.st, "stop", stop)
        with pytest.raises(Stopped):
            auth.require_login()
        assert st.session_state["authenticated"] is False
        assert "_auth_username" not in st.session_state or not st.session_state["_auth_username"]

    def test_activity_keeps_the_session_alive(self, fresh_db):
        self._signed_in(last_seen_minutes_ago=5)
        before = st.session_state["_auth_last_seen"]
        auth.require_login()                    # returns for a live session
        assert st.session_state["_auth_last_seen"] > before

    def test_absolute_limit_still_applies(self, fresh_db):
        self._signed_in(last_seen_minutes_ago=1, login_minutes_ago=auth.SESSION_TIMEOUT_MINUTES + 1)
        assert auth._session_expired()


class TestCredentialAudit:
    def test_reports_formats_without_printing_hashes(self, tmp_path):
        argon = accounts.hash_password(STRONG)
        old = legacy_bcrypt(STRONG)
        secrets = tmp_path / "secrets.toml"
        secrets.write_text(f'[auth.users]\nmodern = "{argon}"\nlegacy = "{old}"\nunsafe = "hunter2"\n')
        out = subprocess.run([sys.executable, "scripts/audit_credentials.py", "--secrets", str(secrets),
                              "--no-database"], cwd=ROOT, capture_output=True, text=True)
        assert out.returncode == 1                       # one REJECTED account
        lines = {line.split()[1]: line.split()[0] for line in out.stdout.splitlines() if line[:1].isupper()
                 and len(line.split()) > 1 and line.split()[0] in ("OK", "UPGRADE", "REJECTED")}
        assert lines == {"modern": "OK", "legacy": "UPGRADE", "unsafe": "REJECTED"}
        for secret in (argon, old, "hunter2", argon[20:40]):
            assert secret not in out.stdout + out.stderr

    def test_clean_configuration_exits_0(self, tmp_path):
        secrets = tmp_path / "secrets.toml"
        secrets.write_text(f'[auth.users]\nmodern = "{accounts.hash_password(STRONG)}"\n')
        out = subprocess.run([sys.executable, "scripts/audit_credentials.py", "--secrets", str(secrets),
                              "--no-database"], cwd=ROOT, capture_output=True, text=True)
        assert out.returncode == 0, out.stdout


class TestSessionRevocation:
    """Audit mandate B4/B5: access after a password change, account deletion
    or role change ends on the next request of every other live session."""

    def _sign_in(self, monkeypatch, username, password):
        monkeypatch.setattr(auth.st, "secrets", {})
        st.session_state.clear()
        assert auth._verify_credentials(username, password)
        now = time.time()
        st.session_state.update({"authenticated": True, "_auth_username": username,
                                 "_auth_login_at": now, "_auth_last_seen": now})

    def test_live_session_is_valid(self, fresh_db, monkeypatch):
        accounts.create_user("sam.site", STRONG)
        self._sign_in(monkeypatch, "sam.site", STRONG)
        assert auth._session_revoked() is None
        auth.require_login()                         # returns: still signed in
        assert st.session_state["authenticated"] is True

    def test_password_changed_elsewhere_ends_this_session(self, fresh_db, monkeypatch):
        accounts.create_user("sam.site", STRONG)
        self._sign_in(monkeypatch, "sam.site", STRONG)
        accounts.change_password("sam.site", STRONG, STRONG + "-New")
        assert auth._session_revoked() == "password changed"

    def test_deleted_account_ends_this_session(self, fresh_db, monkeypatch):
        accounts.create_user("sam.site", STRONG)
        self._sign_in(monkeypatch, "sam.site", STRONG)
        accounts.erase_account_data("sam.site", requested_via="test")
        assert auth._session_revoked() == "account deleted or deactivated"

    def test_role_change_ends_this_session(self, fresh_db, monkeypatch):
        accounts.create_user("sam.site", STRONG)
        self._sign_in(monkeypatch, "sam.site", STRONG)
        with accounts._conn() as conn:
            conn.execute("UPDATE users SET role = 'admin' WHERE username = 'sam.site'")
        assert auth._session_revoked() == "role changed"

    def test_revoked_session_is_signed_out_and_audited(self, fresh_db, monkeypatch):
        accounts.create_user("sam.site", STRONG)
        self._sign_in(monkeypatch, "sam.site", STRONG)
        accounts.change_password("sam.site", STRONG, STRONG + "-New")

        class Stopped(Exception):
            pass

        def stop():
            raise Stopped

        monkeypatch.setattr(auth.st, "stop", stop)
        with pytest.raises(Stopped):
            auth.require_login()
        assert st.session_state["authenticated"] is False
        import analytics
        with analytics.system_context():
            events = analytics.get_audit_log_dataframe()
        assert "SESSION_REVOKED" in set(events["event_type"])

    def test_deployment_credential_rotation_ends_sessions(self, fresh_db, monkeypatch):
        monkeypatch.setattr(auth.st, "secrets", {"auth": {"users": {"ops": accounts.hash_password(STRONG)}}})
        st.session_state.clear()
        assert auth._verify_credentials("ops", STRONG)
        st.session_state.update({"authenticated": True, "_auth_username": "ops"})
        assert auth._session_revoked() is None
        monkeypatch.setattr(auth.st, "secrets", {"auth": {"users": {"ops": accounts.hash_password(STRONG + "2")}}})
        assert auth._session_revoked() == "deployment credential changed"


class TestNoFastHashes:
    """Mandate B4: no plaintext, reversible or fast-hash password storage in
    any code path - verified through the verification function itself."""

    @pytest.mark.parametrize("stored", [
        "Correct-Horse-Battery-9",                                   # plaintext
        "sha256:" + __import__("hashlib").sha256(b"Correct-Horse-Battery-9").hexdigest(),
        __import__("hashlib").sha256(b"Correct-Horse-Battery-9").hexdigest(),
        "md5:" + __import__("hashlib").md5(b"Correct-Horse-Battery-9").hexdigest(),
        "base64:" + __import__("base64").b64encode(b"Correct-Horse-Battery-9").decode(),
    ])
    def test_weak_formats_never_verify(self, stored):
        assert accounts.verify_password(stored, STRONG) is False

    def test_every_write_path_stores_argon2id(self, fresh_db):
        accounts.create_user("writer.one", STRONG)
        assert accounts.get_user("writer.one")["password_hash"].startswith("argon2:$argon2id$")
        accounts.change_password("writer.one", STRONG, STRONG + "-2")
        assert accounts.get_user("writer.one")["password_hash"].startswith("argon2:$argon2id$")
