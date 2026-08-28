"""
MAKU - Multi-Environment AI for Kinetic Risk Assessment
Main entry point / router - SINGLE-FILE EDITION.

Authentication gate (auth.require_login()) runs first, before anything
else in this file - no module layout, sidebar navigation, or dashboard
content is defined or executed for an unauthenticated visitor. See auth.py
for credential handling.

WHY THIS FILE IS SELF-CONTAINED (no pages/ directory):
Streamlit's st.navigation()/st.Page() API supports two kinds of pages:
a path to a .py file, or a plain Python function. This file uses the
function form exclusively - render_dashboard(), render_solar_farms(),
render_offshore_oil_gas(), render_metros_tunnels(), render_high_rise(),
and render_data_centers() are all defined below and passed directly to
st.Page(). There is no pages/ folder anywhere, and nothing here depends on
GitHub preserving a subdirectory structure on upload - every file this
app needs (app.py, auth.py, i18n.py, risk_engine.py, ai_advisor.py,
analytics.py, data_feeds.py, ui_helpers.py, regulatory_references.py)
lives flat at the repo root, which is the least error-prone layout to
upload via the GitHub web UI.

Exactly like the previous multi-file version, each page function is its
own independent "script run" under st.navigation - Streamlit reruns this
entire app.py top-to-bottom on every navigation event, then pg.run()
executes only the selected page function. That means every page function
below still calls st.set_page_config() as its own first Streamlit command,
exactly as the old separate page files did.

All risk math still lives in risk_engine.py (never here) - this file only
orchestrates: it collects inputs, calls into risk_engine/ai_advisor/
analytics/data_feeds/ui_helpers, and renders results.
"""

from __future__ import annotations

import math
import os

import pandas as pd
import streamlit as st

from auth import require_login, render_logout_control
from i18n import t, language_selector
from risk_engine import (
    calculate_solar_albedo_heat_risk,
    calculate_marine_humidex_risk,
    calculate_underground_kinetic_risk,
    calculate_high_rise_kinetic_risk,
    calculate_datacenter_kinetic_risk,
    wbgt_outdoor_approx,
    acgih_action_level,
    CRANE_SUSPEND_WIND_KNOTS,
    DATACENTER_ARC_FLASH_DANGER_CAL,
)
from ai_advisor import get_controls, generate_narrative
from ui_helpers import (
    render_official_report,
    render_analytics_section,
    render_data_mode_selector,
    render_stream_arm_toggle,
    render_stream_not_armed_note,
    render_feed_ok_banner,
    render_feed_error_banner,
    render_virtual_library,
    render_web_search_toggle,
    render_meteorology_forecast,
)
from analytics import log_assessment
from data_feeds import (
    fetch_solar_live,
    fetch_solar_forecast,
    fetch_offshore_live,
    fetch_offshore_forecast,
    simulate_tunnel_telemetry,
    simulate_crane_telemetry,
    simulate_datacenter_telemetry,
    DataFeedError,
)

try:
    from streamlit_js_eval import get_geolocation
    GEOLOCATION_AVAILABLE = True
except ImportError:
    # Should not happen once streamlit-js-eval is in requirements.txt, but
    # the Field Inspection section degrades to a clear "unavailable" note
    # rather than crashing the whole dashboard if the package is ever
    # missing from the deployed environment.
    GEOLOCATION_AVAILABLE = False

LOGO_MODERNE_PATH = "logo_moderne.png"
LOGO_CROQUIS_PATH = "logo_croquis.png"

