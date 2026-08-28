"""
MAKU - Offshore Oil & Gas (Marine) page
UI only. All calculations come from risk_engine.calculate_marine_humidex_risk
(Mathematical Isolation rule - no formulas live in this file).

Supports two data modes, switchable per-page from the sidebar:
  - Manuel / Simulation : sliders, as before
  - Automatique / Temps Réel : live Open-Meteo forecast API (temperature,
    humidity, wind) + Open-Meteo Marine API (wave height, ocean current
    velocity) for the offshore block coordinates. Wave height and current
    velocity are shown as live contextual readouts - the risk engine itself
    only consumes temperature/humidity/wind, per its existing formula. Any
    network/API error falls back safely to manual sliders.
"""

import streamlit as st
from risk_engine import calculate_marine_humidex_risk
from ai_advisor import get_controls, generate_narrative
from i18n import t, language_selector
from analytics import log_assessment
from data_feeds import fetch_offshore_live, fetch_offshore_forecast, DataFeedError, OFFSHORE_COORDS
from ui_helpers import render_data_mode_selector, render_feed_ok_banner, render_feed_error_banner, render_official_report, render_web_search_toggle, render_virtual_library, render_meteorology_forecast

st.set_page_config(page_title="MAKU - Offshore (Marine)", page_icon="🌊", layout="wide")

lang = language_selector(st)

st.sidebar.title(t("app_title", lang))
st.sidebar.caption(t("app_tagline", lang))
st.sidebar.markdown("---")

data_mode = render_data_mode_selector(st, lang, module_key="offshore")

st.sidebar.subheader(t("ai_layer_header", lang))
api_key = st.sidebar.text_input(
    t("api_key_label", lang), type="password", help=t("api_key_help", lang),
)
enable_web_search = render_web_search_toggle(st, lang, module_key="offshore")

st.title(t("offshore_header", lang))
st.caption(t("offshore_caption", lang))

with st.expander("📈 " + ("Prévisions Météo (7 jours)" if lang == "fr" else "7-Day Meteorology Forecast")):
    try:
        forecast = fetch_offshore_forecast(OFFSHORE_COORDS["lat"], OFFSHORE_COORDS["lon"])
        render_meteorology_forecast(
            st, lang, forecast,
            fields=[
                ("temperature_2m_max", "Temp max (°C)"),
                ("wind_speed_10m_max_kn", "Vent max (nds)" if lang == "fr" else "Wind max (kn)"),
            ],
        )
    except DataFeedError as exc:
        st.warning(("Prévisions indisponibles: " if lang == "fr" else "Forecast unavailable: ") + str(exc))

col_inputs, col_results = st.columns([1, 2])

live_data = None
live_error = None
effective_mode = data_mode

if data_mode == "auto":
    try:
        live_data = fetch_offshore_live(OFFSHORE_COORDS["lat"], OFFSHORE_COORDS["lon"])
    except DataFeedError as exc:
        live_error = str(exc)
        effective_mode = "manual"

with col_inputs:
    st.header(t("offshore_env_data_header", lang))

    if effective_mode == "auto":
        render_feed_ok_banner(st, lang, live_data["source"], live_data["fetched_at"])
        o_temp_c = st.slider(
            t("offshore_temp_label", lang), 15.0, 45.0,
            float(min(45.0, max(15.0, live_data["temperature_2m"]))), disabled=True,
        )
        o_rh_pct = st.slider(
            t("offshore_rh_label", lang), 40.0, 100.0,
            float(min(100.0, max(40.0, live_data["relative_humidity_2m"]))), disabled=True,
        )
        wind_knots = st.slider(
            t("offshore_wind_label", lang), 0.0, 50.0,
            float(min(50.0, max(0.0, live_data["wind_speed_10m_kn"]))), disabled=True,
        )

        st.caption(f"🌊 {t('telemetry_readout_label', lang)}")
        wc1, wc2 = st.columns(2)
        wc1.metric(t("wave_height_label", lang), f"{live_data['wave_height_m']} m")
        wc2.metric(t("ocean_current_label", lang), f"{live_data['ocean_current_velocity_ms']} m/s")
        st.caption(t("context_only_note", lang))
    else:
        if live_error:
            render_feed_error_banner(st, lang, live_error)
        o_temp_c = st.slider(t("offshore_temp_label", lang), 15.0, 45.0, 33.0)
        o_rh_pct = st.slider(t("offshore_rh_label", lang), 40.0, 100.0, 92.0)
        wind_knots = st.slider(t("offshore_wind_label", lang), 0.0, 50.0, 15.0)

# Live calculation via the MAKU risk engine (Mathematical Isolation - no math here)
result = calculate_marine_humidex_risk(o_temp_c, o_rh_pct, wind_knots)
controls = get_controls(result)

WIND_STATUS_KEYS = {
    "Normal Operations": "wind_status_normal",
    "Restricted - Monitor Closely": "wind_status_restricted",
    "Suspended - Crane/Lifting Danger": "wind_status_suspended",
}

with col_results:
    st.header(t("offshore_realtime_header", lang))

    band = result["risk_band"]
    color = {"Low": "green", "Moderate": "orange", "High": "red", "Extreme": "red"}[band]
    st.markdown(f"### {t('risk_band_label', lang)}: :{color}[{band}]")

    c1, c2, c3 = st.columns(3)
    c1.metric(t("humidex_label", lang), result["humidex"])
    c2.metric(
        t("wind_status_label", lang),
        t(WIND_STATUS_KEYS.get(result["wind_risk_status"], "wind_status_normal"), lang),
    )
    c3.metric(t("risk_level_label", lang), band)

    if result["safety_override"]:
        st.error(t("safety_override", lang))
    elif band in ("Moderate", "High"):
        st.warning(t("offshore_elevated_alert", lang))
    else:
        st.success(t("offshore_standard_ok", lang))

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

render_virtual_library(st, lang, module="Offshore (Marine)")
