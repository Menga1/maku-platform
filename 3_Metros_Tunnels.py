"""
MAKU - Metros & Tunnels (Underground) page
UI only. All calculations come from risk_engine.calculate_underground_kinetic_risk
(Mathematical Isolation rule - no formulas live in this file).

Supports two data modes, switchable per-page from the sidebar:
  - Manuel / Simulation : sliders, as before
  - Automatique / Temps Réel : arm the "LoRaWAN Tunnel" IoT sensor-hub toggle
    to stream simulated live gas (CO), dust (PM2.5), ambient temperature, and
    humidity readings (bounded random-walk with occasional realistic
    spikes - there is no public real-time API for underground sensor
    networks, so this is clearly simulated telemetry, not a live network
    call). A rare simulated dropout demonstrates the fail-safe: it shows a
    dashboard warning and reverts to manual sliders.
"""

import streamlit as st
from risk_engine import calculate_underground_kinetic_risk
from ai_advisor import get_controls, generate_narrative
from i18n import t, language_selector
from analytics import log_assessment
from data_feeds import simulate_tunnel_telemetry, DataFeedError
from ui_helpers import (
    render_data_mode_selector, render_stream_arm_toggle,
    render_feed_ok_banner, render_feed_error_banner, render_stream_not_armed_note,
    render_official_report, render_web_search_toggle, render_virtual_library,
)

st.set_page_config(page_title="MAKU - Underground (Tunnel/Metro)", page_icon="🚇", layout="wide")

lang = language_selector(st)

st.sidebar.title(t("app_title", lang))
st.sidebar.caption(t("app_tagline", lang))
st.sidebar.markdown("---")

data_mode = render_data_mode_selector(st, lang, module_key="metros")

st.sidebar.subheader(t("ai_layer_header", lang))
api_key = st.sidebar.text_input(
    t("api_key_label", lang), type="password", help=t("api_key_help", lang),
)
enable_web_search = render_web_search_toggle(st, lang, module_key="metros")

st.title(t("underground_header", lang))
st.caption(t("underground_caption", lang))

col_inputs, col_results = st.columns([1, 2])

live_data = None
live_error = None
stream_armed = False
effective_mode = "manual"

with col_inputs:
    st.header(t("underground_env_data_header", lang))

    if data_mode == "auto":
        stream_armed = render_stream_arm_toggle(
            st, lang, module_key="metros", label=t("iot_tunnel_toggle_label", lang),
        )
        if stream_armed:
            try:
                live_data = simulate_tunnel_telemetry()
                effective_mode = "auto"
            except DataFeedError as exc:
                live_error = str(exc)
        else:
            render_stream_not_armed_note(st, lang)

    if effective_mode == "auto":
        render_feed_ok_banner(st, lang, live_data["source"], live_data["fetched_at"])
        ambient_temp = st.slider(
            t("underground_ambient_temp_label", lang), 15.0, 45.0, live_data["ambient_temp"], disabled=True,
        )
        geothermal_humidity = st.slider(
            t("underground_geo_humidity_label", lang), 40.0, 100.0, live_data["geothermal_humidity"], disabled=True,
        )
        particulate_matter_pm25 = st.slider(
            t("underground_pm25_label", lang), 0.0, 400.0, live_data["pm25"], disabled=True,
        )
        gas_co_ppm = st.slider(
            t("underground_co_label", lang), 0.0, 60.0, live_data["gas_co_ppm"], disabled=True,
        )
    else:
        if live_error:
            render_feed_error_banner(st, lang, live_error)
        ambient_temp = st.slider(t("underground_ambient_temp_label", lang), 15.0, 45.0, 30.0)
        geothermal_humidity = st.slider(t("underground_geo_humidity_label", lang), 40.0, 100.0, 80.0)
        particulate_matter_pm25 = st.slider(t("underground_pm25_label", lang), 0.0, 400.0, 60.0)
        gas_co_ppm = st.slider(t("underground_co_label", lang), 0.0, 60.0, 12.0)

# Live calculation via the MAKU risk engine (Mathematical Isolation - no math here)
result = calculate_underground_kinetic_risk(
    ambient_temp, geothermal_humidity, particulate_matter_pm25, gas_co_ppm,
)
controls = get_controls(result)

with col_results:
    st.header(t("underground_realtime_header", lang))

    band = result["risk_band"]
    color = {"LOW": "green", "MODERATE": "orange", "HIGH": "red", "CRITICAL": "red"}[band]
    st.markdown(f"### {t('risk_band_label', lang)}: :{color}[{band}]")

    c1, c2, c3 = st.columns(3)
    c1.metric(t("underground_perceived_temp_label", lang), f"{result['perceived_temp']} °C")
    c2.metric(t("gas_exceeds_label", lang), t("yes", lang) if result["gas_exceeds"] else t("no", lang))
    c3.metric(t("dust_exceeds_label", lang), t("yes", lang) if result["dust_exceeds"] else t("no", lang))

    if result["safety_override"]:
        st.error(t("underground_critical_alert", lang))
    elif band in ("MODERATE", "HIGH"):
        st.warning(t("underground_high_alert", lang))
    else:
        st.success(t("underground_standard_ok", lang))

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

render_virtual_library(st, lang, module="Underground (Tunnel/Metro)")
