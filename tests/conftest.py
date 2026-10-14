"""Shared setup for the tests/ suites: make the application modules importable
from the repository root, and give every test a clean database state."""
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """A private SQLite file, development mode, no fatal state left over."""
    import analytics
    import streamlit as st

    monkeypatch.delenv("MAKU_ENV", raising=False)
    monkeypatch.setattr("analytics.DATABASE_URL", "")
    monkeypatch.setattr("analytics.DB_PATH", str(tmp_path / "test.db"))
    analytics.reset_fatal_state_for_testing()
    st.session_state.clear()
    yield tmp_path
    analytics.reset_fatal_state_for_testing()
    st.session_state.clear()