# ---------------------------------------------------------------------------
# Illustrative reference coordinates for the Field Inspection / geolocation
# feature below. These are NOT real facility locations - MAKU's five
# modules are simulated/MVP demonstrations (see data_feeds.py's module
# docstring), so there is no real GPS-trackable "Solar Farm" or "Data
# Center" to point at. These coordinates exist purely so the "closest
# simulated site" distance calculation has something concrete to measure
# against, spread around the UAE to match the app's existing regulatory
# framing (Dubai Municipality, ADOSH-SF). Solar and Offshore reuse the
# exact coordinates data_feeds.py already uses for its live weather API
# calls, so those two are at least self-consistent with the live data
# shown elsewhere in the app.
# ---------------------------------------------------------------------------
SITE_COORDINATES = {
    "Solar (Desert)": {"lat": 24.4539, "lon": 54.3773, "nav_key": "nav_solar"},
    "Offshore (Marine)": {"lat": 25.5000, "lon": 53.5000, "nav_key": "nav_offshore"},
    "Underground (Tunnel/Metro)": {"lat": 25.2048, "lon": 55.2708, "nav_key": "nav_metros"},
    "High-Rise (Vertical Urban)": {"lat": 25.1972, "lon": 55.2744, "nav_key": "nav_highrise"},
    "Data Center (Controlled Critical Environment)": {"lat": 25.1216, "lon": 55.3773, "nav_key": "nav_datacenter"},
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points in kilometers.
    Pure-math orchestration helper for the Field Inspection section only -
    not a risk formula, so it stays out of risk_engine.py (Mathematical
    Isolation rule: this never feeds into or overrides a module's risk
    calculation, it only helps a user pick which module to open)."""
    r_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * r_km * math.asin(math.sqrt(a))


def _closest_site(lat: float, lon: float) -> tuple[str, float]:
    """Returns (module_name, distance_km) for the closest illustrative
    SITE_COORDINATES entry to the given position."""
    best_module, best_km = None, float("inf")
    for module, coords in SITE_COORDINATES.items():
        km = _haversine_km(lat, lon, coords["lat"], coords["lon"])
        if km < best_km:
            best_module, best_km = module, km
    return best_module, best_km


# ---------------------------------------------------------------------------
# Authentication gate - must be the first Streamlit-affecting call in this
# script. Every navigation event re-executes app.py from the top (that's
# how st.navigation/pg.run() dispatch works), so this check applies
# uniformly to the dashboard AND to all 5 module pages: there is no way to
# reach a module page without first passing this gate.
# ---------------------------------------------------------------------------
require_login()


# ===========================================================================
# Shared helpers (formerly page_common.py) - inlined here so this whole app
# lives in one file with zero extra modules of its own.
# ===========================================================================

def _render_ai_layer_sidebar(lang: str) -> str:
    """The Anthropic API key box, shared verbatim across every page (same
    session_state key 'api_key' so the value entered on one page is still
    there after navigating to another)."""
    st.sidebar.subheader(t("ai_layer_header", lang))
    return st.sidebar.text_input(
        t("api_key_label", lang),
        type="password",
        help=t("api_key_help", lang),
        key="api_key",
    )


def _render_acgih_reference_panel(lang: str, ambient_temp: float, relative_humidity: float) -> None:
    """Optional ACGIH TLV work/rest reference cross-check, shown alongside
    (never instead of) a module's own risk band. Uses the WBGT
    approximation already defined in risk_engine.py - never computes a new
    formula of its own, and never feeds into any module's risk_band."""
    with st.expander("ACGIH TLV" + (" - Référence" if lang == "fr" else " - Reference Check")):
        col1, col2 = st.columns(2)
        with col1:
            work_rate = st.selectbox(
                t("work_rate_label", lang),
                options=["light", "moderate", "heavy"],
                format_func=lambda v: t(f"wr_{v}", lang),
                index=1,
                key="acgih_work_rate",
            )
        with col2:
            work_rest = st.selectbox(
                t("work_rest_label", lang),
                options=["100/0", "75/25", "50/50", "25/75"],
                help=t("work_rest_help", lang),
                key="acgih_work_rest",
            )
        wbgt = wbgt_outdoor_approx(ambient_temp, relative_humidity)
        action = acgih_action_level(wbgt, work_rate, work_rest)
        st.metric("WBGT (approx.)", f"{wbgt:.1f} °C")
        exceeded_label = t("acgih_exceeded_label", lang)
        verdict = t("yes", lang) if action["exceeds"] else t("no", lang)
        st.write(
            f"**{exceeded_label}:** {verdict}  \n"
            f"{t('vs_limit', lang)} {action['limit']} °C "
            f"({'+' if action['margin'] >= 0 else ''}{action['margin']} °C)"
        )


def _sidebar_brand(lang: str) -> None:
    """Brand image shown in the sidebar on every module page. The native
    st.navigation sidebar nav (title + icon per page, auto-generated from
    the st.Page() registrations below) already lists every page - no need
    to hand-build a duplicate nav block here."""
    if os.path.exists(LOGO_CROQUIS_PATH):
        st.sidebar.image(LOGO_CROQUIS_PATH, width="stretch")


def render_field_inspection_section(lang: str) -> None:
    """Dashboard section: on-site GPS check via the browser's Geolocation
    API (streamlit_js_eval.get_geolocation), shown on an interactive map,
    with an automatic "closest simulated site" lookup and a one-click
    jump to that module.

    Mathematical Isolation rule still applies here: this section only
    orchestrates (reads a GPS fix, measures distance, picks a page to
    open) - it never computes or overrides any module's risk_band, and
    risk_engine.py has no geolocation awareness at all.

    get_geolocation() wraps a browser Promise, so on the very first call
    after the user clicks the button it returns None while the browser's
    permission prompt/GPS fix is pending; the component then triggers a
    rerun once the promise resolves (success or error), at which point
    this function runs again and receives the real payload. That's why
    the button only needs to flip a session_state flag rather than loop
    or block - Streamlit's own rerun cycle handles the "wait" for us.
    """
    st.subheader(t("field_inspection_header", lang))
    st.caption(t("field_inspection_caption", lang))

    if not GEOLOCATION_AVAILABLE:
        st.info(
            "streamlit-js-eval is not installed - geolocation is unavailable. "
            "Add it to requirements.txt to enable this section."
            if lang != "fr" else
            "streamlit-js-eval n'est pas installé - la géolocalisation est "
            "indisponible. Ajoutez-le à requirements.txt pour activer cette section."
        )
        return

    armed = st.session_state.get("field_gps_armed", False)

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        label = t("field_inspection_refresh_button", lang) if armed else t("field_inspection_button", lang)
        if st.button(label, key="field_gps_button"):
            st.session_state["field_gps_armed"] = True
            # Clear any previous fix so a stale success/error state from a
            # prior click can't linger under the new "loading" phase below.
            st.session_state.pop("field_gps_last_result", None)
            armed = True

    if not armed:
        return

    location = get_geolocation(component_key="maku_field_gps")
    if location is not None:
        # Cache the latest resolved payload (success or error) so it
        # survives the reruns that other widgets on this same dashboard
        # trigger - get_geolocation() itself only returns fresh data
        # right after the browser promise resolves.
        st.session_state["field_gps_last_result"] = location
    else:
        location = st.session_state.get("field_gps_last_result")

    if location is None:
        st.info(t("field_inspection_loading", lang))
        return

    if "error" in location:
        error_code = location["error"].get("code")
        if error_code == 1:
            st.warning(t("field_inspection_denied", lang))
        elif error_code == 2:
            st.warning(t("field_inspection_unavailable", lang))
        elif error_code == 3:
            st.warning(t("field_inspection_timeout", lang))
        else:
            st.warning(f"{t('field_inspection_error_generic', lang)}: {location['error'].get('message', '')}")
        return

    coords = location.get("coords", {})
    lat, lon = coords.get("latitude"), coords.get("longitude")
    if lat is None or lon is None:
        st.warning(t("field_inspection_error_generic", lang))
        return

    closest_module, distance_km = _closest_site(lat, lon)

    col1, col2, col3 = st.columns(3)
    col1.metric(t("field_inspection_your_position", lang), f"{lat:.5f}, {lon:.5f}")
    accuracy = coords.get("accuracy")
    col2.metric(t("field_inspection_accuracy_label", lang), f"±{accuracy:.0f} m" if accuracy else "-")
    col3.metric(t("field_inspection_distance_label", lang), f"{distance_km:.1f} km")

    st.write(f"**{t('field_inspection_closest_site_label', lang)}:** {t(SITE_COORDINATES[closest_module]['nav_key'], lang)}")

    map_rows = [{"lat": lat, "lon": lon, "color": "#d62728", "size": 120, "label": "you"}]
    for module, site in SITE_COORDINATES.items():
        map_rows.append({
            "lat": site["lat"], "lon": site["lon"],
            "color": "#2c5c63" if module == closest_module else "#7fa8ad",
            "size": 80 if module == closest_module else 50,
            "label": module,
        })
    st.map(pd.DataFrame(map_rows), latitude="lat", longitude="lon", color="color", size="size")
    st.caption(t("field_inspection_sites_note", lang))

    if st.button(t("field_inspection_go_to_module_button", lang), key="field_gps_go_to_module"):
        st.switch_page(MODULE_PAGES[closest_module])


# ===========================================================================
# Dashboard / landing page
# ===========================================================================

def render_dashboard():
    """The landing/overview page. Must call st.set_page_config as its own
    first Streamlit command, exactly like every other page - with
    st.navigation, each page (function or file) is its own script run."""
    st.set_page_config(page_title="MAKU - Kinetic Risk Platform", page_icon="🛡️", layout="wide")

    if os.path.exists(LOGO_CROQUIS_PATH):
        st.sidebar.image(LOGO_CROQUIS_PATH, width="stretch", caption="The Five Worlds of MAKU")

    lang = language_selector(st)

    st.sidebar.title(t("app_title", lang))
    st.sidebar.caption(t("app_tagline", lang))
    st.sidebar.markdown("---")
    render_logout_control(st)
    st.sidebar.markdown("---")

    if os.path.exists(LOGO_MODERNE_PATH):
        st.image(LOGO_MODERNE_PATH, width="stretch")

    st.title(t("app_title", lang))
    st.caption(t("app_tagline", lang))

    st.header(t("dashboard_intro_header", lang))
    st.write(t("dashboard_intro_body", lang))

    st.subheader(t("dashboard_module_col_header", lang))

    st.markdown("---")
    render_field_inspection_section(lang)

    st.sidebar.markdown("---")
    st.sidebar.caption(t("dashboard_footer", lang))
    render_official_report(
        st,
        result=st.session_state.get("latest_risk_result", {}),
        narrative=st.session_state.get("latest_ai_narrative", ""),
        controls=st.session_state.get("latest_controls", []),
        lang=lang,
    )

    st.markdown("---")
    render_analytics_section(st, lang)


# ===========================================================================
# Module 1: Solar Farms (Desert)
# ===========================================================================

_SOLAR_SURFACE_OPTIONS = ["pure_desert_sand", "silicon_pv_panels", "hybrid_assembly_zone"]


def render_solar_farms():
    """UI for calculate_solar_albedo_heat_risk(). All risk math stays in
    risk_engine.py (Mathematical Isolation rule) - this function only
    collects inputs (manual sliders or the live Open-Meteo feed), calls
    the engine, and renders the result."""
    st.set_page_config(page_title="MAKU - Solar Farms", page_icon="☀️", layout="wide")

    lang = language_selector(st)
    _sidebar_brand(lang)
    render_logout_control(st)
    api_key = _render_ai_layer_sidebar(lang)
    enable_web_search = render_web_search_toggle(st, lang, "solar")

    st.title(t("solar_header", lang))
    st.caption(t("solar_caption", lang))

    data_mode = render_data_mode_selector(st, lang, "solar")

    ambient_temp = uv_index = ghi = None
    surface_type = _SOLAR_SURFACE_OPTIONS[0]

    if data_mode == "auto":
        try:
            live = fetch_solar_live()
            render_feed_ok_banner(st, lang, live["source"], live["fetched_at"])
            ambient_temp = live["temperature_2m"]
            uv_index = live["uv_index"]
            ghi = live["shortwave_radiation"]

            st.subheader(t("solar_realtime_header", lang))
            col1, col2, col3 = st.columns(3)
            col1.metric(t("solar_temp_label", lang), f"{ambient_temp} °C")
            col2.metric(t("solar_uv_label", lang), uv_index)
            col3.metric(t("solar_ghi_label", lang), f"{ghi} W/m²")

            surface_type = st.selectbox(
                t("solar_surface_label", lang),
                options=_SOLAR_SURFACE_OPTIONS,
                format_func=lambda v: t(f"surf_{v}", lang),
                key="solar_surface_auto",
            )
        except DataFeedError as exc:
            render_feed_error_banner(st, lang, str(exc))
            data_mode = "manual"

    if data_mode == "manual":
        st.subheader(t("solar_env_data_header", lang))
        col1, col2, col3 = st.columns(3)
        with col1:
            ambient_temp = st.slider(t("solar_temp_label", lang), 15.0, 55.0, 32.0, 0.5)
        with col2:
            ghi = st.slider(t("solar_ghi_label", lang), 0.0, 1200.0, 650.0, 10.0)
        with col3:
            uv_index = st.slider(t("solar_uv_label", lang), 0.0, 14.0, 7.0, 0.5)
        surface_type = st.selectbox(
            t("solar_surface_label", lang),
            options=_SOLAR_SURFACE_OPTIONS,
            format_func=lambda v: t(f"surf_{v}", lang),
            key="solar_surface_manual",
        )

    _render_acgih_reference_panel(lang, ambient_temp, relative_humidity=30.0)

    with st.expander("📡 " + ("Prévision météo 7 jours" if lang == "fr" else "7-Day Meteorology Forecast")):
        try:
            forecast = fetch_solar_forecast()
            render_meteorology_forecast(
                st, lang, forecast,
                fields=[
                    ("temperature_2m_max", t("solar_temp_label", lang)),
                    ("uv_index_max", t("solar_uv_label", lang)),
                ],
            )
        except DataFeedError as exc:
            st.info(str(exc))

    st.markdown("---")

    if st.button(t("run_button", lang), type="primary", width="stretch"):
        result = calculate_solar_albedo_heat_risk(
            ghi=ghi, uv_index=uv_index, ambient_temp=ambient_temp, surface_type=surface_type
        )
        controls = get_controls(result)
        narrative = generate_narrative(
            result, controls, api_key=api_key, lang=lang, enable_web_search=enable_web_search
        )

        log_assessment(st, result)
        st.session_state["latest_risk_result"] = result
        st.session_state["latest_ai_narrative"] = narrative
        st.session_state["latest_controls"] = controls

    if st.session_state.get("latest_risk_result", {}).get("module") == "Solar (Desert)":
        result = st.session_state["latest_risk_result"]
        narrative = st.session_state["latest_ai_narrative"]
        controls = st.session_state["latest_controls"]

        if result["risk_level"] == "CRITICAL":
            st.error(t("solar_critical_alert", lang))
        elif result["risk_level"] == "HIGH":
            st.warning(t("solar_high_alert", lang))
        else:
            st.success(t("solar_standard_ok", lang))

        if result["safety_override"]:
            st.error(t("safety_override", lang))

        col1, col2, col3 = st.columns(3)
        col1.metric(t("perceived_temp_label", lang), f"{result['perceived_temp']} °C")
        col2.metric(t("risk_level_label", lang), result["risk_level"])
        col3.metric(t("shift_rotation_label", lang), result["max_shift_duration"])

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
    render_virtual_library(st, lang, module="Solar (Desert)")


# ===========================================================================
# Module 2: Offshore Oil & Gas (Marine)
# ===========================================================================

_WIND_STATUS_KEY = {
    "Normal Operations": "wind_status_normal",
    "Restricted - Monitor Closely": "wind_status_restricted",
    "Suspended - Crane/Lifting Danger": "wind_status_suspended",
}


def render_offshore_oil_gas():
    """UI for calculate_marine_humidex_risk(). Wave height / ocean current
    are shown as context-only readouts since the current risk_engine
    formula doesn't consume them."""
    st.set_page_config(page_title="MAKU - Offshore Oil & Gas", page_icon="🌊", layout="wide")

    lang = language_selector(st)
    _sidebar_brand(lang)
    render_logout_control(st)
    api_key = _render_ai_layer_sidebar(lang)
    enable_web_search = render_web_search_toggle(st, lang, "offshore")

    st.title(t("offshore_header", lang))
    st.caption(t("offshore_caption", lang))

    data_mode = render_data_mode_selector(st, lang, "offshore")

    ambient_temp = relative_humidity = wind_speed = None

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

    _render_acgih_reference_panel(lang, ambient_temp, relative_humidity)

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
        narrative = generate_narrative(
            result, controls, api_key=api_key, lang=lang, enable_web_search=enable_web_search
        )

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
            t(_WIND_STATUS_KEY.get(result["wind_risk_status"], "wind_status_normal"), lang),
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


# ===========================================================================
# Module 3: Metros & Tunnels (Underground)
# ===========================================================================

def render_metros_tunnels():
    """UI for calculate_underground_kinetic_risk(). No free/keyless public
    API exists for underground gas/dust/heat sensors, so "Automatique"
    mode arms a bounded random-walk simulator that mimics a live LoRaWAN
    sensor-hub stream - clearly labeled as simulated, never presented as
    real data."""
    st.set_page_config(page_title="MAKU - Metros & Tunnels", page_icon="🚇", layout="wide")

    lang = language_selector(st)
    _sidebar_brand(lang)
    render_logout_control(st)
    api_key = _render_ai_layer_sidebar(lang)
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

    _render_acgih_reference_panel(lang, ambient_temp, geothermal_humidity)

    st.markdown("---")

    if st.button(t("run_button", lang), type="primary", width="stretch"):
        result = calculate_underground_kinetic_risk(
            ambient_temp=ambient_temp,
            geothermal_humidity=geothermal_humidity,
            particulate_matter_pm25=pm25,
            gas_co_ppm=gas_co_ppm,
        )
        controls = get_controls(result)
        narrative = generate_narrative(
            result, controls, api_key=api_key, lang=lang, enable_web_search=enable_web_search
        )

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


# ===========================================================================
# Module 4: High-Rise (Vertical Urban)
# ===========================================================================

def render_high_rise():
    """UI for calculate_high_rise_kinetic_risk(). No free/keyless public
    API reports crane-mounted anemometer/oscillation telemetry, so
    "Automatique" mode arms a bounded random-walk simulator clearly
    labeled as simulated."""
    st.set_page_config(page_title="MAKU - High-Rise", page_icon="🏙️", layout="wide")

    lang = language_selector(st)
    _sidebar_brand(lang)
    render_logout_control(st)
    api_key = _render_ai_layer_sidebar(lang)
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
        narrative = generate_narrative(
            result, controls, api_key=api_key, lang=lang, enable_web_search=enable_web_search
        )

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


# ===========================================================================
# Module 5: Data Centers (Controlled Critical Environment)
# ===========================================================================

def render_data_centers():
    """UI for calculate_datacenter_kinetic_risk(). No free/keyless public
    API reports rack-level current-transformer/thermal-probe telemetry, so
    "Automatique" mode arms a bounded random-walk simulator clearly
    labeled as simulated. Confined-space and gas-suppression-armed state
    are site/operational facts, not sensor readings, so they're always
    manual checkboxes even in auto mode."""
    st.set_page_config(page_title="MAKU - Data Centers", page_icon="🖥️", layout="wide")

    lang = language_selector(st)
    _sidebar_brand(lang)
    render_logout_control(st)
    api_key = _render_ai_layer_sidebar(lang)
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
        narrative = generate_narrative(
            result, controls, api_key=api_key, lang=lang, enable_web_search=enable_web_search
        )

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


# ===========================================================================
# Navigation - all six pages are FUNCTIONS, not file paths. No pages/
# directory is read or required anywhere in this app.
#
# Page objects are built as named variables (not inline in the list below)
# so the Field Inspection section in render_dashboard() can also use them
# as st.switch_page() targets - st.switch_page() accepts the actual Page
# object returned by st.Page(), not just a file path.
# ===========================================================================

page_dashboard = st.Page(render_dashboard, title="Dashboard", icon="🛡️", default=True)
page_solar = st.Page(render_solar_farms, title="Solar Farms", icon="☀️")
page_offshore = st.Page(render_offshore_oil_gas, title="Offshore Oil & Gas", icon="🌊")
page_underground = st.Page(render_metros_tunnels, title="Metros & Tunnels", icon="🚇")
page_highrise = st.Page(render_high_rise, title="High Rise", icon="🏗️")
page_datacenter = st.Page(render_data_centers, title="Data Centers", icon="🏢")

# Maps each SITE_COORDINATES module name to its Page object, so the closest-
# site lookup in render_field_inspection_section() can route straight there.
MODULE_PAGES = {
    "Solar (Desert)": page_solar,
    "Offshore (Marine)": page_offshore,
    "Underground (Tunnel/Metro)": page_underground,
    "High-Rise (Vertical Urban)": page_highrise,
    "Data Center (Controlled Critical Environment)": page_datacenter,
}

pg = st.navigation([
    page_dashboard, page_solar, page_offshore, page_underground, page_highrise, page_datacenter,
])
pg.run()
