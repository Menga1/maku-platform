"""P0 data integrity (review finding F1): production never substitutes a
different database, fails loudly, and migrates through versioned revisions."""
import logging
import os
import subprocess
import sys

import pytest
import streamlit as st

import analytics
import db
from risk_engine import calculate_solar_albedo_heat_risk

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PG_URL = os.environ.get("MAKU_TEST_PG_URL", "")  # application role, e.g. postgresql://maku_app:pw@127.0.0.1/maku_test
PG_OWNER_URL = os.environ.get("MAKU_TEST_PG_OWNER_URL", "")   # table owner (migrations)
USE_PG = os.environ.get("MAKU_TEST_BACKEND") == "postgres" and bool(PG_URL)
sqlite_only = pytest.mark.skipif(USE_PG, reason="exercises the no-DATABASE_URL path; not applicable to the PostgreSQL run")


def _run_init_db(env_overrides: dict) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("DATABASE_URL", "MAKU_DATABASE_URL", "MAKU_ENV")}
    env.update(env_overrides)
    return subprocess.run([sys.executable, "scripts/init_db.py"], cwd=ROOT, capture_output=True,
                          text=True, env=env, timeout=120)


# --------------------------------------------------------------- environment
class TestEnvironment:
    def test_default_is_development(self, monkeypatch):
        monkeypatch.delenv("MAKU_ENV", raising=False)
        assert db.maku_env() == "development" and not db.strict_persistence()

    @pytest.mark.parametrize("value", ["production", "staging", "PRODUCTION "])
    def test_strict_environments(self, monkeypatch, value):
        monkeypatch.setenv("MAKU_ENV", value)
        assert db.strict_persistence()

    def test_unknown_value_is_treated_as_production(self, monkeypatch):
        monkeypatch.setenv("MAKU_ENV", "prod")  # typo must not relax the rules
        assert db.maku_env() == "production" and db.strict_persistence()

    @pytest.mark.parametrize("url", ["", "sqlite:///x.db", "mysql://u:p@h/db"])
    def test_production_rejects_anything_but_postgres(self, monkeypatch, url):
        monkeypatch.setenv("MAKU_ENV", "production")
        with pytest.raises(db.ProductionConfigError):
            db.require_production_database(url)

    def test_production_accepts_postgres(self, monkeypatch):
        monkeypatch.setenv("MAKU_ENV", "production")
        db.require_production_database("postgresql://u:p@h:5432/maku")

    def test_error_message_never_contains_the_password(self, monkeypatch):
        monkeypatch.setenv("MAKU_ENV", "production")
        with pytest.raises(db.ProductionConfigError) as err:
            db.require_production_database("mysql://user:s3cret@host/db")
        assert "s3cret" not in str(err.value)
        assert "s3cret" not in db.redact_url("postgresql://user:s3cret@host/db")


# ------------------------------------------------------------ runtime guard
class TestStrictRuntime:
    @sqlite_only
    def test_production_without_database_url_is_fatal_and_writes_nothing(self, fresh_db, monkeypatch, caplog):
        _sign_in_admin()
        monkeypatch.setenv("MAKU_ENV", "production")
        with caplog.at_level(logging.CRITICAL, logger="maku.analytics"):
            with pytest.raises(analytics.PersistenceError):   # never reported as saved
                analytics.log_assessment(st, calculate_solar_albedo_heat_risk(950, 9, 42, "silicon_pv_panels"))
        assert analytics.is_db_fatal()
        assert analytics.LOG_SESSION_KEY not in st.session_state          # no in-memory substitute
        assert not (fresh_db / "test.db").exists()                          # no SQLite file created
        assert any("requires DATABASE_URL" in r.getMessage() for r in caplog.records)

    @sqlite_only
    def test_critical_log_is_written_once_per_reason(self, fresh_db, monkeypatch, caplog):
        monkeypatch.setenv("MAKU_ENV", "production")
        with caplog.at_level(logging.CRITICAL, logger="maku.analytics"):
            for _ in range(3):
                analytics.probe_database(force=True)
        assert len([r for r in caplog.records if r.levelno == logging.CRITICAL]) == 1

    def test_probe_recovers_when_the_same_database_answers_again(self, fresh_db, monkeypatch):
        calls = {"fail": True}

        def flaky():
            if calls["fail"]:
                raise ConnectionError("database restarting")
            return _sqlite_conn(fresh_db)   # stands in for the same server answering again

        monkeypatch.setenv("MAKU_ENV", "staging")
        monkeypatch.setattr("analytics.DATABASE_URL", "postgresql://u:p@db:5432/maku")
        monkeypatch.setattr("analytics._get_connection", flaky)
        assert analytics.probe_database(force=True)["fatal"] is True
        calls["fail"] = False
        assert analytics.probe_database(force=True)["fatal"] is False

    def test_probe_is_throttled(self, fresh_db, monkeypatch):
        counter = {"n": 0}

        def counting():
            counter["n"] += 1
            return _sqlite_conn(fresh_db)

        monkeypatch.setattr("analytics._get_connection", counting)
        analytics.probe_database(force=True)
        for _ in range(10):
            analytics.probe_database()
        assert counter["n"] == 1

    def test_strict_mode_refuses_an_unmigrated_database(self, fresh_db, monkeypatch):
        conn = _sqlite_conn(fresh_db)
        with conn:
            analytics.ensure_schema(conn)          # tables exist, but no alembic_version
        with pytest.raises(analytics.SchemaNotMigratedError):
            analytics.verify_schema_revision(_sqlite_conn(fresh_db))

    def test_development_mode_keeps_working_on_sqlite(self, fresh_db):
        _sign_in_admin()
        analytics.log_assessment(st, calculate_solar_albedo_heat_risk(950, 9, 42, "silicon_pv_panels"))
        assert not analytics.is_db_fatal()
        assert not analytics.get_log_dataframe(st).empty


