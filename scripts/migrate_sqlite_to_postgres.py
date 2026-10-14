#!/usr/bin/env python3
"""
MAKU - one-time migration: local SQLite file -> PostgreSQL
==========================================================
Copies every MAKU table (organizations, projects, sites, users, consents,
deletion receipts, assessment log, site alert log, hash-chained audit log)
from a SQLite file into PostgreSQL, preserving primary keys so the audit
hash chain and all foreign-key style references stay valid.

Safe by design:
  * creates the PostgreSQL schema with the app's own DDL (analytics.ensure_schema)
  * refuses to write into a non-empty target unless --allow-nonempty
  * idempotent re-runs: rows whose id already exists are skipped (ON CONFLICT DO NOTHING)
  * resets every SERIAL sequence to MAX(id) so new rows don't collide
  * verifies row counts and re-checks the audit-log hash chain on PostgreSQL
  * --dry-run reports what would be copied without writing anything

Usage (from the repository root, with the stack running):

  # copy the old Streamlit Cloud / laptop database into the compose stack
  docker compose cp ./maku_site_data.db app:/app/data/import.db
  docker compose exec app python scripts/migrate_sqlite_to_postgres.py \
      --sqlite /app/data/import.db --dry-run
  docker compose exec app python scripts/migrate_sqlite_to_postgres.py \
      --sqlite /app/data/import.db

  # or against any PostgreSQL server from a laptop
  python scripts/migrate_sqlite_to_postgres.py --sqlite maku_site_data.db \
      --postgres "postgresql://user:pass@host:5432/maku?sslmode=require"
"""

from __future__ import annotations

import argparse
import os
import sys

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import analytics  # noqa: E402  (after sys.path tweak)
import db  # noqa: E402

# Parents before children; audit_log last so verification runs on a complete copy.
TABLE_ORDER = [
    "organizations", "projects", "sites",
    "users", "user_consents", "account_deletions", "login_attempts",
    "assessment_log", "site_alert_log", "audit_log",
]
BATCH_SIZE = 1000


def _postgres_url(cli_value: str | None) -> str:
    url = (cli_value or os.environ.get("DATABASE_URL") or os.environ.get("MAKU_DATABASE_URL") or "").strip()
    if not db.is_postgres_url(url):
        sys.exit("A PostgreSQL URL is required (--postgres or DATABASE_URL).")
    return url


def _ensure_pg_schema(pg_url: str) -> None:
    """Point the app's own DB layer at PostgreSQL and let it create the schema."""
    analytics.DATABASE_URL = pg_url
    analytics.reset_fatal_state_for_testing()
    with analytics._get_connection() as conn:
        conn.execute("SELECT 1")


def migrate(sqlite_path: str, pg_url: str, dry_run: bool, allow_nonempty: bool) -> int:
    if not os.path.exists(sqlite_path):
        sys.exit(f"SQLite file not found: {sqlite_path}")

    src_engine = sa.create_engine(db.sqlite_url(sqlite_path))
    src_meta = sa.MetaData()
    src_meta.reflect(bind=src_engine)
    source_tables = [t for t in TABLE_ORDER if t in src_meta.tables]
    print(f"Source  : {sqlite_path}  ({len(source_tables)} MAKU tables found)")

    if not dry_run:
        _ensure_pg_schema(pg_url)
    dst_engine = db.get_engine(pg_url)
    print(f"Target  : {dst_engine.url.render_as_string(hide_password=True)}")

    dst_meta = sa.MetaData()
    if not dry_run:
        dst_meta.reflect(bind=dst_engine, only=[t for t in source_tables])
        with dst_engine.connect() as dconn:
            non_empty = {t: dconn.execute(sa.text(f"SELECT COUNT(*) FROM {t}")).scalar_one()
                         for t in source_tables}
        populated = {t: n for t, n in non_empty.items() if n}
        if populated and not allow_nonempty:
            print("Target already contains data:", populated)
            print("Re-run with --allow-nonempty to merge (existing ids are skipped).")
            return 2

    summary = []
    with src_engine.connect() as sconn:
        for name in source_tables:
            src_table = src_meta.tables[name]
            total = sconn.execute(sa.select(sa.func.count()).select_from(src_table)).scalar_one()
            if dry_run:
                summary.append((name, total, "-"))
                continue
            dst_table = dst_meta.tables[name]
            shared_cols = [c.name for c in src_table.columns if c.name in dst_table.columns]
            copied = 0
            result = sconn.execution_options(stream_results=True).execute(
                sa.select(*[src_table.c[c] for c in shared_cols]).order_by(src_table.c["id"])
            )
            with dst_engine.begin() as dconn:
                while True:
                    rows = result.fetchmany(BATCH_SIZE)
                    if not rows:
                        break
                    payload = [dict(zip(shared_cols, row)) for row in rows]
                    stmt = pg_insert(dst_table).values(payload).on_conflict_do_nothing(index_elements=["id"])
                    copied += dconn.execute(stmt).rowcount or 0
                dconn.execute(sa.text(
                    f"SELECT setval(pg_get_serial_sequence('{name}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {name}), 1), "
                    f"(SELECT MAX(id) FROM {name}) IS NOT NULL)"
                ))
            summary.append((name, total, copied))

    print(f"\n{'table':<20}{'source rows':>12}{'copied':>10}")
    for name, total, copied in summary:
        print(f"{name:<20}{total:>12}{copied!s:>10}")

    if dry_run:
        print("\nDry run - nothing was written.")
        return 0

    with dst_engine.connect() as dconn:
        mismatches = []
        for name, total, _ in summary:
            dst_total = dconn.execute(sa.text(f"SELECT COUNT(*) FROM {name}")).scalar_one()
            if dst_total < total:
                mismatches.append((name, total, dst_total))
    if mismatches:
        print("\nRow-count check FAILED:", mismatches)
        return 1

    integrity = analytics.verify_audit_log_integrity()
    print(f"\nAudit-log hash chain on PostgreSQL: {'VALID' if integrity.get('ok') else 'BROKEN'} "
          f"({integrity.get('rows_checked')} rows checked)")
    if not integrity.get("ok"):
        print("First broken row id:", integrity.get("first_broken_id"))
        return 1
    print("Migration complete.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sqlite", required=True, help="path to the source SQLite file")
    parser.add_argument("--postgres", default=None, help="target PostgreSQL URL (default: $DATABASE_URL)")
    parser.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    parser.add_argument("--allow-nonempty", action="store_true", help="merge into a target that already has rows")
    args = parser.parse_args(argv)
    return migrate(args.sqlite, _postgres_url(args.postgres), args.dry_run, args.allow_nonempty)


if __name__ == "__main__":
    sys.exit(main())
