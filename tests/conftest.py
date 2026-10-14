"""Shared setup for the tests/ suites: make the application modules importable
from the repository root, and give every test a clean database state."""
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# MAKU_TEST_BACKEND=postgres runs every test that uses `fresh_db` against the
# (already migrated) PostgreSQL at MAKU_TEST_PG_URL, emptied before each test.
PG_URL = os.environ.get("MAKU_TEST_PG_URL", "")
USE_PG = os.environ.get("MAKU_TEST_BACKEND") == "postgres" and bool(PG_URL)
_TABLES = ("assessment_log", "site_alert_log", "audit_log", "organizations", "projects", "sites",
           "users", "login_attempts", "user_consents", "account_deletions", "device_tokens",
           "organization_members")


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """A clean database, development mode, no fatal state left over: a private
    SQLite file by default, or the test PostgreSQL (see USE_PG)."""
    import analytics
    import streamlit as st

    monkeypatch.delenv("MAKU_ENV", raising=False)
    monkeypatch.setattr("analytics.DB_PATH", str(tmp_path / "test.db"))
    if USE_PG:
        monkeypatch.setattr("analytics.DATABASE_URL", PG_URL)
        analytics.reset_fatal_state_for_testing()
        with analytics._get_connection() as conn:
            conn.execute(f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY")
    else:
        monkeypatch.setattr("analytics.DATABASE_URL", "")
    analytics.reset_fatal_state_for_testing()
    st.session_state.clear()
    yield tmp_path
    analytics.reset_fatal_state_for_testing()
    st.session_state.clear()
