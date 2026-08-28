"""
MAKU - High-Rise (Vertical Urban) page
UI only. All calculations come from risk_engine.calculate_high_rise_kinetic_risk
(Mathematical Isolation rule - no formulas live in this file).

Supports two data modes, switchable per-page from the sidebar:
  - Manuel / Simulation : sliders, as before
  - Automatique / Temps Réel : arm the "Crane Anemometer & Oscillation
    Sensor" toggle to stream simulated live ground wind speed and crane
    load telemetry (bounded random-walk with occasional realistic gusts -
    there is no public real-time API for crane-mounted sensors, so this is
    clearly simulated telemetry, not a live network call). A rare simulated
    dropout demonstrates the fail-safe: it shows a dashboard warning and
    reverts to manual sliders.
"""

import streamlit as st
from risk_engine import calculate_high_rise_kinetic_risk
from ai_advisor import get_controls, generate_narrative
from i18n import t, language_selector
from analytics import log_assessment
from data_feeds import simulate_crane_telemetry, DataFeedError
from ui_helpers import (
    render_data_mode_selector, render_stream_arm_toggle,
    render_feed_ok_banner, render_feed_error_banner, render_stream_not_armed_note,
    render_official_report, render_web_search_toggle, render_virtual_library,
)

st.set_page_config(page_title="MAKU - High-Rise", page_icon="🏗️", layout="wide")

lang = language_selector(st)

st.sidebar.title(t("app_title", lang))
st.sidebar.caption(t("app_tagline", lang))
st.sidebar.markdown("---")

data_mode = render_data_mode_selector(st, lang, module_key="highrise")

st.sidebar.subheader(t("ai_layer_header", lang))
api_key = st.sidebar.text_input(
    t("api_key_label", lang), type="password", help=t("api_key_help", lang),
)
enable_web_search = render_web_search_toggle(st, lang, module_key="highrise")

st.title(t("highrise_header", lang))
st.caption(t("highrise_caption", lang))

col_inputs, col_results = st.columns([1, 2])

live_data = None
live_error = None
stream_armed = False
effective_mode = "manual"

with col_inputs:
    st.header(t("highrise_env_data_header", lang))

    # Floor level is a site-configuration value (which floor the crew/crane is
    # operating on right now), not something a wind/oscillation sensor reports,
    # so it stays a manual input in both data modes.
    floor_level = st.slider(t("highrise_floor_level_label", lang), 1, 120, 40)

    if data_mode == "auto":
        stream_armed = render_stream_arm_toggle(
            st, lang, module_key="highrise", label=t("crane_telemetry_toggle_label", lang),
        )
        if stream_armed:
            try:
                live_data = simulate_crane_telemetry(floor_level)
                effective_mode = "auto"
            except DataFeedError as exc:
                live_error = str(exc)
        else:
            render_stream_not_armed_note(st, lang)

    if effective_mode == "auto":
        render_feed_ok_banner(st, lang, live_data["source"], live_data["fetched_at"])
        ground_wind_speed_knots = st.slider(
            t("highrise_ground_wind_label", lang), 0.0, 60.0,
            live_data["ground_wind_speed_knots"], disabled=True,
        )
        crane_load_mass_tons = st.slider(
            t("highrise_crane_load_label", lang), 0.5, 25.0,
            live_data["crane_load_mass_tons"], step=0.5, disabled=True,
        )
    else:
        if live_error:
            render_feed_error_banner(st, lang, live_error)
        ground_wind_speed_knots = st.slider(t("highrise_ground_wind_label", lang), 0.0, 60.0, 15.0)
        crane_load_mass_tons = st.slider(t("highrise_crane_load_label", lang), 0.5, 25.0, 4.0, step=0.5)

# Live calculation via the MAKU risk engine (Mathematical Isolation - no math here)
result = calculate_high_rise_kinetic_risk(ground_wind_speed_knots, floor_level, crane_load_mass_tons)
controls = get_controls(result)

with col_results:
    st.header(t("highrise_realtime_header", lang))

    band = result["risk_band"]
    color = {"LOW": "green", "MODERATE": "orange", "HIGH": "red", "CRITICAL": "red"}[band]
    st.markdown(f"### {t('risk_band_label', lang)}: :{color}[{band}]")

    c1, c2, c3 = st.columns(3)
    c1.metric(t("scaled_wind_label", lang), f"{result['scaled_wind_speed']} kt")
    c2.metric(t("oscillation_index_label", lang), result["oscillation_index"])
    c3.metric(t("risk_level_label", lang), band)

    if result["safety_override"]:
        st.error(t("highrise_critical_alert", lang))
    elif band in ("MODERATE", "HIGH"):
        st.warning(t("highrise_high_alert", lang))
    else:
        st.success(t("highrise_standard_ok", lang))

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

render_virtual_library(st, lang, module="High-Rise (Vertical Urban)")
