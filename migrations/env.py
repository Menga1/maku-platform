"""Alembic environment for MAKU (plain SQL migrations, no ORM metadata)."""
from __future__ import annotations

import logging.config
import os
import sys

from alembic import context
from sqlalchemy import create_engine, pool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import db  # noqa: E402

config = context.config
if config.config_file_name and not logging.getLogger().handlers:
    logging.config.fileConfig(config.config_file_name, disable_existing_loggers=False)


def database_url() -> str:
    url = (context.get_x_argument(as_dictionary=True).get("url")
           or os.environ.get("DATABASE_URL") or os.environ.get("MAKU_DATABASE_URL") or "").strip()
    db.require_production_database(url)  # strict mode never migrates a SQLite file
    if not url:
        url = db.sqlite_url(os.environ.get("MAKU_DB_PATH", "maku_site_data.db"))
    return db.normalize_url(url)


def run_migrations_offline() -> None:
    context.configure(url=database_url(), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, transaction_per_migration=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
