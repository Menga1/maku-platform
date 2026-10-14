"""Baseline: the MAKU schema as of 14 October 2026.

Revision ID: 0001_baseline
Revises: -
Create Date: 2026-10-14

A frozen copy of the tables, columns and indexes that analytics.ensure_schema()
created before versioned migrations existed. Idempotent, so it can be applied
to an empty database AND to a database that ensure_schema() already built
(it then only adds missing columns and records the revision).
Later schema changes are new numbered revisions, never edits to this file.
"""
from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None

TABLES = [
    "CREATE TABLE IF NOT EXISTS assessment_log (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    session_id TEXT NOT NULL,\n    timestamp TEXT NOT NULL,\n    module TEXT NOT NULL,\n    risk_band TEXT,\n    safety_override INTEGER,\n    key_metric REAL,\n    primary_hazard TEXT,\n    organization TEXT,\n    project TEXT,\n    site TEXT\n)",
    "CREATE TABLE IF NOT EXISTS site_alert_log (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    timestamp TEXT NOT NULL,\n    worker_or_site_id TEXT,\n    alert_type TEXT NOT NULL,\n    severity TEXT NOT NULL,\n    message TEXT NOT NULL,\n    module TEXT,\n    organization TEXT,\n    project TEXT,\n    site TEXT\n)",
    "CREATE TABLE IF NOT EXISTS audit_log (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    timestamp TEXT NOT NULL,\n    event_type TEXT NOT NULL,\n    actor TEXT NOT NULL,\n    detail TEXT,\n    organization TEXT,\n    project TEXT,\n    site TEXT,\n    prev_hash TEXT NOT NULL,\n    row_hash TEXT NOT NULL\n)",
    "CREATE TABLE IF NOT EXISTS organizations (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    name TEXT NOT NULL UNIQUE\n)",
    "CREATE TABLE IF NOT EXISTS projects (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    organization_id INTEGER NOT NULL,\n    name TEXT NOT NULL,\n    UNIQUE(organization_id, name)\n)",
    "CREATE TABLE IF NOT EXISTS sites (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    project_id INTEGER NOT NULL,\n    name TEXT NOT NULL,\n    UNIQUE(project_id, name)\n)",
    "CREATE TABLE IF NOT EXISTS users (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    username TEXT NOT NULL UNIQUE,\n    password_hash TEXT NOT NULL,\n    role TEXT NOT NULL DEFAULT 'supervisor',\n    email TEXT,\n    created_at TEXT NOT NULL,\n    created_by TEXT,\n    last_login_at TEXT,\n    is_active INTEGER NOT NULL DEFAULT 1\n)",
    "CREATE TABLE IF NOT EXISTS login_attempts (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    username TEXT NOT NULL,\n    client_ip TEXT,\n    attempted_at REAL NOT NULL,\n    succeeded INTEGER NOT NULL DEFAULT 0\n)",
    "CREATE TABLE IF NOT EXISTS user_consents (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    username TEXT NOT NULL,\n    purpose TEXT NOT NULL,\n    granted INTEGER NOT NULL,\n    policy_version TEXT NOT NULL,\n    recorded_at TEXT NOT NULL,\n    UNIQUE(username, purpose)\n)",
    "CREATE TABLE IF NOT EXISTS account_deletions (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    username_sha256 TEXT NOT NULL,\n    deleted_at TEXT NOT NULL,\n    requested_via TEXT NOT NULL,\n    rows_deleted INTEGER NOT NULL\n)",
    "CREATE TABLE IF NOT EXISTS device_tokens (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    username TEXT NOT NULL,\n    token TEXT NOT NULL UNIQUE,\n    platform TEXT NOT NULL,\n    organization TEXT,\n    created_at TEXT NOT NULL,\n    updated_at TEXT NOT NULL\n)"
]

ADDED_COLUMNS = [
    "ALTER TABLE assessment_log ADD COLUMN organization TEXT",
    "ALTER TABLE assessment_log ADD COLUMN project TEXT",
    "ALTER TABLE assessment_log ADD COLUMN site TEXT",
    "ALTER TABLE assessment_log ADD COLUMN organization_id INTEGER",
    "ALTER TABLE assessment_log ADD COLUMN project_id INTEGER",
    "ALTER TABLE assessment_log ADD COLUMN site_id INTEGER",
    "ALTER TABLE site_alert_log ADD COLUMN organization TEXT",
    "ALTER TABLE site_alert_log ADD COLUMN project TEXT",
    "ALTER TABLE site_alert_log ADD COLUMN site TEXT",
    "ALTER TABLE site_alert_log ADD COLUMN organization_id INTEGER",
    "ALTER TABLE site_alert_log ADD COLUMN project_id INTEGER",
    "ALTER TABLE site_alert_log ADD COLUMN site_id INTEGER",
    "ALTER TABLE audit_log ADD COLUMN organization_id INTEGER",
    "ALTER TABLE audit_log ADD COLUMN project_id INTEGER",
    "ALTER TABLE audit_log ADD COLUMN site_id INTEGER",
    "ALTER TABLE assessment_log ADD COLUMN username TEXT",
    "ALTER TABLE assessment_log ADD COLUMN data_provenance TEXT"
]

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_assessment_session ON assessment_log(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_assessment_ts ON assessment_log(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_assessment_org ON assessment_log(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_assessment_user ON assessment_log(username)",
    "CREATE INDEX IF NOT EXISTS idx_alert_ts ON site_alert_log(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_alert_org ON site_alert_log(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_projects_org ON projects(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_sites_project ON sites(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_login_attempts_user_time ON login_attempts(username, attempted_at)",
    "CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_time ON login_attempts(client_ip, attempted_at)",
    "CREATE INDEX IF NOT EXISTS idx_device_tokens_org ON device_tokens(organization)",
    "CREATE INDEX IF NOT EXISTS idx_device_tokens_user ON device_tokens(username)"
]


def _sql(dialect: str, sql: str) -> str:
    if dialect == "postgresql":
        return sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    return sql


def _columns(bind, table: str) -> set[str]:
    if bind.dialect.name == "postgresql":
        rows = bind.exec_driver_sql(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %(t)s AND table_schema = current_schema()", {"t": table})
        return {r[0] for r in rows}
    return {r[1] for r in bind.exec_driver_sql(f"PRAGMA table_info({table})")}


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    for ddl in TABLES:
        bind.exec_driver_sql(_sql(dialect, ddl))
    cache: dict[str, set[str]] = {}
    for stmt in ADDED_COLUMNS:
        parts = stmt.split()
        table, column = parts[2], parts[5]
        cols = cache.setdefault(table, _columns(bind, table))
        if column not in cols:
            bind.exec_driver_sql(stmt)
            cols.add(column)
    for stmt in INDEXES:
        bind.exec_driver_sql(stmt)


def downgrade() -> None:
    raise NotImplementedError("The baseline revision cannot be downgraded; restore from a backup instead.")
