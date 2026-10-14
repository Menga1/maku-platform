"""
Startup database initialisation (run by docker-entrypoint.sh, or by hand:
    docker compose exec app python scripts/init_db.py ).

Uses the app's pooled SQLAlchemy engine (db.py: QueuePool, pre-ping,
recycle) and the app's own idempotent DDL (analytics.ensure_schema), so the
schema created here is exactly the one the application expects.

  * waits up to MAKU_DB_WAIT_SECONDS (default 60) for the database,
  * creates every table/index and applies additive migrations
    (analytics.ensure_schema - idempotent),
  * exits non-zero if the database never becomes reachable, so the
    orchestrator restarts the container instead of serving a broken app.
"""

from __future__ import annotations

import logging
import os
import sys
import time

# Run from anywhere: make the application modules (analytics.py, db.py) importable.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("maku.init_db")


def main() -> int:
    import analytics
    import db

    deadline = time.time() + int(os.environ.get("MAKU_DB_WAIT_SECONDS", "60"))
    backend = "PostgreSQL" if analytics.DATABASE_URL and db.is_postgres_url(analytics.DATABASE_URL) else "SQLite"
    attempt = 0
    while True:
        attempt += 1
        try:
            with analytics._get_connection() as conn:
                conn.execute("SELECT 1")
            log.info("Database ready (%s) - schema verified after %d attempt(s)", backend, attempt)
            return 0
        except Exception as exc:  # noqa: BLE001
            analytics.reset_fatal_state_for_testing()  # allow retry during startup only
            if time.time() > deadline:
                log.error("Database not reachable after %d attempts: %s", attempt, exc)
                return 1
            log.info("Waiting for database (%s)...", exc.__class__.__name__)
            time.sleep(2)


if __name__ == "__main__":
    sys.exit(main())
