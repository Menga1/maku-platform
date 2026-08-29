"""
MAKU - Assessment Log, Trend Analytics, Site Alert Log & Monthly Excel Export
==============================================================================
Logs every risk assessment run, plus every site safety alert (physiological
CRITICAL/WARNING strain events, safety-override triggers, regulatory fallback
notices), into a local SQLite database - and builds a real downloadable
.xlsx (openpyxl) with a raw-data sheet, a monthly summary sheet, and an
embedded trend chart.

PERSISTENCE - WHAT SQLITE ACTUALLY BUYS HERE, HONESTLY:
Streamlit Cloud gives each running app instance ephemeral local disk: a
redeploy, reboot, or the app sleeping from inactivity wipes it, exactly
like before. SQLite does NOT change that. What it DOES change: previously
every browser tab held its own private in-memory Python list
(st.session_state) that vanished the instant that tab closed - a second
foreman opening the dashboard from their own phone saw nothing the first
foreman had logged, even seconds earlier on the same running app. With a
real SQLite file on the same running instance's disk, every session
writes to (and can be read from) one shared store for as long as that
instance stays up - multiple simultaneous users now see a common history,
survive their own tab refresh, and a page reload no longer loses data.
That is a genuine reliability upgrade, just not a claim of surviving a
redeploy - true cross-deploy persistence still needs an external datastore
(hosted Postgres/S3-backed SQLite/etc.), and swapping that in only touches
this file, not risk_engine.py or the pages.

If the SQLite file can't be opened or written for any reason (read-only
filesystem, disk full, locked), every write/read here degrades gracefully
to the previous pure-session_state behavior rather than crashing the page
- see _sqlite_ok().

SESSION-SCOPED VIEW vs ALL-TIME HISTORY:
get_log_dataframe()/monthly_summary()/build_monthly_excel() keep their
original session-scoped contract (each browser session sees only its own
logged rows, and st.session_state.clear() resets that view to empty) -
this preserves the exact UX and test contract the rest of the app already
relies on. Session scoping is implemented with a per-session UUID tag
column, not a separate in-memory store, so the underlying rows are never
actually lost - get_all_time_log_dataframe() (new) reads the full durable
history across every session that has ever written to this running
instance, bounded by `limit` so the trend module never has to load an
unbounded table into RAM. log_site_alert()/get_site_alert_log_dataframe()
(new) are the durable "site alert log / historical risk incidents" store
requested for the physiological-strain and environmental-alert features.

Mathematical Isolation rule still applies: this file aggregates/logs
results computed elsewhere. It never computes risk itself.
"""

from __future__ import annotations

import io
import os
import sqlite3
import uuid
from datetime import datetime, timezone

import pandas as pd
from openpyxl import load_workbook
from openpyxl.chart import LineChart, Reference

LOG_SESSION_KEY = "assessment_log"          # legacy in-memory fallback store
SESSION_ID_KEY = "_analytics_session_id"

DB_PATH = os.environ.get("MAKU_DB_PATH", "maku_site_data.db")
ALL_TIME_DEFAULT_LIMIT = 5000     # RAM guard for the durable multi-session view
ALERT_LOG_DEFAULT_LIMIT = 1000

# Best-effort single "headline" numeric metric per module, for trend charts -
# each module's result dict has different fields, so this picks the one most
# representative of that module's core risk driver.
MODULE_KEY_METRIC = {
    "Solar (Desert)": "perceived_temp",
    "Offshore (Marine)": "humidex",
    "Underground (Tunnel/Metro)": "perceived_temp",
    "High-Rise (Vertical Urban)": "scaled_wind_speed",
    "Data Center (Controlled Critical Environment)": "arc_flash_energy_cal",
    "Wind Energy (Onshore/Offshore)": "hub_height_wind_speed_ms",
    "Mining & Quarrying": "noise_dose_pct",
    "Marine & Port Construction": "tide_clearance_margin_m",
}

