"""
MAKU - Pooled database engine layer (SQLAlchemy 2.x)
====================================================
One SQLAlchemy Engine per database URL per process, created lazily and
reused by every request - instead of opening a brand-new connection (and
re-running the whole schema) on every single log write, which is what the
original analytics.py did.

  * PostgreSQL (production): QueuePool with pre-ping (dead connections are
    replaced transparently after a database failover or idle timeout),
    recycling, and a bounded size so the app can never exhaust the
    database's connection limit.
        MAKU_DB_POOL_SIZE      default 5   persistent connections per process
        MAKU_DB_MAX_OVERFLOW   default 10  burst connections above the pool
        MAKU_DB_POOL_RECYCLE   default 1800 seconds
        MAKU_DB_CONNECT_TIMEOUT default 5 seconds
  * SQLite (local development / tests): NullPool - a SQLite file connection
    is cheap and must not be shared across Streamlit's worker threads.

analytics.py keeps its existing "?"-placeholder SQL and its _Connection
wrapper; it simply obtains the underlying DBAPI connection from here via
raw_connection(). Calling .close() on that connection returns it to the
pool rather than closing the socket.
"""

from __future__ import annotations

import logging
import os
import threading

import sqlalchemy as sa
from sqlalchemy.pool import NullPool, QueuePool

logger = logging.getLogger("maku.db")

_ENGINES: dict[str, sa.Engine] = {}
_ENGINES_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# Deployment environment (P0 "no silent persistence fallback")
#   MAKU_ENV=production | staging   strict: PostgreSQL is mandatory. Without
#                                   a PostgreSQL DATABASE_URL the app refuses
#                                   to start (scripts/init_db.py exits 2) and
#                                   every page shows an explicit error.
#   MAKU_ENV=demo                   local SQLite allowed; UI says data is not kept
#   MAKU_ENV=development (default)  local SQLite allowed (laptops, tests)
# The Docker image sets MAKU_ENV=production, so a server deployment is strict
# unless someone deliberately overrides it. Unknown values are treated as
# production (fail safe).
# ---------------------------------------------------------------------------
STRICT_ENVIRONMENTS = {"production", "staging"}
KNOWN_ENVIRONMENTS = STRICT_ENVIRONMENTS | {"demo", "development", "test"}


class ProductionConfigError(RuntimeError):
    """The deployment is configured in a way production must never run with."""


def maku_env() -> str:
    value = (os.environ.get("MAKU_ENV") or "development").strip().lower()
    if value not in KNOWN_ENVIRONMENTS:
        logger.warning("Unknown MAKU_ENV=%r - treating it as 'production'", value)
        return "production"
    return value


def strict_persistence() -> bool:
    """True when only PostgreSQL may be used and any database problem must
    stop the application instead of degrading."""
    return maku_env() in STRICT_ENVIRONMENTS


def require_production_database(url: str) -> None:
    """Raises ProductionConfigError when a strict environment is not pointed
    at PostgreSQL. Never logs the URL itself (it can contain a password)."""
    if not strict_persistence():
        return
    if not url:
        raise ProductionConfigError(
            f"MAKU_ENV={maku_env()} requires DATABASE_URL to point at PostgreSQL, but DATABASE_URL is not set. "
            "Refusing to fall back to a local SQLite file.")
    if not is_postgres_url(url):
        raise ProductionConfigError(
            f"MAKU_ENV={maku_env()} requires a PostgreSQL DATABASE_URL (postgresql://...), but the configured "
            f"URL uses the '{url.split(':', 1)[0]}' scheme. Refusing to start.")


def redact_url(url: str) -> str:
    """URL safe for logs: password replaced."""
    try:
        return sa.engine.make_url(normalize_url(url)).render_as_string(hide_password=True)
    except Exception:  # noqa: BLE001
        return "<unparseable database URL>"


def is_postgres_url(url: str) -> bool:
    return url.startswith(("postgres://", "postgresql://", "postgresql+psycopg2://"))


def normalize_url(url: str) -> str:
    """Hosted providers (Heroku, Supabase, Render, Neon...) often hand out
    'postgres://' URLs, which SQLAlchemy 2 rejects. Map them to the
    explicit psycopg2 dialect."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


def sqlite_url(path: str) -> str:
    return f"sqlite:///{os.path.abspath(path)}"


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "").strip() or default)
    except ValueError:
        return default


def get_engine(url: str) -> sa.Engine:
    """Process-wide engine cache, keyed by the exact URL."""
    engine = _ENGINES.get(url)
    if engine is not None:
        return engine
    with _ENGINES_LOCK:
        engine = _ENGINES.get(url)
        if engine is not None:
            return engine
        if is_postgres_url(url):
            engine = sa.create_engine(
                normalize_url(url),
                poolclass=QueuePool,
                pool_size=_env_int("MAKU_DB_POOL_SIZE", 5),
                max_overflow=_env_int("MAKU_DB_MAX_OVERFLOW", 10),
                pool_pre_ping=True,
                pool_recycle=_env_int("MAKU_DB_POOL_RECYCLE", 1800),
                pool_timeout=10,
                connect_args={"connect_timeout": _env_int("MAKU_DB_CONNECT_TIMEOUT", 5),
                              "application_name": "maku"},
            )
        else:
            engine = sa.create_engine(
                url,
                poolclass=NullPool,
                connect_args={"timeout": 5, "check_same_thread": False},
            )
        _ENGINES[url] = engine
        logger.info("Created database engine for %s", engine.url.render_as_string(hide_password=True))
        return engine


def raw_connection(url: str):
    """A pooled DBAPI connection (psycopg2 or sqlite3). .close() returns it
    to the pool. Raises on connection failure - analytics.py turns that into
    its fail-fast CRITICAL DATABASE ERROR state for Postgres."""
    return get_engine(url).raw_connection()


def dispose_all() -> None:
    """Closes every pooled connection (used by tests and graceful shutdown)."""
    with _ENGINES_LOCK:
        for engine in _ENGINES.values():
            engine.dispose()
        _ENGINES.clear()
