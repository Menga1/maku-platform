pages/1_Solar_Farms."""
MAKU - Solar (Desert) page
UI only. All calculations come from risk_engine.calculate_solar_albedo_heat_risk
(Mathematical Isolation rule - no formulas live in this file).

Supports two data modes, switchable per-page from the sidebar:
  - Manuel / Simulation : sliders, as before
  - Automatique / Temps Réel : live Open-Meteo forecast API
    (temperature_2m, uv_index, shortwave_radiation) for the desert site
    coordinates. Any network/API error falls back safely to manual sliders.
"""

import streamlit as st
from risk_engine import calculate_solar_albedo_heat_risk
from ai_advisor import get_controls, generate_narrative
from i18n import t, language_selector
from analytics import log_assessment
from data_feeds import fetch_solar_live, fetch_solar_forecast, DataFeedError, SOLAR_COORDS
from ui_helpers import render_data_mode_selector, render_feed_ok_banner, render_feed_error_banner, render_official_report, render_web_search_toggle, render_virtual_library, render_meteorology_forecast

st.set_page_config(page_title="MAKU - Solar (Desert)", page_icon="☀️", layout="wide")

lang = language_selector(st)

st.sidebar.title(t("app_title", lang))
st.sidebar.caption(t("app_tagline", lang))
st.sidebar.markdown("---")

data_mode = render_data_mode_selector(st, lang, module_key="solar")

st.sidebar.subheader(t("ai_layer_header", lang))
api_key = st.sidebar.text_input(
    t("api_key_label", lang), type="password", help=t("api_key_help", lang),
)
enable_web_search = render_web_search_toggle(st, lang, module_key="solar")

st.title(t("solar_header", lang))
st.caption(t("solar_caption", lang))

with st.expander("📈 " + ("Prévisions Météo (7 jours)" if lang == "fr" else "7-Day Meteorology Forecast")):
    try:
        forecast = fetch_solar_forecast(SOLAR_COORDS["lat"], SOLAR_COORDS["lon"])
        render_meteorology_forecast(
            st, lang, forecast,
            fields=[
                ("temperature_2m_max", "Temp max (°C)"),
                ("uv_index_max", "UV max"),
                ("shortwave_radiation_sum", "GHI cumulé (MJ/m²)" if lang == "fr" else "GHI sum (MJ/m²)"),
            ],
        )
    except DataFeedError as exc:
        st.warning(("Prévisions indisponibles: " if lang == "fr" else "Forecast unavailable: ") + str(exc))

col_inputs, col_results = st.columns([1, 2])

SURFACE_TYPES = ["pure_desert_sand", "silicon_pv_panels", "hybrid_assembly_zone"]

live_data = None
live_error = None
effective_mode = data_mode

if data_mode == "auto":
    try:
        live_data = fetch_solar_live(SOLAR_COORDS["lat"], SOLAR_COORDS["lon"])
    except DataFeedError as exc:
        live_error = str(exc)
        effective_mode = "manual"

with col_inputs:
    st.header(t("solar_env_data_header", lang))

    if effective_mode == "auto":
        render_feed_ok_banner(st, lang, live_data["source"], live_data["fetched_at"])
        temp = st.slider(
            t("solar_temp_label", lang), 20.0, 55.0,
            float(min(55.0, max(20.0, live_data["temperature_2m"]))), disabled=True,
        )
        ghi = st.number_input(
            t("solar_ghi_label", lang), 0, 1200,
            int(min(1200, max(0, live_data["shortwave_radiation"]))), disabled=True,
        )
        uv = st.slider(
            t("solar_uv_label", lang), 0, 15,
            int(min(15, max(0, round(live_data["uv_index"])))), disabled=True,
        )
    else:
        if live_error:
            render_feed_error_banner(st, lang, live_error)
        temp = st.slider(t("solar_temp_label", lang), 20.0, 55.0, 38.0)
        ghi = st.number_input(t("solar_ghi_label", lang), 0, 1200, 850)
        uv = st.slider(t("solar_uv_label", lang), 0, 15, 9)

    surface = st.selectbox(
        t("solar_surface_label", lang),
        SURFACE_TYPES,
        format_func=lambda v: t(f"surf_{v}", lang),
    )

# Live calculation via the MAKU risk engine (Mathematical Isolation - no math here)
result = calculate_solar_albedo_heat_risk(ghi, uv, temp, surface)
controls = get_controls(result)

with col_results:
    st.header(t("solar_realtime_header", lang))

    c1, c2, c3 = st.columns(3)
    c1.metric(
        t("perceived_temp_label", lang),
        f"{result['perceived_temp']} °C",
        f"+{result['thermal_amplification']}°C {t('albedo_delta_label', lang)}",
    )
    c2.metric(t("risk_level_label", lang), result["risk_level"])
    c3.metric(t("shift_rotation_label", lang), result["max_shift_duration"])

    if result["risk_level"] == "CRITICAL":
        st.error(f"{t('solar_critical_alert', lang)} {result['max_shift_duration']}.")
    elif result["risk_level"] == "HIGH":
        st.warning(f"{t('solar_high_alert', lang)} {result['max_shift_duration']}.")
    else:
        st.success(t("solar_standard_ok", lang))

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

render_virtual_library(st, lang, module="Solar (Desert)")
