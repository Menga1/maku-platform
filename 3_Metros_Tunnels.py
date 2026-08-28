"""
MAKU - Module 3: Metros & Tunnels (Underground Substructure Infrastructure)
============================================================================
UI page for calculate_underground_kinetic_risk(). No free/keyless public
API exists for underground gas/dust/heat sensors, so "Automatique" mode
here arms a bounded random-walk simulator (data_feeds.simulate_tunnel_telemetry)
that mimics a live LoRaWAN sensor-hub stream - clearly labeled as simulated,
never presented as real data.
"""

import streamlit as st

from i18n import t, language_selector
from page_common import render_page_sidebar_header, render_ai_layer_sidebar, render_acgih_reference_panel
from risk_engine import calculate_underground_kinetic_risk
from ai_advisor import get_controls, generate_narrative
from ui_helpers import (
    render_official_report,
    render_data_mode_selector,
    render_stream_arm_toggle,
    render_stream_not_armed_note,
    render_feed_ok_banner,
    render_feed_error_banner,
    render_virtual_library,
    render_web_search_toggle,
)
from analytics import log_assessment
from data_feeds import simulate_tunnel_telemetry, DataFeedError

st.set_page_config(page_title="MAKU - Metros & Tunnels", page_icon="🚇", layout="wide")

lang = language_selector(st)
render_page_sidebar_header(st, lang)
api_key = render_ai_layer_sidebar(st, lang)
enable_web_search = render_web_search_toggle(st, lang, "underground")

st.title(t("underground_header", lang))
st.caption(t("underground_caption", lang))

data_mode = render_data_mode_selector(st, lang, "underground")

ambient_temp = geothermal_humidity = pm25 = gas_co_ppm = None

if data_mode == "auto":
    armed = render_stream_arm_toggle(st, lang, "underground", t("iot_tunnel_toggle_label", lang))
    if armed:
        try:
            telemetry = simulate_tunnel_telemetry()
            render_feed_ok_banner(st, lang, telemetry["source"], telemetry["fetched_at"])
            ambient_temp = telemetry["ambient_temp"]
            geothermal_humidity = telemetry["geothermal_humidity"]
            pm25 = telemetry["pm25"]
            gas_co_ppm = telemetry["gas_co_ppm"]

            st.subheader(t("underground_realtime_header", lang))
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(t("underground_ambient_temp_label", lang), f"{ambient_temp} °C")
            col2.metric(t("underground_geo_humidity_label", lang), f"{geothermal_humidity} %")
            col3.metric(t("underground_pm25_label", lang), f"{pm25} µg/m³")
            col4.metric(t("underground_co_label", lang), f"{gas_co_ppm} ppm")
        except DataFeedError as exc:
            render_feed_error_banner(st, lang, str(exc))
            data_mode = "manual"
    else:
        render_stream_not_armed_note(st, lang)
        data_mode = "manual"

if data_mode == "manual":
    st.subheader(t("underground_env_data_header", lang))
    col1, col2 = st.columns(2)
    with col1:
        ambient_temp = st.slider(t("underground_ambient_temp_label", lang), 15.0, 45.0, 28.0, 0.5)
        pm25 = st.slider(t("underground_pm25_label", lang), 0.0, 400.0, 60.0, 5.0)
    with col2:
        geothermal_humidity = st.slider(t("underground_geo_humidity_label", lang), 40.0, 100.0, 80.0, 1.0)
        gas_co_ppm = st.slider(t("underground_co_label", lang), 0.0, 60.0, 10.0, 0.5)

render_acgih_reference_panel(st, lang, ambient_temp, geothermal_humidity)

st.markdown("---")

if st.button(t("run_button", lang), type="primary", width="stretch"):
    result = calculate_underground_kinetic_risk(
        ambient_temp=ambient_temp,
        geothermal_humidity=geothermal_humidity,
        particulate_matter_pm25=pm25,
        gas_co_ppm=gas_co_ppm,
    )
    controls = get_controls(result)
    narrative = generate_narrative(result, controls, api_key=api_key, lang=lang, enable_web_search=enable_web_search)

    log_assessment(st, result)
    st.session_state["latest_risk_result"] = result
    st.session_state["latest_ai_narrative"] = narrative
    st.session_state["latest_controls"] = controls

if st.session_state.get("latest_risk_result", {}).get("module") == "Underground (Tunnel/Metro)":
    result = st.session_state["latest_risk_result"]
    narrative = st.session_state["latest_ai_narrative"]
    controls = st.session_state["latest_controls"]

    if result["safety_override"]:
        st.error(t("safety_override", lang))
        st.error(t("underground_critical_alert", lang))
    elif result["risk_band"] in ("MODERATE", "HIGH"):
        st.warning(t("underground_high_alert", lang))
    else:
        st.success(t("underground_standard_ok", lang))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("underground_perceived_temp_label", lang), f"{result['perceived_temp']} °C")
    col2.metric(t("risk_band_label", lang), result["risk_band"])
    col3.metric(t("gas_exceeds_label", lang), t("yes", lang) if result["gas_exceeds"] else t("no", lang))
    col4.metric(t("dust_exceeds_label", lang), t("yes", lang) if result["dust_exceeds"] else t("no", lang))

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
render_virtual_library(st, lang, module="Underground (Tunnel/Metro)")
