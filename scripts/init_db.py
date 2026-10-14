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
  3. Applies the versioned migrations (Alembic, migrations/versions) up to
     head, then verifies the application sees the expected schema revision.

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


def run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(os.path.join(ROOT, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(ROOT, "migrations"))
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

    if not wait_for_database(url, time.time() + int(os.environ.get("MAKU_DB_WAIT_SECONDS", "60"))):
        return 1

    try:
        run_migrations()
    except Exception as exc:  # noqa: BLE001
        log.critical("Database migration failed: %s: %s", exc.__class__.__name__, exc)
        return 1

    import analytics
    try:
        with analytics._get_connection() as conn:
            revision = analytics.current_schema_revision(conn)
    except Exception as exc:  # noqa: BLE001
        log.critical("Schema check failed after migration: %s: %s", exc.__class__.__name__, exc)
        return 1
    log.info("Database ready - schema revision %s", revision)
    return 0


if __name__ == "__main__":
    sys.exit(main())
