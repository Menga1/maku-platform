"""
MAKU - Module 2: Offshore Oil & Gas (Marine Environment)
=========================================================
UI page for calculate_marine_humidex_risk(). All risk math stays in
risk_engine.py - this file only collects inputs (manual sliders or the
live Open-Meteo forecast + Marine API feed) and renders the result.

Wave height / ocean current are shown as context-only readouts (per
data_feeds.py and i18n's context_only_note) since the current risk_engine
formula doesn't consume them - they're wired through so a future formula
change is a data-plumbing non-event, not a new UI to build.
"""

import streamlit as st

from i18n import t, language_selector
from page_common import render_page_sidebar_header, render_ai_layer_sidebar, render_acgih_reference_panel
from risk_engine import calculate_marine_humidex_risk
from ai_advisor import get_controls, generate_narrative
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
from data_feeds import fetch_offshore_live, fetch_offshore_forecast, DataFeedError

WIND_STATUS_KEY = {
    "Normal Operations": "wind_status_normal",
    "Restricted - Monitor Closely": "wind_status_restricted",
    "Suspended - Crane/Lifting Danger": "wind_status_suspended",
}

st.set_page_config(page_title="MAKU - Offshore Oil & Gas", page_icon="🌊", layout="wide")

lang = language_selector(st)
render_page_sidebar_header(st, lang)
api_key = render_ai_layer_sidebar(st, lang)
enable_web_search = render_web_search_toggle(st, lang, "offshore")

st.title(t("offshore_header", lang))
st.caption(t("offshore_caption", lang))

data_mode = render_data_mode_selector(st, lang, "offshore")

ambient_temp = relative_humidity = wind_speed = None
wave_height = ocean_current = None

if data_mode == "auto":
    try:
        live = fetch_offshore_live()
        render_feed_ok_banner(st, lang, live["source"], live["fetched_at"])
        ambient_temp = live["temperature_2m"]
        relative_humidity = live["relative_humidity_2m"]
        wind_speed = live["wind_speed_10m_kn"]
        wave_height = live["wave_height_m"]
        ocean_current = live["ocean_current_velocity_ms"]

        st.subheader(t("offshore_realtime_header", lang))
        col1, col2, col3 = st.columns(3)
        col1.metric(t("offshore_temp_label", lang), f"{ambient_temp} °C")
        col2.metric(t("offshore_rh_label", lang), f"{relative_humidity} %")
        col3.metric(t("offshore_wind_label", lang), f"{wind_speed} kn")

        col4, col5 = st.columns(2)
        col4.metric(t("wave_height_label", lang), f"{wave_height} m", help=t("context_only_note", lang))
        col5.metric(t("ocean_current_label", lang), f"{ocean_current} m/s", help=t("context_only_note", lang))
        st.caption(t("context_only_note", lang))
    except DataFeedError as exc:
        render_feed_error_banner(st, lang, str(exc))
        data_mode = "manual"

if data_mode == "manual":
    st.subheader(t("offshore_env_data_header", lang))
    col1, col2, col3 = st.columns(3)
    with col1:
        ambient_temp = st.slider(t("offshore_temp_label", lang), 15.0, 45.0, 30.0, 0.5)
    with col2:
        relative_humidity = st.slider(t("offshore_rh_label", lang), 30.0, 100.0, 75.0, 1.0)
    with col3:
        wind_speed = st.slider(t("offshore_wind_label", lang), 0.0, 60.0, 15.0, 0.5)

render_acgih_reference_panel(st, lang, ambient_temp, relative_humidity)

with st.expander("📡 " + ("Prévision météo 7 jours" if lang == "fr" else "7-Day Meteorology Forecast")):
    try:
        forecast = fetch_offshore_forecast()
        render_meteorology_forecast(
            st, lang, forecast,
            fields=[
                ("temperature_2m_max", t("offshore_temp_label", lang)),
                ("wind_speed_10m_max_kn", t("offshore_wind_label", lang)),
            ],
        )
    except DataFeedError as exc:
        st.info(str(exc))

st.markdown("---")

if st.button(t("run_button", lang), type="primary", width="stretch"):
    result = calculate_marine_humidex_risk(
        ambient_temp=ambient_temp, relative_humidity=relative_humidity, wind_speed=wind_speed
    )
    controls = get_controls(result)
    narrative = generate_narrative(result, controls, api_key=api_key, lang=lang, enable_web_search=enable_web_search)

    log_assessment(st, result)
    st.session_state["latest_risk_result"] = result
    st.session_state["latest_ai_narrative"] = narrative
    st.session_state["latest_controls"] = controls

if st.session_state.get("latest_risk_result", {}).get("module") == "Offshore (Marine)":
    result = st.session_state["latest_risk_result"]
    narrative = st.session_state["latest_ai_narrative"]
    controls = st.session_state["latest_controls"]

    if result["safety_override"]:
        st.error(t("safety_override", lang))
        st.error(t("offshore_elevated_alert", lang))
    elif result["risk_band"] in ("Moderate", "High", "Extreme"):
        st.warning(t("offshore_elevated_alert", lang))
    else:
        st.success(t("offshore_standard_ok", lang))

    col1, col2, col3 = st.columns(3)
    col1.metric(t("humidex_label", lang), f"{result['humidex']} °C")
    col2.metric(t("risk_band_label", lang), result["risk_band"])
    col3.metric(
        t("wind_status_label", lang),
        t(WIND_STATUS_KEY.get(result["wind_risk_status"], "wind_status_normal"), lang),
    )

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
render_virtual_library(st, lang, module="Offshore (Marine)")