def _sign_in_admin():
    st.session_state.update({"authenticated": True, "_auth_username": "ops.admin", "_auth_role": "admin"})


def _sqlite_conn(tmp_path):
    raw = db.raw_connection(db.sqlite_url(str(tmp_path / "test.db")))
    return analytics._Connection(raw, "sqlite")


# ------------------------------------------------------------ page gate
class TestPageGate:
    @sqlite_only
    def test_every_page_stops_with_an_explicit_error(self, fresh_db, monkeypatch):
        from streamlit.testing.v1 import AppTest
        monkeypatch.setenv("MAKU_ENV", "production")
        at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=60).run()
        texts = " ".join(e.value for e in at.error)
        assert "CRITICAL DATABASE ERROR" in texts
        assert not at.text_input   # login form never rendered
        assert not at.exception

    def test_demo_mode_shows_data_not_kept(self, fresh_db, monkeypatch):
        from streamlit.testing.v1 import AppTest
        monkeypatch.setenv("MAKU_ENV", "demo")
        at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=60).run()
        assert any("not kept" in w.value or "pas conservées" in w.value for w in at.sidebar.warning)


# ------------------------------------------------------------ start-up + migrations
class TestInitDb:
    def test_production_without_database_url_refuses_to_start(self):
        out = _run_init_db({"MAKU_ENV": "production"})
        assert out.returncode == 2
        assert "CRITICAL" in out.stderr and "Refusing to fall back" in out.stderr

    def test_production_with_sqlite_url_refuses_to_start(self, tmp_path):
        out = _run_init_db({"MAKU_ENV": "production", "DATABASE_URL": f"sqlite:///{tmp_path}/x.db"})
        assert out.returncode == 2

    def test_unreachable_postgres_exits_1_without_leaking_password(self):
        out = _run_init_db({"MAKU_ENV": "production", "MAKU_DB_WAIT_SECONDS": "1",
                            "DATABASE_URL": "postgresql://maku:Sup3rSecret@127.0.0.1:1/maku"})
        assert out.returncode == 1
        assert "Sup3rSecret" not in out.stderr + out.stdout

    def test_development_creates_and_migrates_sqlite(self, tmp_path):
        out = _run_init_db({"MAKU_DB_PATH": str(tmp_path / "dev.db")})
        assert out.returncode == 0, out.stderr
        assert f"schema revision {analytics.SCHEMA_REVISION}" in out.stderr

    def test_baseline_upgrades_a_database_built_before_migrations(self, tmp_path, monkeypatch):
        """Existing deployments (tables created by ensure_schema) migrate in place."""
        path = tmp_path / "legacy.db"
        monkeypatch.setattr("analytics.DB_PATH", str(path))
        analytics.reset_fatal_state_for_testing()
        conn = analytics._Connection(db.raw_connection(db.sqlite_url(str(path))), "sqlite")
        with conn:
            analytics.ensure_schema(conn)
            conn.execute("INSERT INTO organizations (name) VALUES ('Legacy Co')")
        out = _run_init_db({"MAKU_DB_PATH": str(path)})
        assert out.returncode == 0, out.stderr
        conn = analytics._Connection(db.raw_connection(db.sqlite_url(str(path))), "sqlite")
        with conn:
            assert analytics.current_schema_revision(conn) == analytics.SCHEMA_REVISION
            assert conn.execute("SELECT name FROM organizations").fetchone()[0] == "Legacy Co"

    def test_code_expects_the_latest_migration(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        cfg = Config(os.path.join(ROOT, "alembic.ini"))
        cfg.set_main_option("script_location", os.path.join(ROOT, "migrations"))
        assert ScriptDirectory.from_config(cfg).get_current_head() == analytics.SCHEMA_REVISION


@pytest.mark.skipif(not (PG_URL and PG_OWNER_URL),
                    reason="set MAKU_TEST_PG_URL (application role) and MAKU_TEST_PG_OWNER_URL (owner)")
class TestPostgresProduction:
    def test_production_refuses_to_connect_as_the_table_owner(self):
        """RLS does not apply to the owner: production must not start that way."""
        out = _run_init_db({"MAKU_ENV": "production", "DATABASE_URL": PG_OWNER_URL})
        assert out.returncode == 2
        assert "row-level security" in out.stderr

    def test_runtime_refuses_the_owner_role_too(self, monkeypatch):
        monkeypatch.setenv("MAKU_ENV", "production")
        conn = analytics._Connection(db.raw_connection(PG_OWNER_URL), "postgres")
        with pytest.raises(analytics.RowLevelSecurityBypassed):
            analytics.verify_rls_enforced(conn)
        conn._conn.close()

    def test_production_start_migrate_and_write(self, monkeypatch):
        env = {"MAKU_ENV": "production", "DATABASE_URL": PG_URL, "MIGRATION_DATABASE_URL": PG_OWNER_URL}
        out = _run_init_db(env)
        assert out.returncode == 0, out.stderr
        out = _run_init_db(env)   # idempotent
        assert out.returncode == 0, out.stderr

        monkeypatch.setenv("MAKU_ENV", "production")
        monkeypatch.setattr("analytics.DATABASE_URL", PG_URL)
        analytics.reset_fatal_state_for_testing()
        st.session_state.clear()
        _sign_in_admin()
        analytics.log_assessment(st, calculate_solar_albedo_heat_risk(950, 9, 42, "silicon_pv_panels"))
        assert not analytics.is_db_fatal()
        assert not analytics.get_log_dataframe(st).empty
        analytics.reset_fatal_state_for_testing()
