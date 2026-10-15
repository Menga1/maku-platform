"""
Start-up database initialisation (run by docker-entrypoint.sh, or by hand:
    docker compose exec app python scripts/init_db.py ).

  1. Configuration check. In strict mode (MAKU_ENV=production/staging, the
     Docker default) DATABASE_URL must point at PostgreSQL. Otherwise this
     exits with code 2 immediately and a CRITICAL log line - the container
     never starts on a local SQLite file.
  2. Waits up to MAKU_DB_WAIT_SECONDS (default 60) for the database to answer.
     Exits 1 if it never does, so the orchestrator restarts the container
     instead of serving a broken app.
  3. PostgreSQL: makes sure the APPLICATION role exists and is separate from
     the table owner (row-level security, migration 0003, is skipped for the
     owner). Migrations run as MIGRATION_DATABASE_URL (the owner); the app
     connects as DATABASE_URL (the application role). If the owner may create
     roles, the application role is created / its password synchronised from
     DATABASE_URL.
  4. Applies the versioned migrations (Alembic, migrations/versions) up to
     head, (re)grants the application role, then verifies - connected as the
     application - the schema revision and that RLS is enforced for it.

Exit codes: 0 ready · 1 database unreachable or migration failed · 2 invalid configuration.
"""

from __future__ import annotations

import logging
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("maku.init_db")


def database_url() -> str:
    return (os.environ.get("DATABASE_URL") or os.environ.get("MAKU_DATABASE_URL") or "").strip()


def migration_url(app_url: str) -> str:
    return (os.environ.get("MIGRATION_DATABASE_URL") or "").strip() or app_url


def _user_of(url: str) -> str:
    import sqlalchemy as sa
    import db
    return sa.engine.make_url(db.normalize_url(url)).username or ""


def prepare_application_role(owner_url: str, app_url: str) -> str:
    """Creates the application role if missing (when the owner may), keeps its
    password in sync with DATABASE_URL and returns its name. Raises
    ProductionConfigError for an unusable configuration."""
    import re
    import sqlalchemy as sa
    import db

    app_role, owner_role = _user_of(app_url), _user_of(owner_url)
    if not re.match(r"^[a-z_][a-z0-9_]{0,62}$", app_role or ""):
        raise db.ProductionConfigError("The DATABASE_URL user must be a plain lower-case role name.")
    if app_role == owner_role:
        raise db.ProductionConfigError(
            "DATABASE_URL connects as the table owner, so PostgreSQL would skip row-level security. "
            "Set MIGRATION_DATABASE_URL to the owner and DATABASE_URL to a separate application role "
            "(docs/DEPLOYMENT.md).")
    password = sa.engine.make_url(db.normalize_url(app_url)).password
    engine = sa.create_engine(db.normalize_url(owner_url), poolclass=sa.pool.NullPool)
    try:
        with engine.begin() as conn:
            can_create = conn.exec_driver_sql(
                "SELECT rolsuper OR rolcreaterole FROM pg_roles WHERE rolname = current_user").scalar()
            exists = conn.exec_driver_sql("SELECT 1 FROM pg_roles WHERE rolname = %s", (app_role,)).scalar()
            if can_create:
                verb = "ALTER" if exists else "CREATE"
                # New roles default to NOSUPERUSER NOBYPASSRLS; the application
                # re-checks both at start-up (analytics.verify_rls_enforced).
                conn.exec_driver_sql(f"{verb} ROLE {app_role} LOGIN PASSWORD %s", (password or "",))
                log.info("Application role %s %s", app_role, "updated" if exists else "created")
            elif not exists:
                raise db.ProductionConfigError(
                    f"Application role {app_role} does not exist and the migration role cannot create it.")
            database = conn.exec_driver_sql("SELECT current_database()").scalar()
            conn.exec_driver_sql(f'GRANT CONNECT ON DATABASE "{database}" TO {app_role}')
    finally:
        engine.dispose()
    return app_role


def grant_application_role(owner_url: str, role: str) -> None:
    import importlib.util
    import sqlalchemy as sa
    import db

    spec = importlib.util.spec_from_file_location(
        "rls_migration", os.path.join(ROOT, "migrations", "versions", "0003_row_level_security.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = sa.create_engine(db.normalize_url(owner_url), poolclass=sa.pool.NullPool)
    try:
        with engine.begin() as conn:
            schema = conn.exec_driver_sql("SELECT current_schema()").scalar()
            for statement in module.grant_statements(role, schema):
                conn.exec_driver_sql(statement)
    finally:
        engine.dispose()


def wait_for_database(url: str, deadline: float) -> bool:
    import sqlalchemy as sa
    import db

    target = db.normalize_url(url) if url else db.sqlite_url(os.environ.get("MAKU_DB_PATH", "maku_site_data.db"))
    attempt = 0
    while True:
        attempt += 1
        try:
            engine = sa.create_engine(target, poolclass=sa.pool.NullPool,
                                      connect_args={"connect_timeout": 5} if url else {})
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            engine.dispose()
            log.info("Database reachable after %d attempt(s)", attempt)
            return True
        except Exception as exc:  # noqa: BLE001
            if time.time() > deadline:
                log.critical("Database not reachable after %d attempts (%s): %s",
                             attempt, db.redact_url(target), exc.__class__.__name__)
                return False
            log.info("Waiting for database (%s)...", exc.__class__.__name__)
            time.sleep(2)


def run_migrations(url: str = "") -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(os.path.join(ROOT, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(ROOT, "migrations"))
    if url:
        cfg.cmd_opts = type("Opts", (), {"x": [f"url={url}"]})()
    command.upgrade(cfg, "head")


def main() -> int:
    import db

    url = database_url()
    log.info("MAKU_ENV=%s (strict persistence: %s)", db.maku_env(), db.strict_persistence())
    try:
        db.require_production_database(url)
    except db.ProductionConfigError as exc:
        log.critical("%s", exc)
        return 2

    owner_url = migration_url(url)
    # Wait as the owner: the application role may not exist yet.
    if not wait_for_database(owner_url, time.time() + int(os.environ.get("MAKU_DB_WAIT_SECONDS", "60"))):
        return 1

    postgres = bool(url) and db.is_postgres_url(url)
    app_role = None
    if postgres and (db.strict_persistence() or owner_url != url):
        try:
            app_role = prepare_application_role(owner_url, url)
        except db.ProductionConfigError as exc:
            log.critical("%s", exc)
            return 2
        except Exception as exc:  # noqa: BLE001
            log.critical("Could not prepare the application role: %s", exc.__class__.__name__)
            return 1
        os.environ["MAKU_APP_DB_ROLE"] = app_role

    try:
        run_migrations(owner_url if postgres else "")
        if app_role:
            grant_application_role(owner_url, app_role)
    except Exception as exc:  # noqa: BLE001
        detail = "" if "://" in str(exc) else str(exc)   # never log a URL (it may hold a password)
        log.critical("Database migration failed: %s: %s", exc.__class__.__name__, detail)
        return 1

    import analytics
    try:
        with analytics.system_context(), analytics._get_connection() as conn:
            revision = analytics.current_schema_revision(conn)
    except Exception as exc:  # noqa: BLE001
        log.critical("Schema check failed after migration: %s: %s", exc.__class__.__name__, exc)
        return 1
    log.info("Database ready - schema revision %s", revision)
    return 0


if __name__ == "__main__":
    sys.exit(main())
