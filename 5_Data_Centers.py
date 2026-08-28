"""
MAKU - Module 5: Data Center Construction & Commissioning
==========================================================
UI page for calculate_datacenter_kinetic_risk(). No free/keyless public API
reports rack-level current-transformer/thermal-probe telemetry, so
"Automatique" mode arms a bounded random-walk simulator
(data_feeds.simulate_datacenter_telemetry) clearly labeled as simulated.
Confined-space and gas-suppression-armed state are site/operational facts,
not sensor readings, so they're always manual checkboxes even in auto mode.
"""

import streamlit as st

from i18n import t, language_selector
from page_common import render_page_sidebar_header, render_ai_layer_sidebar
from risk_engine import calculate_datacenter_kinetic_risk, DATACENTER_ARC_FLASH_DANGER_CAL
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
from data_feeds import simulate_datacenter_telemetry, DataFeedError

st.set_page_config(page_title="MAKU - Data Centers", page_icon="🖥️", layout="wide")

lang = language_selector(st)
render_page_sidebar_header(st, lang)
api_key = render_ai_layer_sidebar(st, lang)
enable_web_search = render_web_search_toggle(st, lang, "datacenter")

st.title(t("datacenter_header", lang))
st.caption(t("datacenter_caption", lang))

data_mode = render_data_mode_selector(st, lang, "datacenter")

electrical_load_kw = hot_aisle_temp = None

if data_mode == "auto":
    armed = render_stream_arm_toggle(st, lang, "datacenter", t("dc_telemetry_toggle_label", lang))
    if armed:
        try:
            telemetry = simulate_datacenter_telemetry()
            render_feed_ok_banner(st, lang, telemetry["source"], telemetry["fetched_at"])
            electrical_load_kw = telemetry["electrical_load_kw"]
            hot_aisle_temp = telemetry["hot_aisle_temp"]

            st.subheader(t("datacenter_realtime_header", lang))
            col1, col2 = st.columns(2)
            col1.metric(t("datacenter_load_label", lang), f"{electrical_load_kw} kW")
            col2.metric(t("datacenter_hot_aisle_label", lang), f"{hot_aisle_temp} °C")
        except DataFeedError as exc:
            render_feed_error_banner(st, lang, str(exc))
            data_mode = "manual"
    else:
        render_stream_not_armed_note(st, lang)
        data_mode = "manual"

if data_mode == "manual":
    st.subheader(t("datacenter_env_data_header", lang))
    col1, col2 = st.columns(2)
    with col1:
        electrical_load_kw = st.slider(t("datacenter_load_label", lang), 20.0, 2000.0, 400.0, 10.0)
    with col2:
        hot_aisle_temp = st.slider(t("datacenter_hot_aisle_label", lang), 20.0, 55.0, 34.0, 0.5)

st.subheader(t("confined_clean_agent_label", lang))
col1, col2 = st.columns(2)
with col1:
    ceiling_void_confined = st.checkbox(t("datacenter_confined_label", lang))
with col2:
    gas_system_armed = st.checkbox(t("datacenter_gas_armed_label", lang))

st.markdown("---")

if st.button(t("run_button", lang), type="primary", width="stretch"):
    result = calculate_datacenter_kinetic_risk(
        electrical_load_kw=electrical_load_kw,
        hot_aisle_temp=hot_aisle_temp,
        ceiling_void_confined=ceiling_void_confined,
        gas_system_armed=gas_system_armed,
    )
    controls = get_controls(result)
    narrative = generate_narrative(result, controls, api_key=api_key, lang=lang, enable_web_search=enable_web_search)

    log_assessment(st, result)
    st.session_state["latest_risk_result"] = result
    st.session_state["latest_ai_narrative"] = narrative
    st.session_state["latest_controls"] = controls

if st.session_state.get("latest_risk_result", {}).get("module") == "Data Center (Controlled Critical Environment)":
    result = st.session_state["latest_risk_result"]
    narrative = st.session_state["latest_ai_narrative"]
    controls = st.session_state["latest_controls"]

    if result["safety_override"]:
        st.error(t("safety_override", lang))
        st.error(t("datacenter_critical_alert", lang))
    elif result["risk_band"] == "HIGH":
        st.warning(t("datacenter_high_alert", lang))
    else:
        st.success(t("datacenter_standard_ok", lang))

    col1, col2, col3 = st.columns(3)
    col1.metric(t("arc_flash_energy_label", lang), f"{result['arc_flash_energy_cal']} cal/cm²")
    col2.metric(t("thermal_differential_label", lang), f"{result['thermal_differential']} °C")
    col3.metric(t("esd_risk_label", lang), result["risk_band"])

    if result["arc_flash_danger"]:
        st.caption(f"⚠️ {t('arc_flash_energy_label', lang)} > {DATACENTER_ARC_FLASH_DANGER_CAL} cal/cm²")
    if result["confined_armed_danger"]:
        st.caption(f"⚠️ {t('confined_clean_agent_label', lang)}")

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
render_virtual_library(st, lang, module="Data Center (Controlled Critical Environment)")