LOG_COLUMNS = ["timestamp", "module", "risk_band", "safety_override", "key_metric", "primary_hazard"]
ALERT_LOG_COLUMNS = ["timestamp", "worker_or_site_id", "alert_type", "severity", "message", "module"]


# ---------------------------------------------------------------------------
# SQLite plumbing - a fresh short-lived connection per call (simplest way to
# be safe across Streamlit's worker threads without a shared connection
# object), and every public function tries SQLite first, falling back to the
# legacy session_state list on ANY failure. _SQLITE_DISABLED is process-wide
# (not per-session) once a failure is seen, so a broken filesystem doesn't
# retry-and-fail on every single call for the rest of the process.
# ---------------------------------------------------------------------------
_SQLITE_DISABLED = False


def _sqlite_ok() -> bool:
    return not _SQLITE_DISABLED


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS assessment_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            module TEXT NOT NULL,
            risk_band TEXT,
            safety_override INTEGER,
            key_metric REAL,
            primary_hazard TEXT
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS site_alert_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            worker_or_site_id TEXT,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            module TEXT
        )"""
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_assessment_session ON assessment_log(session_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_assessment_ts ON assessment_log(timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_alert_ts ON site_alert_log(timestamp)")
    return conn


def _disable_sqlite() -> None:
    global _SQLITE_DISABLED
    _SQLITE_DISABLED = True


def _get_session_id(st_module) -> str:
    """One random id per browser session, stored in session_state. Clearing
    session_state (as the test suite does between test methods, and as a
    real logout would) forgets this id, which is exactly what makes
    get_log_dataframe() go back to reporting an empty session-scoped log -
    the underlying SQLite rows from the old id are never deleted, just no
    longer tagged as 'this session's view'."""
    if SESSION_ID_KEY not in st_module.session_state:
        st_module.session_state[SESSION_ID_KEY] = uuid.uuid4().hex
    return st_module.session_state[SESSION_ID_KEY]


# ---------------------------------------------------------------------------
# Assessment log (session-scoped view, SQLite-backed with durable history)
# ---------------------------------------------------------------------------

