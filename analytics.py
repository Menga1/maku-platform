"""
MAKU - Assessment Log, Trend Analytics & Excel Export
=========================================================
Logs every risk assessment run during a session, and builds a real
downloadable .xlsx (openpyxl) with a raw-data sheet, a monthly summary
sheet, and an embedded trend chart.

PERSISTENCE CAVEAT - read this before assuming this is a database:
Streamlit Cloud gives each app ephemeral local storage. Any file this
process writes to disk is wiped on redeploy, reboot, or (eventually)
inactivity. There is no built-in database here. So the log is
session-scoped: it only remembers what ran during the current browser
session. To build a real multi-week/monthly history, the user carries
it forward manually - download the CSV periodically, and upload it back
in on a later session to merge with whatever ran since. This is an
honest, low-tech substitute for a real backend, not a claim that one
exists. If this ever needs true persistence, the fix is a real datastore
(e.g. a hosted Postgres/SQLite file via an external service) - swapping
that in only touches this file, not risk_engine.py or the pages.

Mathematical Isolation rule still applies: this file aggregates/logs
results computed elsewhere. It never computes risk itself.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone

import pandas as pd
from openpyxl import load_workbook
from openpyxl.chart import LineChart, Reference

LOG_SESSION_KEY = "assessment_log"

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


def log_assessment(st_module, result: dict) -> None:
    """Append one row to this session's in-memory assessment log. Call
    right after computing a result on any module page."""
    if LOG_SESSION_KEY not in st_module.session_state:
        st_module.session_state[LOG_SESSION_KEY] = []
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
    st_module.session_state[LOG_SESSION_KEY].append(row)


def get_log_dataframe(st_module) -> pd.DataFrame:
    """Current session's log as a DataFrame, oldest first, timestamp parsed."""
    rows = st_module.session_state.get(LOG_SESSION_KEY, [])
    if not rows:
        return pd.DataFrame(columns=LOG_COLUMNS)
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)


def merge_uploaded_csv(st_module, uploaded_file) -> int:
    """Parses a previously-downloaded CSV log and merges it into this
    session's log, de-duplicating exact repeats. Returns how many new
    rows were actually added (0 if everything was already present)."""
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

    records = combined.to_dict("records")
    for row in records:
        ts = row["timestamp"]
        row["timestamp"] = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
    st_module.session_state[LOG_SESSION_KEY] = records
    return len(combined) - before


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
