"""Shared Streamlit assessment UI for the five MAKU environment modules."""

from __future__ import annotations

import streamlit as st

from ai_advisor import generate_narrative, get_controls
from data_feeds import (
    DataFeedError,
    fetch_offshore_live,
    fetch_solar_live,
    simulate_crane_telemetry,
    simulate_datacenter_telemetry,
    simulate_tunnel_telemetry,
)
from i18n import t
from risk_engine import (
    calculate_datacenter_kinetic_risk,
    calculate_high_rise_kinetic_risk,
    calculate_marine_humidex_risk,
    calculate_solar_albedo_heat_risk,
    calculate_underground_kinetic_risk,
)
from ui_helpers import (
    render_data_mode_selector,
    render_feed_error_banner,
    render_feed_ok_banner,
    render_stream_arm_toggle,
    render_stream_not_armed_note,
)

MODULES = {
    "solar": {"key": "solar", "header": "solar_header", "caption": "solar_caption", "title": "Solar (Desert)"},
    "offshore": {"key": "offshore", "header": "offshore_header", "caption": "offshore_caption", "title": "Offshore (Marine)"},
    "underground": {"key": "underground", "header": "underground_header", "caption": "underground_caption", "title": "Underground (Tunnel/Metro)"},
    "highrise": {"key": "highrise", "header": "highrise_header", "caption": "highrise_caption", "title": "High-Rise (Vertical Urban)"},
    "datacenter": {"key": "datacenter", "header": "datacenter_header", "caption": "datacenter_caption", "title": "Data Center (Controlled Critical Environment)"},
}


def _manual_inputs(module: str, lang: str) -> dict:
    if module == "solar":
        return {
            "ambient_temp": st.slider(t("solar_temp_label", lang), -10.0, 60.0, 32.0),
            "ghi": st.slider(t("solar_ghi_label", lang), 0.0, 1400.0, 800.0),
            "uv_index": st.slider(t("solar_uv_label", lang), 0.0, 15.0, 7.0),
            "surface_type": st.selectbox(t("solar_surface_label", lang), ["pure_desert_sand", "silicon_pv_panels", "hybrid_assembly_zone"], format_func=lambda value: t(f"surf_{value}", lang)),
        }
    if module == "offshore":
        return {
            "ambient_temp": st.slider(t("offshore_temp_label", lang), -10.0, 55.0, 30.0),
            "relative_humidity": st.slider(t("offshore_rh_label", lang), 0.0, 100.0, 70.0),
            "wind_speed": st.slider(t("offshore_wind_label", lang), 0.0, 60.0, 12.0),
        }
    if module == "underground":
        return {
            "ambient_temp": st.slider(t("underground_ambient_temp_label", lang), 0.0, 50.0, 30.0),
            "geothermal_humidity": st.slider(t("underground_geo_humidity_label", lang), 0.0, 100.0, 80.0),
            "particulate_matter_pm25": st.slider(t("underground_pm25_label", lang), 0.0, 400.0, 60.0),
            "gas_co_ppm": st.slider(t("underground_co_label", lang), 0.0, 60.0, 12.0),
        }
    if module == "highrise":
        return {
            "ground_wind_speed_knots": st.slider(t("highrise_ground_wind_label", lang), 0.0, 60.0, 15.0),
            "floor_level": st.slider(t("highrise_floor_level_label", lang), 1, 200, 30),
            "crane_load_mass_tons": st.slider(t("highrise_crane_load_label", lang), 0.5, 30.0, 4.0),
        }
    return {
        "electrical_load_kw": st.slider(t("datacenter_load_label", lang), 0.0, 2000.0, 400.0),
        "hot_aisle_temp": st.slider(t("datacenter_hot_aisle_label", lang), 10.0, 60.0, 34.0),
        "ceiling_void_confined": st.checkbox(t("datacenter_confined_label", lang)),
        "gas_system_armed": st.checkbox(t("datacenter_gas_armed_label", lang)),
    }


def _telemetry(module: str, lang: str, mode: str) -> dict | None:
    armed = render_stream_arm_toggle(st, lang, module, t(f"{module}_telemetry_toggle_label", lang))
    if mode != "auto" or not armed:
        if mode == "auto":
            render_stream_not_armed_note(st, lang)
        return None
    try:
        if module == "solar":
            data = fetch_solar_live()
        elif module == "offshore":
            data = fetch_offshore_live()
        elif module == "underground":
            data = simulate_tunnel_telemetry()
        elif module == "highrise":
            data = simulate_crane_telemetry(st.session_state.get(f"{module}_floor_level", 30))
        else:
            data = simulate_datacenter_telemetry()
        render_feed_ok_banner(st, lang, data["source"], data["fetched_at"])
        return data
    except DataFeedError as exc:
        render_feed_error_banner(st, lang, str(exc))
        return None


def _assessment(module: str, inputs: dict) -> dict:
    if module == "solar":
        return calculate_solar_albedo_heat_risk(**inputs)
    if module == "offshore":
        return calculate_marine_humidex_risk(**inputs)
    if module == "underground":
        return calculate_underground_kinetic_risk(**inputs)
    if module == "highrise":
        return calculate_high_rise_kinetic_risk(**inputs)
    return calculate_datacenter_kinetic_risk(**inputs)


def _merge_telemetry(module: str, data: dict) -> dict:
    mappings = {
        "solar": {"temperature_2m": "ambient_temp", "shortwave_radiation": "ghi"},
        "offshore": {"temperature_2m": "ambient_temp", "relative_humidity_2m": "relative_humidity", "wind_speed_10m_kn": "wind_speed"},
        "underground": {"pm25": "particulate_matter_pm25"},
        "highrise": {},
        "datacenter": {},
    }
    result = dict(data)
    for source, target in mappings[module].items():
        if source in data:
            result[target] = data[source]
    return result


def render_module_page(module: str) -> None:
    config = MODULES[module]
    lang = st.session_state.get("lang", "fr")
    st.title(t(config["header"], lang))
    st.caption(t(config["caption"], lang))

    mode = render_data_mode_selector(st, lang, module)
    telemetry = _telemetry(module, lang, mode)
    inputs = _manual_inputs(module, lang)
    if telemetry:
        inputs = _merge_telemetry(module, telemetry)
        st.subheader(t(f"{module}_realtime_header", lang))
    else:
        st.subheader(t(f"{module}_env_data_header", lang))

    result = _assessment(module, inputs)
    controls = get_controls(result)
    left, middle, right = st.columns(3)
    left.metric(t("risk_band_label", lang), result["risk_band"])
    middle.metric(t("primary_hazard_label", lang), result["primary_hazard"].split(" - ")[0])
    right.metric(t("safety_override", lang), t("yes", lang) if result["safety_override"] else t("no", lang))
    if result["safety_override"]:
        st.error(t(f"{module}_critical_alert", lang))
    else:
        st.success(t(f"{module}_standard_ok", lang))

    st.subheader(t("drivers_label", lang))
    st.json(result["drivers"])
    st.subheader(t("controls_label", lang))
    for control in controls:
        st.markdown(f"- {control}")

    api_key = st.sidebar.text_input(t("api_key_label", lang), type="password", help=t("api_key_help", lang))
    st.subheader(t("briefing_label", lang))
    st.write(generate_narrative(result, controls, api_key=api_key, lang=lang))
