"""
MAKU - Data Center Construction & Commissioning page
UI only. All calculations come from risk_engine.calculate_datacenter_kinetic_risk
(Mathematical Isolation rule - no formulas live in this file).

Supports two data modes, switchable per-page from the sidebar:
  - Manuel / Simulation : sliders/checkboxes, as before
  - Automatique / Temps Réel : arm the "Current Transformer & Thermal Probe"
    toggle to stream simulated live electrical load (amperage/kW) and
    hot-aisle thermal telemetry directly into the arc-flash engine (bounded
    random-walk with occasional realistic spikes - there is no public
    real-time API for a data center's electrical/thermal plant, so this is
    clearly simulated telemetry, not a live network call). A rare simulated
    dropout demonstrates the fail-safe: it shows a dashboard warning and
    reverts to manual controls.
"""

import streamlit as st
from risk_engine import calculate_datacenter_kinetic_risk
from ai_advisor import get_controls, generate_narrative
from i18n import t, language_selector
from analytics import log_assessment
from data_feeds import simulate_datacenter_telemetry, DataFeedError
from ui_helpers import (
    render_data_mode_selector, render_stream_arm_toggle,
    render_feed_ok_banner, render_feed_error_banner, render_stream_not_armed_note,
    render_official_report, render_web_search_toggle, render_virtual_library,
)

st.set_page_config(page_title="MAKU - Data Center", page_icon="🏢", layout="wide")

lang = language_selector(st)

st.sidebar.title(t("app_title", lang))
st.sidebar.caption(t("app_tagline", lang))
st.sidebar.markdown("---")

data_mode = render_data_mode_selector(st, lang, module_key="datacenter")

st.sidebar.subheader(t("ai_layer_header", lang))
api_key = st.sidebar.text_input(
    t("api_key_label", lang), type="password", help=t("api_key_help", lang),
)
enable_web_search = render_web_search_toggle(st, lang, module_key="datacenter")

st.title(t("datacenter_header", lang))
st.caption(t("datacenter_caption", lang))

col_inputs, col_results = st.columns([1, 2])

live_data = None
live_error = None
stream_armed = False
effective_mode = "manual"

with col_inputs:
    st.header(t("datacenter_env_data_header", lang))

    # Site-configuration switches (confined ceiling void, gas suppression
    # system armed) are facility-state facts, not sensor telemetry, so they
    # stay manual checkboxes in both data modes.
    ceiling_void_confined = st.checkbox(t("datacenter_confined_label", lang), value=False)
    gas_system_armed = st.checkbox(t("datacenter_gas_armed_label", lang), value=True)

    if data_mode == "auto":
        stream_armed = render_stream_arm_toggle(
            st, lang, module_key="datacenter", label=t("dc_telemetry_toggle_label", lang),
        )
        if stream_armed:
            try:
                live_data = simulate_datacenter_telemetry()
                effective_mode = "auto"
            except DataFeedError as exc:
                live_error = str(exc)
        else:
            render_stream_not_armed_note(st, lang)

    if effective_mode == "auto":
        render_feed_ok_banner(st, lang, live_data["source"], live_data["fetched_at"])
        electrical_load_kw = st.slider(
            t("datacenter_load_label", lang), 10.0, 2000.0,
            live_data["electrical_load_kw"], step=10.0, disabled=True,
        )
        hot_aisle_temp = st.slider(
            t("datacenter_hot_aisle_label", lang), 20.0, 55.0,
            live_data["hot_aisle_temp"], disabled=True,
        )
    else:
        if live_error:
            render_feed_error_banner(st, lang, live_error)
        electrical_load_kw = st.slider(t("datacenter_load_label", lang), 10.0, 2000.0, 400.0, step=10.0)
        hot_aisle_temp = st.slider(t("datacenter_hot_aisle_label", lang), 20.0, 55.0, 34.0)

# Live calculation via the MAKU risk engine (Mathematical Isolation - no math here)
result = calculate_datacenter_kinetic_risk(
    electrical_load_kw, hot_aisle_temp, ceiling_void_confined, gas_system_armed,
)
controls = get_controls(result)

with col_results:
    st.header(t("datacenter_realtime_header", lang))

    band = result["risk_band"]
    color = {"LOW": "green", "MODERATE": "orange", "HIGH": "red", "CRITICAL": "red"}[band]
    st.markdown(f"### {t('risk_band_label', lang)}: :{color}[{band}]")

    c1, c2, c3 = st.columns(3)
    c1.metric(t("arc_flash_energy_label", lang), result["arc_flash_energy_cal"])
    c2.metric(t("thermal_differential_label", lang), result["thermal_differential"])
    c3.metric(t("risk_level_label", lang), band)

    if result["safety_override"]:
        st.error(t("datacenter_critical_alert", lang))
    elif band in ("MODERATE", "HIGH"):
        st.warning(t("datacenter_high_alert", lang))
    else:
        st.success(t("datacenter_standard_ok", lang))

    st.markdown(
        f"**{t('confined_clean_agent_label', lang)}:** "
        f"{t('yes', lang) if result['confined_armed_danger'] else t('no', lang)}"
    )
    st.markdown(f"**{t('primary_hazard_label', lang)}:** {result['primary_hazard']}")

    with st.expander(t("drivers_label", lang)):
        st.json(result["drivers"])

    st.subheader(t("controls_label", lang))
    for c in controls:
        st.markdown(f"- {c}")

    st.subheader(t("briefing_label", lang))
    narrative = generate_narrative(result, controls, api_key, lang, enable_web_search)
    st.info(narrative)

st.session_state["latest_risk_result"] = result
log_assessment(st, result)
st.session_state["latest_controls"] = controls
st.session_state["latest_ai_narrative"] = narrative

render_official_report(st, result, narrative, controls, lang)

render_virtual_library(st, lang, module="Data Center (Controlled Critical Environment)")
