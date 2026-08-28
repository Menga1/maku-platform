"""
MAKU - Module 4: High-Rise Building Construction (Vertical Urban Environment)
==============================================================================
UI page for calculate_high_rise_kinetic_risk(). No free/keyless public API
reports crane-mounted anemometer or oscillation telemetry, so "Automatique"
mode arms a bounded random-walk simulator (data_feeds.simulate_crane_telemetry)
clearly labeled as simulated. Floor level is a site fact, not a sensor
reading, so it's always a manual input (it also feeds the shear-amplification
factor the simulator itself uses).
"""

import streamlit as st

from i18n import t, language_selector
from page_common import render_page_sidebar_header, render_ai_layer_sidebar
from risk_engine import calculate_high_rise_kinetic_risk, CRANE_SUSPEND_WIND_KNOTS
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
from data_feeds import simulate_crane_telemetry, DataFeedError

st.set_page_config(page_title="MAKU - High-Rise", page_icon="🏙️", layout="wide")

lang = language_selector(st)
render_page_sidebar_header(st, lang)
api_key = render_ai_layer_sidebar(st, lang)
enable_web_search = render_web_search_toggle(st, lang, "highrise")

st.title(t("highrise_header", lang))
st.caption(t("highrise_caption", lang))

st.subheader(t("highrise_floor_level_label", lang))
floor_level = st.slider(t("highrise_floor_level_label", lang), 1, 150, 40, 1, label_visibility="collapsed")

data_mode = render_data_mode_selector(st, lang, "highrise")

ground_wind_speed_knots = crane_load_mass_tons = None

if data_mode == "auto":
    armed = render_stream_arm_toggle(st, lang, "highrise", t("crane_telemetry_toggle_label", lang))
    if armed:
        try:
            telemetry = simulate_crane_telemetry(floor_level)
            render_feed_ok_banner(st, lang, telemetry["source"], telemetry["fetched_at"])
            ground_wind_speed_knots = telemetry["ground_wind_speed_knots"]
            crane_load_mass_tons = telemetry["crane_load_mass_tons"]

            st.subheader(t("highrise_realtime_header", lang))
            col1, col2, col3 = st.columns(3)
            col1.metric(t("highrise_ground_wind_label", lang), f"{ground_wind_speed_knots} kn")
            col2.metric(t("highrise_crane_load_label", lang), f"{crane_load_mass_tons} t")
            col3.metric("Shear factor", telemetry["shear_factor"], help=t("context_only_note", lang))
        except DataFeedError as exc:
            render_feed_error_banner(st, lang, str(exc))
            data_mode = "manual"
    else:
        render_stream_not_armed_note(st, lang)
        data_mode = "manual"

if data_mode == "manual":
    st.subheader(t("highrise_env_data_header", lang))
    col1, col2 = st.columns(2)
    with col1:
        ground_wind_speed_knots = st.slider(t("highrise_ground_wind_label", lang), 0.0, 55.0, 15.0, 0.5)
    with col2:
        crane_load_mass_tons = st.slider(t("highrise_crane_load_label", lang), 0.5, 25.0, 4.0, 0.5)

st.markdown("---")

if st.button(t("run_button", lang), type="primary", width="stretch"):
    result = calculate_high_rise_kinetic_risk(
        ground_wind_speed_knots=ground_wind_speed_knots,
        floor_level=floor_level,
        crane_load_mass_tons=crane_load_mass_tons,
    )
    controls = get_controls(result)
    narrative = generate_narrative(result, controls, api_key=api_key, lang=lang, enable_web_search=enable_web_search)

    log_assessment(st, result)
    st.session_state["latest_risk_result"] = result
    st.session_state["latest_ai_narrative"] = narrative
    st.session_state["latest_controls"] = controls

if st.session_state.get("latest_risk_result", {}).get("module") == "High-Rise (Vertical Urban)":
    result = st.session_state["latest_risk_result"]
    narrative = st.session_state["latest_ai_narrative"]
    controls = st.session_state["latest_controls"]

    if result["safety_override"]:
        st.error(t("safety_override", lang))
        st.error(t("highrise_critical_alert", lang))
        st.error(t("fall_arrest_alert", lang))
    elif result["risk_band"] in ("HIGH", "MODERATE"):
        st.warning(t("highrise_high_alert", lang))
    else:
        st.success(t("highrise_standard_ok", lang))

    col1, col2, col3 = st.columns(3)
    col1.metric(t("scaled_wind_label", lang), f"{result['scaled_wind_speed']} kn")
    col2.metric(t("oscillation_index_label", lang), result["oscillation_index"])
    col3.metric(t("crane_gate_label", lang), f"{CRANE_SUSPEND_WIND_KNOTS} kn")

    st.subheader(t("risk_band_label", lang))
    st.write(result["risk_band"])

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
render_virtual_library(st, lang, module="High-Rise (Vertical Urban)")
