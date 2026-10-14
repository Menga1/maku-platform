"""
Container health check (Dockerfile HEALTHCHECK). Healthy only when BOTH
  * the Streamlit server answers on /_stcore/health, and
  * the configured database answers SELECT 1 (strict mode, or whenever
    DATABASE_URL is set).
A database outage therefore marks the container unhealthy, so Caddy's
upstream checks and the operator's monitoring see it, instead of the
container reporting healthy while no assessment can be saved.
Exit 0 = healthy, 1 = unhealthy. Prints one line explaining why.
"""

from __future__ import annotations

import os
import sys
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def main() -> int:
    port = os.environ.get("STREAMLIT_SERVER_PORT", "8501")
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=4) as resp:
            if resp.status != 200:
                print(f"unhealthy: web server returned {resp.status}")
                return 1
    except Exception as exc:  # noqa: BLE001
        print(f"unhealthy: web server not answering ({exc.__class__.__name__})")
        return 1

    import db

    url = (os.environ.get("DATABASE_URL") or os.environ.get("MAKU_DATABASE_URL") or "").strip()
    if not (url or db.strict_persistence()):
        print("healthy (local development database not checked)")
        return 0
    try:
        db.require_production_database(url)
        import sqlalchemy as sa
        engine = sa.create_engine(db.normalize_url(url), poolclass=sa.pool.NullPool,
                                  connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        engine.dispose()
    except Exception as exc:  # noqa: BLE001
        print(f"unhealthy: database check failed ({exc.__class__.__name__})")
        return 1
    print("healthy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