def log_assessment(st_module, result: dict) -> None:
    """Append one row to this session's assessment log. Call right after
    computing a result on any module page."""
    module = result.get("module", "")
    key_metric_field = MODULE_KEY_METRIC.get(module)
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "module": module,
        "risk_band": str(result.get("risk_band", "")),
        "safety_override": bool(result.get("safety_override", False)),
        "key_metric": result.get(key_metric_field) if key_metric_field else None,
        "primary_hazard": result.get("primary_hazard", ""),
    }

    if _sqlite_ok():
        session_id = _get_session_id(st_module)
        try:
            with _get_connection() as conn:
                conn.execute(
                    """INSERT INTO assessment_log
                       (session_id, timestamp, module, risk_band, safety_override, key_metric, primary_hazard)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (session_id, row["timestamp"], row["module"], row["risk_band"],
                     int(row["safety_override"]), row["key_metric"], row["primary_hazard"]),
                )
            return
        except sqlite3.Error:
            _disable_sqlite()  # fall through to the legacy in-memory path below

    if LOG_SESSION_KEY not in st_module.session_state:
        st_module.session_state[LOG_SESSION_KEY] = []
    st_module.session_state[LOG_SESSION_KEY].append(row)


def get_log_dataframe(st_module) -> pd.DataFrame:
    """This session's log as a DataFrame, oldest first, timestamp parsed.
    Same contract as before the SQLite upgrade: empty right after
    st.session_state.clear()."""
    if _sqlite_ok():
        session_id = st_module.session_state.get(SESSION_ID_KEY)
        if session_id is None:
            return pd.DataFrame(columns=LOG_COLUMNS)
        try:
            with _get_connection() as conn:
                df = pd.read_sql_query(
                    f"SELECT {', '.join(LOG_COLUMNS)} FROM assessment_log "
                    "WHERE session_id = ? ORDER BY timestamp",
                    conn, params=(session_id,),
                )
            if df.empty:
                return pd.DataFrame(columns=LOG_COLUMNS)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["safety_override"] = df["safety_override"].astype(bool)
            return df.reset_index(drop=True)
        except sqlite3.Error:
            _disable_sqlite()  # fall through

    rows = st_module.session_state.get(LOG_SESSION_KEY, [])
    if not rows:
        return pd.DataFrame(columns=LOG_COLUMNS)
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)


def get_all_time_log_dataframe(limit: int = ALL_TIME_DEFAULT_LIMIT) -> pd.DataFrame:
    """The durable, cross-session history for this running instance (see
    module docstring) - every assessment ever logged while this app
    instance has been up, from every browser session, newest first,
    bounded by `limit` so this never pulls an unbounded table into RAM.
    Returns an empty DataFrame (never raises) if SQLite is unavailable."""
    if not _sqlite_ok():
        return pd.DataFrame(columns=LOG_COLUMNS)
    try:
        with _get_connection() as conn:
            df = pd.read_sql_query(
                f"SELECT {', '.join(LOG_COLUMNS)} FROM assessment_log "
                "ORDER BY timestamp DESC LIMIT ?",
                conn, params=(int(limit),),
            )
        if df.empty:
            return pd.DataFrame(columns=LOG_COLUMNS)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["safety_override"] = df["safety_override"].astype(bool)
        return df.reset_index(drop=True)
    except sqlite3.Error:
        _disable_sqlite()
        return pd.DataFrame(columns=LOG_COLUMNS)


def merge_uploaded_csv(st_module, uploaded_file) -> int:
    """Parses a previously-downloaded CSV log and merges it into this
    session's log, de-duplicating exact repeats. Returns how many new
    rows were actually added (0 if everything was already present).
    Behavior/semantics are unchanged from the pre-SQLite implementation;
    only the storage backing this session's view changed."""
    uploaded_df = pd.read_csv(uploaded_file)
    missing = set(LOG_COLUMNS) - set(uploaded_df.columns)
    if missing:
        raise ValueError(f"Uploaded file is missing expected columns: {sorted(missing)}")

    existing_df = get_log_dataframe(st_module)
    combined = pd.concat([existing_df, uploaded_df], ignore_index=True)
    combined["timestamp"] = pd.to_datetime(combined["timestamp"])
    before = len(existing_df)
    combined = combined.drop_duplicates(subset=["timestamp", "module", "risk_band", "key_metric"])
    combined = combined.sort_values("timestamp").reset_index(drop=True)
    added = len(combined) - before

    records = combined.to_dict("records")
    for row in records:
        ts = row["timestamp"]
        row["timestamp"] = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
        row["safety_override"] = bool(row["safety_override"])

    if _sqlite_ok():
        session_id = _get_session_id(st_module)
        try:
            with _get_connection() as conn:
                conn.execute("DELETE FROM assessment_log WHERE session_id = ?", (session_id,))
                conn.executemany(
                    """INSERT INTO assessment_log
                       (session_id, timestamp, module, risk_band, safety_override, key_metric, primary_hazard)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    [(session_id, r["timestamp"], r["module"], r["risk_band"],
                      int(r["safety_override"]), r["key_metric"], r["primary_hazard"]) for r in records],
                )
            return added
        except sqlite3.Error:
            _disable_sqlite()  # fall through

    st_module.session_state[LOG_SESSION_KEY] = records
    return added


# ---------------------------------------------------------------------------
# Site alert log - physiological CRITICAL/WARNING strain events, safety-
# override triggers, regulatory-fallback notices, etc. Always durable
# (all-time, not session-scoped) since these are safety incidents a site
# manager needs to review regardless of who was looking at the dashboard
# when they fired. Never includes worker names - callers must pass an
# already-anonymized id (e.g. "Worker_A3"), never raw PII (see app.py's
# worker-strain dashboard for the anonymization step).
# ---------------------------------------------------------------------------

def log_site_alert(worker_or_site_id: str, alert_type: str, severity: str, message: str, module: str = "") -> None:
    """Records one durable site alert row. Silently no-ops if SQLite is
    unavailable (an alert that can't be written to disk still displayed on
    screen at the moment it fired - this is a log for later review, not
    the sole notification channel)."""
    if not _sqlite_ok():
        return
    try:
        with _get_connection() as conn:
            conn.execute(
                """INSERT INTO site_alert_log
                   (timestamp, worker_or_site_id, alert_type, severity, message, module)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 worker_or_site_id, alert_type, severity, message, module),
            )
    except sqlite3.Error:
        _disable_sqlite()


