"""
MAKU - Module 1: Utility-Scale Solar Farms (Desert Environment)
================================================================
UI page for calculate_solar_albedo_heat_risk(). All risk math stays in
risk_engine.py (Mathematical Isolation rule) - this file only collects
inputs (manual sliders or the live Open-Meteo feed via data_feeds.py),
calls the engine, and renders the result.

Live data note: GHI/UV/temp come from Open-Meteo's free, keyless forecast
API (data_feeds.fetch_solar_live) - a real HTTP call, not a simulation.
Surface type is not something a weather API reports, so it stays a manual
selector even in "Automatique" mode.
"""

import streamlit as st

from i18n import t, language_selector
from page_common import render_page_sidebar_header, render_ai_layer_sidebar, render_acgih_reference_panel
from risk_engine import calculate_solar_albedo_heat_risk
from ai_advisor import get_controls, generate_narrative, get_regulatory_references, get_bibliography
from ui_helpers import (
    render_official_report,
    render_data_mode_selector,
    render_feed_ok_banner,
    render_feed_error_banner,
    render_virtual_library,
    render_web_search_toggle,
    render_meteorology_forecast,
)
from analytics import log_assessment
from data_feeds import fetch_solar_live, fetch_solar_forecast, DataFeedError

SURFACE_OPTIONS = ["pure_desert_sand", "silicon_pv_panels", "hybrid_assembly_zone"]

st.set_page_config(page_title="MAKU - Solar Farms", page_icon="☀️", layout="wide")

lang = language_selector(st)
render_page_sidebar_header(st, lang)
api_key = render_ai_layer_sidebar(st, lang)
enable_web_search = render_web_search_toggle(st, lang, "solar")

st.title(t("solar_header", lang))
st.caption(t("solar_caption", lang))

data_mode = render_data_mode_selector(st, lang, "solar")

ambient_temp = uv_index = ghi = None
surface_type = SURFACE_OPTIONS[0]

if data_mode == "auto":
    try:
        live = fetch_solar_live()
        render_feed_ok_banner(st, lang, live["source"], live["fetched_at"])
        ambient_temp = live["temperature_2m"]
        uv_index = live["uv_index"]
        ghi = live["shortwave_radiation"]

        st.subheader(t("solar_realtime_header", lang))
        col1, col2, col3 = st.columns(3)
        col1.metric(t("solar_temp_label", lang), f"{ambient_temp} °C")
        col2.metric(t("solar_uv_label", lang), uv_index)
        col3.metric(t("solar_ghi_label", lang), f"{ghi} W/m²")

        surface_type = st.selectbox(
            t("solar_surface_label", lang),
            options=SURFACE_OPTIONS,
            format_func=lambda v: t(f"surf_{v}", lang),
            key="solar_surface_auto",
        )
    except DataFeedError as exc:
        render_feed_error_banner(st, lang, str(exc))
        data_mode = "manual"

if data_mode == "manual":
    st.subheader(t("solar_env_data_header", lang))
    col1, col2, col3 = st.columns(3)
    with col1:
        ambient_temp = st.slider(t("solar_temp_label", lang), 15.0, 55.0, 32.0, 0.5)
    with col2:
        ghi = st.slider(t("solar_ghi_label", lang), 0.0, 1200.0, 650.0, 10.0)
    with col3:
        uv_index = st.slider(t("solar_uv_label", lang), 0.0, 14.0, 7.0, 0.5)
    surface_type = st.selectbox(
        t("solar_surface_label", lang),
        options=SURFACE_OPTIONS,
        format_func=lambda v: t(f"surf_{v}", lang),
        key="solar_surface_manual",
    )

render_acgih_reference_panel(st, lang, ambient_temp, relative_humidity=30.0)

with st.expander("📡 " + ("Prévision météo 7 jours" if lang == "fr" else "7-Day Meteorology Forecast")):
    try:
        forecast = fetch_solar_forecast()
        render_meteorology_forecast(
            st, lang, forecast,
            fields=[
                ("temperature_2m_max", t("solar_temp_label", lang)),
                ("uv_index_max", t("solar_uv_label", lang)),
            ],
        )
    except DataFeedError as exc:
        st.info(str(exc))

st.markdown("---")

if st.button(t("run_button", lang), type="primary", width="stretch"):
    result = calculate_solar_albedo_heat_risk(
        ghi=ghi, uv_index=uv_index, ambient_temp=ambient_temp, surface_type=surface_type
    )
    controls = get_controls(result)
    narrative = generate_narrative(result, controls, api_key=api_key, lang=lang, enable_web_search=enable_web_search)

    log_assessment(st, result)
    st.session_state["latest_risk_result"] = result
    st.session_state["latest_ai_narrative"] = narrative
    st.session_state["latest_controls"] = controls

if st.session_state.get("latest_risk_result", {}).get("module") == "Solar (Desert)":
    result = st.session_state["latest_risk_result"]
    narrative = st.session_state["latest_ai_narrative"]
    controls = st.session_state["latest_controls"]

    if result["risk_level"] == "CRITICAL":
        st.error(t("solar_critical_alert", lang))
    elif result["risk_level"] == "HIGH":
        st.warning(t("solar_high_alert", lang))
    else:
        st.success(t("solar_standard_ok", lang))

    if result["safety_override"]:
        st.error(t("safety_override", lang))

    col1, col2, col3 = st.columns(3)
    col1.metric(t("perceived_temp_label", lang), f"{result['perceived_temp']} °C")
    col2.metric(t("risk_level_label", lang), result["risk_level"])
    col3.metric(t("shift_rotation_label", lang), result["max_shift_duration"])

    st.subheader(t("drivers_label", lang))
    st.table({k: str(v) for k, v in result["drivers"].items()})

    st.subheader(t("briefing_label", lang))
    st.write(narrative)

    st.subheader(t("controls_label", lang))
    for control in controls:
        st.markdown(f"- {control}")

    st.markdown("---")
    render_official_report(st, result=result, narrative=narrative, controls=controls, lang=lang)

st.markdown("---")
render_virtual_library(st, lang, module="Solar (Desert)")