def get_site_alert_log_dataframe(limit: int = ALERT_LOG_DEFAULT_LIMIT) -> pd.DataFrame:
    """Durable site alert history, newest first, bounded by `limit`."""
    if not _sqlite_ok():
        return pd.DataFrame(columns=ALERT_LOG_COLUMNS)
    try:
        with _get_connection() as conn:
            df = pd.read_sql_query(
                f"SELECT {', '.join(ALERT_LOG_COLUMNS)} FROM site_alert_log "
                "ORDER BY timestamp DESC LIMIT ?",
                conn, params=(int(limit),),
            )
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except sqlite3.Error:
        _disable_sqlite()
        return pd.DataFrame(columns=ALERT_LOG_COLUMNS)


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates the log by (year-month, module): assessment count, safety
    override count, and average key metric."""
    if df.empty:
        return pd.DataFrame(columns=["month", "module", "assessments", "safety_overrides", "avg_key_metric"])
    work = df.copy()
    work["month"] = work["timestamp"].dt.tz_localize(None).dt.to_period("M").astype(str)
    grouped = work.groupby(["month", "module"]).agg(
        assessments=("module", "count"),
        safety_overrides=("safety_override", "sum"),
        avg_key_metric=("key_metric", "mean"),
    ).reset_index()
    grouped["avg_key_metric"] = grouped["avg_key_metric"].round(2)
    return grouped


def build_monthly_excel(df: pd.DataFrame) -> bytes:
    """Builds a real downloadable .xlsx with:
      - 'Raw Log' sheet: every logged assessment
      - 'Monthly Summary' sheet: assessments/overrides/avg metric by month+module
      - 'Trend Chart' sheet: an embedded line chart (assessment count per
        month per module) - a real chart object in the workbook, not just
        a description of one.
    """
    summary = monthly_summary(df)

    buffer = io.BytesIO()
    export_df = df.copy()
    if not export_df.empty:
        # Excel has no concept of timezone-aware datetimes - strip the tz
        # info (values stay correct, just displayed as naive UTC) rather
        # than letting pandas raise ValueError on write.
        export_df["timestamp"] = export_df["timestamp"].dt.tz_localize(None)
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        (export_df if not export_df.empty else pd.DataFrame(columns=LOG_COLUMNS)).to_excel(
            writer, sheet_name="Raw Log", index=False
        )
        summary.to_excel(writer, sheet_name="Monthly Summary", index=False)
    buffer.seek(0)

    wb = load_workbook(buffer)
    chart_sheet = wb.create_sheet("Trend Chart")

    if not summary.empty:
        pivot = summary.pivot(index="month", columns="module", values="assessments").fillna(0)
        chart_sheet.append(["month"] + list(pivot.columns))
        for month, row in pivot.iterrows():
            chart_sheet.append([month] + list(row.values))

        chart = LineChart()
        chart.title = "Assessments per Month by Module"
        chart.y_axis.title = "Assessment count"
        chart.x_axis.title = "Month"
        n_rows, n_cols = pivot.shape
        data_ref = Reference(chart_sheet, min_col=2, max_col=1 + n_cols, min_row=1, max_row=1 + n_rows)
        cats_ref = Reference(chart_sheet, min_col=1, max_col=1, min_row=2, max_row=1 + n_rows)
        chart.add_data(data_ref, titles_from_data=True)
        chart.set_categories(cats_ref)
        chart_sheet.add_chart(chart, "H2")
    else:
        chart_sheet.append(["No data logged yet this session."])

    out_buffer = io.BytesIO()
    wb.save(out_buffer)
    return out_buffer.getvalue()
