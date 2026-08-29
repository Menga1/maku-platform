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

import io
import math
import os

import pandas as pd
import streamlit as st

from auth import require_login, render_logout_control
from i18n import t, language_selector, LANGUAGES
from risk_engine import (
    calculate_solar_albedo_heat_risk,
    calculate_marine_humidex_risk,
    calculate_underground_kinetic_risk,
    calculate_high_rise_kinetic_risk,
    calculate_datacenter_kinetic_risk,
    calculate_wind_energy_kinetic_risk,
    calculate_mining_quarrying_kinetic_risk,
    calculate_marine_port_kinetic_risk,
    wbgt_outdoor_approx,
    CRANE_SUSPEND_WIND_KNOTS,
    DATACENTER_ARC_FLASH_DANGER_CAL,
    humidex,
    classify_humidex,
    wind_chill_c,
    classify_wind_chill,
    classify_uv_index,
    classify_bushfire_smoke_pm25,
)
from ai_advisor import (
    get_controls, generate_narrative, translate_narrative,
    generate_daily_briefing, predict_forecast_breach, generate_predictive_alert,
)
from regulatory_country_thresholds import (
    get_country_thresholds, is_midday_outdoor_ban_active, COUNTRY_LABELS, resolve_heat_stress_limit,
    get_uv_heat_config, get_bushfire_smoke_bands,
    is_remote_comms_required, get_remote_comms_config,
)
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
    fetch_live_weather_universal,
    fetch_air_quality_live,
    reverse_geocode_country,
    SOLAR_COORDS,
    WIND_ENERGY_COORDS,
    MINING_COORDS,
    MARINE_PORT_COORDS,
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

try:
    from gtts import gTTS
    TTS_LIBRARY_AVAILABLE = True
except ImportError:
    TTS_LIBRARY_AVAILABLE = False

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
    "Wind Energy (Onshore/Offshore)": {"lat": WIND_ENERGY_COORDS["lat"], "lon": WIND_ENERGY_COORDS["lon"], "nav_key": "nav_windenergy"},
    "Mining & Quarrying": {"lat": MINING_COORDS["lat"], "lon": MINING_COORDS["lon"], "nav_key": "nav_mining"},
    "Marine & Port Construction": {"lat": MARINE_PORT_COORDS["lat"], "lon": MARINE_PORT_COORDS["lon"], "nav_key": "nav_marineport"},
}

# Geofence radius (km) around each illustrative site. Purely an
# orchestration/UI concern - crossing this radius changes the dashboard's
# visual state (Module 3's "high-visibility hazard layout" requirement) but
# never feeds into or overrides any module's actual risk_band calculation.
GEOFENCE_RADIUS_KM = 5.0


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


def is_inside_geofence(lat: float, lon: float, radius_km: float = GEOFENCE_RADIUS_KM) -> tuple[bool, str | None, float]:
    """Module 3 geofencing: returns (inside_any_zone, module_name_or_None,
    distance_km_to_that_zone). Reuses the same haversine helper and
    SITE_COORDINATES already used for closest-site routing - a geofence is
    just "closest site, and is that distance under the radius"."""
    module, distance_km = _closest_site(lat, lon)
    return distance_km <= radius_km, (module if distance_km <= radius_km else None), distance_km


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


def render_workload_selector(lang: str) -> str:
    """Global sidebar Workload Intensity selector (light/moderate/heavy),
    session-state-backed so it persists across page navigation exactly
    like the language and country selectors. Feeds directly into the
    ACGIH/ISO7243 heat-stress reference panel below via regulatory_
    country_thresholds.resolve_heat_stress_limit()."""
    if "workload_intensity" not in st.session_state:
        st.session_state["workload_intensity"] = "moderate"
    options = ["light", "moderate", "heavy"]
    chosen = st.sidebar.selectbox(
        t("work_rate_label", lang),
        options=options,
        index=options.index(st.session_state["workload_intensity"]),
        format_func=lambda v: t(f"wr_{v}", lang),
        key="workload_intensity_widget",
    )
    st.session_state["workload_intensity"] = chosen
    return chosen


def _render_acgih_reference_panel(lang: str, ambient_temp: float, relative_humidity: float,
                                   regulatory_profile: dict, work_rate: str,
                                   wind_speed_kmh: float | None = None) -> None:
    """Heat-stress reference cross-check, shown alongside (never instead
    of) a module's own risk band. Uses the WBGT approximation already
    defined in risk_engine.py - never computes a new formula of its own,
    and never feeds into any module's risk_band.

    Country-aware since the global regulatory-profile refactor: USA/UAE/
    UK/Australia profiles use the ACGIH work/rest-indexed table, France
    uses the ISO 7243 continuous-exposure reference value, and Canada
    switches entirely to Environment Canada's Humidex method (with its
    45.0 critical safety cutoff) - resolve_heat_stress_limit() picks the
    right method automatically and this panel labels which one is active,
    directly answering 'which regulation applies here'.

    When the active profile also defines a cold_stress section (currently
    Canada only) and the caller supplies a wind speed reading, this panel
    additionally renders an Environment Canada Wind Chill sub-panel -
    still a pure display of risk_engine.wind_chill_c()/classify_wind_chill(),
    never feeding back into the module's own risk_band."""
    heat_method = regulatory_profile["heat_stress"]["method"]
    panel_title = f"{heat_method} ({regulatory_profile['label']})"
    with st.expander(panel_title):
        if heat_method == "HUMIDEX":
            hmdx = round(humidex(ambient_temp, relative_humidity), 1)
            st.metric(t("humidex_label", lang), f"{hmdx} °C")
            st.write(f"**{classify_humidex(hmdx)}**")

            action = resolve_heat_stress_limit(regulatory_profile, work_rate)
            exceeded_label = t("acgih_exceeded_label", lang)
            exceeds = hmdx >= action["limit"]
            verdict = t("yes", lang) if exceeds else t("no", lang)
            margin = round(hmdx - action["limit"], 1)
            st.write(
                f"**{exceeded_label}:** {verdict}  \n"
                f"{t('vs_limit', lang)} {action['limit']} °C "
                f"({'+' if margin >= 0 else ''}{margin} °C)"
            )
            st.caption(action["source_note"])
        else:
            wbgt = wbgt_outdoor_approx(ambient_temp, relative_humidity)
            st.metric("WBGT (approx.)", f"{wbgt:.1f} °C")

            if heat_method == "ACGIH":
                work_rest = st.selectbox(
                    t("work_rest_label", lang),
                    options=["100/0", "75/25", "50/50", "25/75"],
                    help=t("work_rest_help", lang),
                    key="acgih_work_rest",
                )
            else:
                work_rest = "100/0"  # ISO 7243 has no work/rest axis - resolve_heat_stress_limit() ignores this

            action = resolve_heat_stress_limit(regulatory_profile, work_rate, work_rest)
            exceeded_label = t("acgih_exceeded_label", lang)
            exceeds = wbgt > action["limit"]
            verdict = t("yes", lang) if exceeds else t("no", lang)
            margin = round(wbgt - action["limit"], 1)
            st.write(
                f"**{exceeded_label}:** {verdict}  \n"
                f"{t('vs_limit', lang)} {action['limit']} °C "
                f"({'+' if margin >= 0 else ''}{margin} °C)"
            )
            st.caption(action["source_note"])

        cold_cfg = regulatory_profile.get("cold_stress")
        if cold_cfg and wind_speed_kmh is not None:
            st.markdown("---")
            st.subheader(t("windchill_label", lang))
            wc = wind_chill_c(ambient_temp, wind_speed_kmh)
            st.metric(t("windchill_label", lang), f"{wc} °C")
            st.write(f"**{classify_wind_chill(wc)}**")
            st.caption(cold_cfg["source_note"])


def _sidebar_brand(lang: str) -> None:
    """Brand image shown in the sidebar on every module page. The native
    st.navigation sidebar nav (title + icon per page, auto-generated from
    the st.Page() registrations below) already lists every page - no need
    to hand-build a duplicate nav block here."""
    if os.path.exists(LOGO_CROQUIS_PATH):
        st.sidebar.image(LOGO_CROQUIS_PATH, width="stretch")


# ---------------------------------------------------------------------------
# Module 3 (part 2): Mobile UX optimization
# ---------------------------------------------------------------------------
# Streamlit doesn't expose viewport width to Python, so this is pure CSS:
# media queries do the actual "is this a phone" detection in the browser.
# Two things this targets specifically, per the feature request:
#   1. Critical safety-action buttons (rendered via render_critical_action_
#      button() below, tagged with a data attribute) become massive and
#      high-contrast on narrow screens.
#   2. Heavy chart content (the trend/analytics section) is wrapped in a
#      collapsed st.expander by render_analytics_section() already - the
#      media query here just also shrinks its font/padding on mobile so
#      the collapsed header itself doesn't dominate a phone screen.
def inject_mobile_css() -> None:
    st.markdown(
        """
        <style>
        /* Critical safety-action buttons: identified by a data attribute
           set via a small wrapper markdown span right before the button -
           see render_critical_action_button(). Streamlit doesn't let us
           add arbitrary data-* attributes to st.button directly, so we
           target the *primary* button type broadly on narrow viewports,
           which in this app's pages is only ever used for the run-
           assessment / critical-action calls-to-action. */
        @media (max-width: 768px) {
            div.stButton > button[kind="primary"] {
                font-size: 1.35rem !important;
                font-weight: 800 !important;
                padding: 1.1rem 0.5rem !important;
                min-height: 3.4rem !important;
                border-width: 3px !important;
                letter-spacing: 0.02em;
            }
            /* Metrics stack more readably on a phone-width column */
            div[data-testid="stMetric"] {
                padding: 0.4rem 0.2rem !important;
            }
            /* Reduce heavy heading sizes so more fits above the fold */
            h1 { font-size: 1.6rem !important; }
            h2 { font-size: 1.3rem !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_critical_action_button(label: str, key: str) -> bool:
    """A safety-action button (e.g. 'HALT THE POUR', 'ROTATE CREW',
    'SUSPEND LIFT') styled to be massive and unmistakable on a foreman's
    phone screen via inject_mobile_css()'s [kind="primary"] media-query
    rule above. Functionally identical to st.button(type="primary") - the
    wrapper exists so every call site is self-documenting about *why*
    type="primary" was chosen here specifically."""
    return st.button(label, key=key, type="primary", width="stretch")


# ---------------------------------------------------------------------------
# Module 1 (part 3): Text-to-speech for critical alerts
# ---------------------------------------------------------------------------
# gTTS wraps an UNOFFICIAL Google Translate endpoint, not a stable public
# API - it can be blocked by corporate/site firewalls or break if Google
# changes an internal token, which is exactly the kind of failure Module 5
# asks this app to survive gracefully everywhere else. So this follows the
# same pattern as every other external call in this app: try, and on any
# failure, show a clear "audio unavailable" note and leave the on-screen
# alert text (which is always rendered regardless) as the source of truth -
# never crash the page over a missing audio clip.
# gTTS (Google Translate TTS wrapper) language codes for every language
# the sidebar language selector offers. gTTS's own supported-language list
# doesn't perfectly mirror ISO 639-1 (Mandarin is "zh-CN", not "zh", for
# instance) - text_to_speech_audio() falls back to "en" for anything not
# listed here, and never crashes the page even if a code turns out to be
# rejected by the upstream API (see its try/except below).
_GTTS_LANG_MAP = {
    "fr": "fr", "en": "en", "ar": "ar", "es": "es",
    "zh": "zh-CN", "ja": "ja", "hi": "hi", "ur": "ur",
    "da": "da", "nl": "nl", "no": "no", "sv": "sv",
    "pt": "pt", "de": "de",
}


def text_to_speech_audio(text: str, lang: str) -> bytes | None:
    """Returns MP3 bytes for the given text, or None if TTS is unavailable
    for any reason (library missing, network blocked, upstream API
    change). Never raises."""
    if not TTS_LIBRARY_AVAILABLE or not text:
        return None
    try:
        buf = io.BytesIO()
        gTTS(text=text, lang=_GTTS_LANG_MAP.get(lang, "en")).write_to_fp(buf)
        return buf.getvalue()
    except Exception:  # noqa: BLE001 - any TTS failure -> no audio, not a crash
        return None


def render_tts_button(text: str, lang: str, key: str) -> None:
    """Renders a 'Listen to this alert' button. On click, attempts TTS
    and either plays the audio or shows the offline-safe unavailable
    message - text alerts remain fully readable either way."""
    if st.button(t("tts_button_label", lang), key=key):
        with st.spinner(t("tts_generating", lang)):
            audio_bytes = text_to_speech_audio(text, lang)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3")
        else:
            st.info(t("tts_unavailable", lang))


# ---------------------------------------------------------------------------
# Module 1 (part 4): Instant narrative translation widget
# ---------------------------------------------------------------------------

def render_translation_widget(narrative: str, lang: str, api_key: str | None, key_prefix: str) -> None:
    """Lets an HSE manager translate an already-generated briefing into
    another language on demand (e.g. read the French briefing, translate
    to Gulf Arabic to relay to the crew) without re-running the
    assessment. See ai_advisor.translate_narrative()'s docstring for the
    honesty guarantee: this never fabricates a translation."""
    with st.expander(t("translate_expander_label", lang)):
        # Every language the sidebar interface-language selector offers is
        # also a valid narrative-translation target - built from the same
        # i18n.LANGUAGES source of truth so the two lists can never drift
        # apart. LANGUAGES maps native-display-name -> code; invert it once.
        code_to_native = {code: native for native, code in LANGUAGES.items()}
        target_options = list(code_to_native.keys())
        target = st.selectbox(
            t("translate_target_label", lang),
            options=target_options,
            format_func=lambda code: code_to_native.get(code, code),
            key=f"{key_prefix}_translate_target",
        )
        dialect = "msa"
        if target == "ar":
            dialect_options = {"msa": "Modern Standard Arabic", "gulf": "Gulf Arabic (UAE/Kuwait)", "egyptian": "Egyptian Arabic"}
            dialect = st.selectbox(
                t("translate_dialect_label", lang),
                options=list(dialect_options.keys()),
                format_func=lambda k: dialect_options[k],
                key=f"{key_prefix}_translate_dialect",
            )
        if st.button(t("translate_button", lang), key=f"{key_prefix}_translate_run"):
            if not api_key:
                st.warning(t("translate_no_key", lang))
                st.write(narrative)
            else:
                result = translate_narrative(narrative, target, api_key, dialect)
                if result["translated"]:
                    st.write(result["text"])
                else:
                    st.warning(t("translate_failed", lang))
                    st.write(result["text"])


# ---------------------------------------------------------------------------
# Module 5a (part 2): Country selector (sidebar, session-state-backed like
# the language selector, so the choice persists across page navigation).
# Defaults to the GPS-auto-detected country (via data_feeds.reverse_geocode_
# country, triggered once a GPS fix exists from the Field Inspection
# section) but always allows manual override thereafter.
# ---------------------------------------------------------------------------

def apply_gps_country_autodetect_once(lat: float, lon: float) -> None:
    """Called from render_field_inspection_section() right after a
    successful GPS fix. Auto-applies the detected country as the session's
    active regulatory profile exactly once per session - after that, the
    user's own selection (whether it's the auto-detected value or a manual
    override) always wins, so a later GPS refresh never silently yanks the
    country out from under a deliberate manual choice.

    Forces an immediate rerun on the one occasion it actually changes the
    country: the sidebar country selector is built earlier in the script
    than this Field Inspection section runs, so without the rerun the
    newly-detected country wouldn't be reflected in the selector until the
    user's next incidental interaction - a confusing one-click lag."""
    if st.session_state.get("country_auto_apply_done"):
        return
    st.session_state["country_auto_apply_done"] = True
    geo = reverse_geocode_country(lat, lon)
    if geo.get("used_fallback"):
        # GPS resolved to a real country, but that country has no
        # registered regulatory profile in regulatory_country_thresholds.py -
        # reverse_geocode_country() already substituted the GLOBAL/ACGIH-
        # OSHA fallback code below, so this toast is purely informational,
        # using the exact required wording (i18n's "en" entry matches it
        # verbatim; other languages are real translations of the same
        # message).
        st.toast(t("regulatory_fallback_warning", st.session_state.get("lang", "fr")), icon="⚠️")
    if geo["country_code"]:
        # Don't write directly to "country_code" or the widget's own key
        # here - render_country_selector() already ran earlier THIS script
        # pass (sidebar renders before this Field Inspection section), and
        # Streamlit raises StreamlitAPIException if you modify a widget's
        # key after that widget has already been instantiated in the same
        # run. Instead, stage the change and force a fresh pass: on the
        # next run, render_country_selector() (which runs before this
        # section) consumes the pending override and seeds both the
        # widget's key and the mirror variable BEFORE the widget is
        # created - which is the only point it's safe to do so.
        st.session_state["_pending_country_override"] = geo["country_code"]
        st.session_state["country_auto_detected_code"] = geo["country_code"]
        st.session_state["country_auto_detect_source"] = geo["source"]
        st.rerun()


def render_country_selector(lang: str) -> dict:
    """Renders the regulatory-framework/country selector and returns the
    resolved regulatory profile dict. Also surfaces the UAE midday
    outdoor-work-ban banner when applicable - the one place in this app
    where that statutory rule is genuinely relevant (outdoor modules:
    Solar, Offshore, Wind Energy, Marine & Port).

    The widget's own session_state key ("country_selector_widget") is the
    single source of truth for its current value - no separate index=
    parameter is used alongside it. Streamlit warns (and this app used to
    trigger that warning) when a widget is given both a default via
    index=/value= AND has its state also set through the Session State
    API - the fix is to never do both for the same key, only ever writing
    to the key itself, and only before that widget is instantiated in the
    current run."""
    if "country_selector_widget" not in st.session_state:
        st.session_state["country_selector_widget"] = "USA"

    # Consume any pending GPS auto-detect override staged by
    # apply_gps_country_autodetect_once() on a prior run - this MUST
    # happen before the selectbox below is instantiated; writing to its
    # key afterward raises StreamlitAPIException.
    pending = st.session_state.pop("_pending_country_override", None)
    if pending:
        st.session_state["country_selector_widget"] = pending

    codes = list(COUNTRY_LABELS.keys())
    chosen = st.sidebar.selectbox(
        t("country_selector_label", lang),
        options=codes,
        format_func=lambda c: COUNTRY_LABELS[c],
        key="country_selector_widget",
    )
    st.session_state["country_code"] = chosen  # read-only mirror for other code
    if chosen == st.session_state.get("country_auto_detected_code"):
        st.sidebar.caption(t("country_auto_detected_note", lang))
    render_workload_selector(lang)
    return get_country_thresholds(chosen)


def alert_with_regulation(base_message: str, result: dict) -> str:
    """Appends the regulatory profile that actually produced this result to
    an alert/TTS message - e.g. 'CRITICAL ALERT: ... — France (Code du
    Travail / INRS)'. Every calculate_*_kinetic_risk() function now tags
    its result with regulatory_profile_label for exactly this purpose."""
    label = result.get("regulatory_profile_label")
    return f"{base_message} — {label}" if label else base_message


def render_midday_ban_banner_if_active(lang: str, country_code: str) -> None:
    """Shown on outdoor-work modules only. Honest by construction: this
    calls is_midday_outdoor_ban_active() for TODAY's real date, so it can
    only ever fire for a country whose profile actually defines the rule
    (currently just UAE) and only during the real statutory window."""
    if is_midday_outdoor_ban_active(country_code, check_hour=None):
        # Season-only check here (no specific hour known ahead of a live
        # clock reading) - still a meaningful heads-up for a manager
        # planning today's shift, without claiming false precision.
        st.warning(t("midday_ban_active_warning", lang))


def render_remote_comms_banner_if_required(lang: str, country_code: str) -> None:
    """Shown on remote/isolated-site modules (Wind Energy, Mining &
    Quarrying, Marine & Port Construction). Honest by construction: only
    ever fires for a country whose profile actually defines a remote_comms
    requirement (currently only Australia's Safe Work Australia isolated-
    worker rule) - is_remote_comms_required() returns False for every
    other registered profile."""
    if is_remote_comms_required(country_code):
        st.info(t("remote_comms_banner", lang))
        cfg = get_remote_comms_config(country_code)
        if cfg:
            st.caption(cfg["source_note"])


def render_uv_and_bushfire_smoke_panel(lang: str, country_code: str, uv_index: float | None,
                                        lat: float, lon: float) -> None:
    """Australia-only supplementary panel: SunSmart UV-Index category
    (Safe Work Australia / Cancer Council Australia scale) plus, when a
    live ambient PM2.5 reading is reachable, an illustrative bushfire-
    smoke air-quality category. Both are pure display, sourced from
    country-profile band tables via risk_engine's generic classifiers -
    they never feed into or override the module's own risk_band (Module 3
    doesn't have a bushfire/UV hazard of its own; this is purely the AU
    regulatory cross-check requested for the Solar module, which already
    collects a uv_index reading).

    Silently does nothing for every other country - get_uv_heat_config()
    returns None whenever the active profile doesn't define a uv_heat
    section, which today is every profile except Australia."""
    uv_cfg = get_uv_heat_config(country_code)
    if not uv_cfg:
        return

    with st.expander(f"☀️🇦🇺 {t('uv_category_label', lang)} / {t('bushfire_smoke_header', lang)}"):
        if uv_index is not None:
            category = classify_uv_index(uv_index, uv_cfg["uv_index_bands"])
            st.metric(t("uv_category_label", lang), category, help=f"UV Index {uv_index}")
            if uv_index >= uv_cfg["action_at_or_above_uv_index"]:
                st.warning(t("uv_category_label", lang) + f": {category}")
            st.caption(uv_cfg["source_note"])

        bands = get_bushfire_smoke_bands(country_code)
        if bands:
            st.markdown("---")
            st.subheader(t("bushfire_smoke_header", lang))
            try:
                aq = fetch_air_quality_live(lat, lon)
                pm25 = aq["pm2_5_ugm3"]
                smoke_category = classify_bushfire_smoke_pm25(pm25, bands)
                st.metric("PM2.5", f"{pm25} µg/m³", help=smoke_category)
                st.write(f"**{smoke_category}**")
                st.caption(f"{aq['source']} · {aq['fetched_at']}")
            except DataFeedError as exc:
                st.info(str(exc))


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

    apply_gps_country_autodetect_once(lat, lon)
    closest_module, distance_km = _closest_site(lat, lon)

    col1, col2, col3 = st.columns(3)
    col1.metric(t("field_inspection_your_position", lang), f"{lat:.5f}, {lon:.5f}")
    accuracy = coords.get("accuracy")
    col2.metric(t("field_inspection_accuracy_label", lang), f"±{accuracy:.0f} m" if accuracy else "-")
    col3.metric(t("field_inspection_distance_label", lang), f"{distance_km:.1f} km")

    st.write(f"**{t('field_inspection_closest_site_label', lang)}:** {t(SITE_COORDINATES[closest_module]['nav_key'], lang)}")

    # Module 3 geofencing: instantly switch to a high-visibility layout
    # when the live GPS fix falls within GEOFENCE_RADIUS_KM of a site.
    inside_zone, zone_module, _ = is_inside_geofence(lat, lon)
    if inside_zone:
        st.error(f"{t('geofence_inside_label', lang)} - {t(SITE_COORDINATES[zone_module]['nav_key'], lang)}")
    else:
        st.caption(t("geofence_outside_label", lang))

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

def render_daily_briefing_section(lang: str) -> None:
    """Module 4 (part 1) dashboard section: generates a toolbox-talk script
    for the day, tailored to scheduled tasks + current weather. Uses the
    same api_key session-state value the module pages' AI layer uses."""
    st.subheader(t("daily_briefing_header", lang))
    st.caption(t("daily_briefing_caption", lang))

    api_key = st.session_state.get("api_key", "")
    col1, col2 = st.columns(2)
    with col1:
        site_name = st.text_input(t("daily_briefing_site_label", lang), value="MAKU Site", key="briefing_site_name")
    with col2:
        tasks_raw = st.text_area(t("daily_briefing_tasks_label", lang), key="briefing_tasks", height=100)

    if st.button(t("daily_briefing_generate_button", lang), key="briefing_generate_button"):
        tasks = [line.strip() for line in tasks_raw.splitlines() if line.strip()]
        weather_summary = fetch_live_weather_universal(24.4539, 54.3773, api_key=None)
        result = generate_daily_briefing(site_name, tasks, weather_summary, api_key or None, lang)
        st.session_state["daily_briefing_script"] = result["script"]

    if st.session_state.get("daily_briefing_script"):
        st.markdown(f"**{t('daily_briefing_script_label', lang)}:**")
        st.write(st.session_state["daily_briefing_script"])
        render_tts_button(st.session_state["daily_briefing_script"], lang, key="briefing_tts")


def render_dashboard():
    """The landing/overview page. Must call st.set_page_config as its own
    first Streamlit command, exactly like every other page - with
    st.navigation, each page (function or file) is its own script run."""
    st.set_page_config(page_title="MAKU - Kinetic Risk Platform", page_icon="🛡️", layout="wide")
    inject_mobile_css()

    if os.path.exists(LOGO_CROQUIS_PATH):
        st.sidebar.image(LOGO_CROQUIS_PATH, width="stretch", caption="The Five Worlds of MAKU")

    lang = language_selector(st)
    country_thresholds = render_country_selector(lang)

    st.sidebar.title(t("app_title", lang))
    st.sidebar.caption(t("app_tagline", lang))
    st.sidebar.markdown("---")
    render_logout_control(st)
    st.sidebar.markdown("---")

    if os.path.exists(LOGO_MODERNE_PATH):
        st.image(LOGO_MODERNE_PATH, width="stretch")

    st.title(t("app_title", lang))
    st.caption(t("app_tagline", lang))

    render_midday_ban_banner_if_active(lang, country_thresholds["country_code"])

    st.header(t("dashboard_intro_header", lang))
    st.write(t("dashboard_intro_body", lang))

    st.subheader(t("dashboard_module_col_header", lang))

    st.markdown("---")
    render_field_inspection_section(lang)

    st.markdown("---")
    render_daily_briefing_section(lang)

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
    inject_mobile_css()

    lang = language_selector(st)
    country_thresholds = render_country_selector(lang)
    work_rate = st.session_state["workload_intensity"]
    _sidebar_brand(lang)
    render_logout_control(st)
    api_key = _render_ai_layer_sidebar(lang)
    enable_web_search = render_web_search_toggle(st, lang, "solar")

    st.title(t("solar_header", lang))
    st.caption(t("solar_caption", lang))
    render_midday_ban_banner_if_active(lang, country_thresholds["country_code"])

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

    _render_acgih_reference_panel(lang, ambient_temp, relative_humidity=30.0,
                                   regulatory_profile=country_thresholds, work_rate=work_rate)
    render_uv_and_bushfire_smoke_panel(
        lang, country_thresholds["country_code"], uv_index,
        lat=SOLAR_COORDS["lat"], lon=SOLAR_COORDS["lon"],
    )

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
            ghi=ghi, uv_index=uv_index, ambient_temp=ambient_temp, surface_type=surface_type,
            regulatory_profile=country_thresholds,
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
            st.error(alert_with_regulation(t("solar_critical_alert", lang), result))
            render_tts_button(alert_with_regulation(t("solar_critical_alert", lang), result), lang, key="solar_tts")
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
        render_translation_widget(narrative, lang, api_key, key_prefix="solar")

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
    inject_mobile_css()

    lang = language_selector(st)
    country_thresholds = render_country_selector(lang)
    work_rate = st.session_state["workload_intensity"]
    _sidebar_brand(lang)
    render_logout_control(st)
    api_key = _render_ai_layer_sidebar(lang)
    enable_web_search = render_web_search_toggle(st, lang, "offshore")

    st.title(t("offshore_header", lang))
    st.caption(t("offshore_caption", lang))
    render_midday_ban_banner_if_active(lang, country_thresholds["country_code"])

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

    _render_acgih_reference_panel(
        lang, ambient_temp, relative_humidity,
        regulatory_profile=country_thresholds, work_rate=work_rate,
        wind_speed_kmh=round(wind_speed * 1.852, 1) if wind_speed is not None else None,
    )

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
            ambient_temp=ambient_temp, relative_humidity=relative_humidity, wind_speed=wind_speed,
            regulatory_profile=country_thresholds,
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
            st.error(alert_with_regulation(t("offshore_elevated_alert", lang), result))
            render_tts_button(alert_with_regulation(t("offshore_elevated_alert", lang), result), lang, key="offshore_tts")
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
        render_translation_widget(narrative, lang, api_key, key_prefix="offshore")

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
    inject_mobile_css()

    lang = language_selector(st)
    country_thresholds = render_country_selector(lang)
    work_rate = st.session_state["workload_intensity"]
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

    _render_acgih_reference_panel(lang, ambient_temp, geothermal_humidity,
                                   regulatory_profile=country_thresholds, work_rate=work_rate)

    st.markdown("---")

    if st.button(t("run_button", lang), type="primary", width="stretch"):
        result = calculate_underground_kinetic_risk(
            ambient_temp=ambient_temp,
            geothermal_humidity=geothermal_humidity,
            particulate_matter_pm25=pm25,
            gas_co_ppm=gas_co_ppm,
            regulatory_profile=country_thresholds,
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
            st.error(alert_with_regulation(t("underground_critical_alert", lang), result))
            render_tts_button(alert_with_regulation(t("underground_critical_alert", lang), result), lang, key="underground_tts")
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
        render_translation_widget(narrative, lang, api_key, key_prefix="underground")

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
    inject_mobile_css()

    lang = language_selector(st)
    country_thresholds = render_country_selector(lang)
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
            regulatory_profile=country_thresholds,
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
            st.error(alert_with_regulation(t("highrise_critical_alert", lang), result))
            st.error(t("fall_arrest_alert", lang))
            render_tts_button(alert_with_regulation(t("highrise_critical_alert", lang), result), lang, key="highrise_tts")
        elif result["risk_band"] in ("HIGH", "MODERATE"):
            st.warning(t("highrise_high_alert", lang))
        else:
            st.success(t("highrise_standard_ok", lang))

        col1, col2, col3 = st.columns(3)
        col1.metric(t("scaled_wind_label", lang), f"{result['scaled_wind_speed']} kn")
        col2.metric(t("oscillation_index_label", lang), result["oscillation_index"])
        col3.metric(t("crane_gate_label", lang), f"{country_thresholds['wind_shear']['crane_suspend_knots']} kn")
        crane_suspend_mph = country_thresholds["wind_shear"].get("crane_suspend_mph")
        if crane_suspend_mph is not None:
            # UK profile only, currently - HSE/site anemometry there
            # commonly reports crane wind gates in mph as well as knots.
            st.caption(
                f"{t('crane_wind_mph_caption', lang)}: "
                f"{crane_suspend_mph} mph / {country_thresholds['wind_shear']['crane_suspend_knots']} kn"
            )

        st.subheader(t("risk_band_label", lang))
        st.write(result["risk_band"])

        st.subheader(t("drivers_label", lang))
        st.table({k: str(v) for k, v in result["drivers"].items()})

        st.subheader(t("briefing_label", lang))
        st.write(narrative)
        render_translation_widget(narrative, lang, api_key, key_prefix="highrise")

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
    inject_mobile_css()

    lang = language_selector(st)
    country_thresholds = render_country_selector(lang)
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
            regulatory_profile=country_thresholds,
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
            st.error(alert_with_regulation(t("datacenter_critical_alert", lang), result))
            render_tts_button(alert_with_regulation(t("datacenter_critical_alert", lang), result), lang, key="datacenter_tts")
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
        render_translation_widget(narrative, lang, api_key, key_prefix="datacenter")

        st.subheader(t("controls_label", lang))
        for control in controls:
            st.markdown(f"- {control}")

        st.markdown("---")
        render_official_report(st, result=result, narrative=narrative, controls=controls, lang=lang)

    st.markdown("---")
    render_virtual_library(st, lang, module="Data Center (Controlled Critical Environment)")


# ===========================================================================
# Module 6: Wind Energy (Onshore/Offshore)
# ===========================================================================

def render_wind_energy():
    """UI for calculate_wind_energy_kinetic_risk(). "Automatique" mode uses
    fetch_live_weather_universal() (Open-Meteo/OpenWeatherMap/mock chain)
    for wind speed; lightning and offshore sea-state are always manual
    inputs since they're site observations, not generic weather-API fields."""
    st.set_page_config(page_title="MAKU - Wind Energy", page_icon="💨", layout="wide")
    inject_mobile_css()

    lang = language_selector(st)
    country_thresholds = render_country_selector(lang)
    _sidebar_brand(lang)
    render_logout_control(st)
    api_key = _render_ai_layer_sidebar(lang)
    enable_web_search = render_web_search_toggle(st, lang, "windenergy")

    st.title(t("windenergy_header", lang))
    st.caption(t("windenergy_caption", lang))
    render_midday_ban_banner_if_active(lang, country_thresholds["country_code"])
    render_remote_comms_banner_if_required(lang, country_thresholds["country_code"])

    is_offshore = st.checkbox(t("windenergy_offshore_toggle", lang))

    data_mode = render_data_mode_selector(st, lang, "windenergy")
    hub_height_wind_speed_ms = None

    if data_mode == "auto":
        try:
            live = fetch_live_weather_universal(WIND_ENERGY_COORDS["lat"], WIND_ENERGY_COORDS["lon"])
            render_feed_ok_banner(st, lang, live["source"], live["fetched_at"])
            hub_height_wind_speed_ms = round(live["wind_speed_10m_kn"] * 0.514444, 1)  # knots -> m/s
            st.metric(t("windenergy_wind_label", lang), f"{hub_height_wind_speed_ms} m/s")
        except DataFeedError as exc:
            render_feed_error_banner(st, lang, str(exc))
            data_mode = "manual"

    if data_mode == "manual":
        st.subheader(t("windenergy_env_data_header", lang))
        hub_height_wind_speed_ms = st.slider(t("windenergy_wind_label", lang), 0.0, 30.0, 8.0, 0.5)

    col1, col2 = st.columns(2)
    with col1:
        lightning_observed = st.checkbox(t("windenergy_lightning_toggle", lang))
        flash_to_bang_sec = None
        if lightning_observed:
            flash_to_bang_sec = st.slider(t("windenergy_lightning_label", lang), 1.0, 120.0, 45.0, 1.0)
    with col2:
        significant_wave_height_m = 0.0
        if is_offshore:
            significant_wave_height_m = st.slider(t("windenergy_wave_label", lang), 0.0, 5.0, 1.0, 0.1)

    st.markdown("---")

    if render_critical_action_button(t("run_button", lang), key="windenergy_run"):
        result = calculate_wind_energy_kinetic_risk(
            hub_height_wind_speed_ms=hub_height_wind_speed_ms,
            is_offshore=is_offshore,
            significant_wave_height_m=significant_wave_height_m,
            flash_to_bang_sec=flash_to_bang_sec,
            regulatory_profile=country_thresholds,
        )
        controls = get_controls(result)
        narrative = generate_narrative(
            result, controls, api_key=api_key, lang=lang, enable_web_search=enable_web_search
        )

        log_assessment(st, result)
        st.session_state["latest_risk_result"] = result
        st.session_state["latest_ai_narrative"] = narrative
        st.session_state["latest_controls"] = controls

    if st.session_state.get("latest_risk_result", {}).get("module") == "Wind Energy (Onshore/Offshore)":
        result = st.session_state["latest_risk_result"]
        narrative = st.session_state["latest_ai_narrative"]
        controls = st.session_state["latest_controls"]

        if result["safety_override"]:
            st.error(t("safety_override", lang))
            st.error(alert_with_regulation(t("windenergy_critical_alert", lang), result))
            render_tts_button(alert_with_regulation(t("windenergy_critical_alert", lang), result), lang, key="windenergy_tts")
        elif result["risk_band"] in ("HIGH", "MODERATE"):
            st.warning(t("windenergy_high_alert", lang))
        else:
            st.success(t("windenergy_standard_ok", lang))

        col1, col2, col3 = st.columns(3)
        col1.metric(t("windenergy_wind_label", lang), f"{result['hub_height_wind_speed_ms']} m/s")
        col2.metric(t("lightning_status_label", lang), result["lightning_status"])
        col3.metric(t("ctv_status_label", lang), result["ctv_transfer_status"])

        st.subheader(t("risk_band_label", lang))
        st.write(result["risk_band"])

        st.subheader(t("drivers_label", lang))
        st.table({k: str(v) for k, v in result["drivers"].items()})

        st.subheader(t("briefing_label", lang))
        st.write(narrative)
        render_translation_widget(narrative, lang, api_key, key_prefix="windenergy")

        st.subheader(t("controls_label", lang))
        for control in controls:
            st.markdown(f"- {control}")

        st.markdown("---")
        render_official_report(st, result=result, narrative=narrative, controls=controls, lang=lang)

    st.markdown("---")
    render_virtual_library(st, lang, module="Wind Energy (Onshore/Offshore)")


# ===========================================================================
# Module 7: Mining & Quarrying
# ===========================================================================

def render_mining_quarrying():
    """UI for calculate_mining_quarrying_kinetic_risk(). No natural public
    live-feed source for silica/noise/vibration readings exists (same
    situation as Underground/High-Rise/Data Center), so this module is
    manual-input only. Noise criterion/exchange-rate come from the sidebar
    country selector (Module 5a) rather than a hardcoded constant."""
    st.set_page_config(page_title="MAKU - Mining & Quarrying", page_icon="⛏️", layout="wide")
    inject_mobile_css()

    lang = language_selector(st)
    country_thresholds = render_country_selector(lang)
    _sidebar_brand(lang)
    render_logout_control(st)
    api_key = _render_ai_layer_sidebar(lang)
    enable_web_search = render_web_search_toggle(st, lang, "mining")

    st.title(t("mining_header", lang))
    st.caption(t("mining_caption", lang))
    st.caption(f"{t('country_selector_label', lang)}: {country_thresholds['label']} "
               f"({country_thresholds['noise_criterion_dba']:.0f} dBA / "
               f"{country_thresholds['noise_exchange_rate_db']:.0f} dB exchange rate)")
    render_remote_comms_banner_if_required(lang, country_thresholds["country_code"])

    st.subheader(t("mining_env_data_header", lang))
    col1, col2 = st.columns(2)
    with col1:
        respirable_silica_ugm3 = st.slider(t("mining_silica_label", lang), 0.0, 150.0, 15.0, 1.0)
        measured_noise_dba = st.slider(t("mining_noise_label", lang), 60.0, 120.0, 80.0, 1.0)
        noise_exposure_hours = st.slider(t("mining_noise_hours_label", lang), 0.0, 12.0, 8.0, 0.5)
    with col2:
        measured_vibration_aw_ms2 = st.slider(t("mining_vibration_label", lang), 0.0, 3.0, 0.3, 0.05)
        vibration_exposure_hours = st.slider(t("mining_vibration_hours_label", lang), 0.0, 12.0, 8.0, 0.5)

    render_uv_and_bushfire_smoke_panel(
        lang, country_thresholds["country_code"], uv_index=None,
        lat=MINING_COORDS["lat"], lon=MINING_COORDS["lon"],
    )

    st.markdown("---")

    if render_critical_action_button(t("run_button", lang), key="mining_run"):
        result = calculate_mining_quarrying_kinetic_risk(
            respirable_silica_ugm3=respirable_silica_ugm3,
            measured_noise_dba=measured_noise_dba,
            noise_exposure_hours=noise_exposure_hours,
            measured_vibration_aw_ms2=measured_vibration_aw_ms2,
            vibration_exposure_hours=vibration_exposure_hours,
            regulatory_profile=country_thresholds,
        )
        controls = get_controls(result)
        narrative = generate_narrative(
            result, controls, api_key=api_key, lang=lang, enable_web_search=enable_web_search
        )

        log_assessment(st, result)
        st.session_state["latest_risk_result"] = result
        st.session_state["latest_ai_narrative"] = narrative
        st.session_state["latest_controls"] = controls

    if st.session_state.get("latest_risk_result", {}).get("module") == "Mining & Quarrying":
        result = st.session_state["latest_risk_result"]
        narrative = st.session_state["latest_ai_narrative"]
        controls = st.session_state["latest_controls"]

        if result["safety_override"]:
            st.error(t("safety_override", lang))
            st.error(alert_with_regulation(t("mining_critical_alert", lang), result))
            render_tts_button(alert_with_regulation(t("mining_critical_alert", lang), result), lang, key="mining_tts")
        elif result["risk_band"] in ("HIGH", "MODERATE"):
            st.warning(t("mining_high_alert", lang))
        else:
            st.success(t("mining_standard_ok", lang))

        col1, col2, col3 = st.columns(3)
        col1.metric(t("silica_exceeds_label", lang), t("yes", lang) if result["silica_exceeds_oel"] else t("no", lang))
        col2.metric(t("noise_dose_label", lang), f"{result['noise_dose_pct']}%")
        col3.metric(t("vibration_a8_label", lang), result["vibration_a8_ms2"])

        st.subheader(t("risk_band_label", lang))
        st.write(result["risk_band"])

        st.subheader(t("drivers_label", lang))
        st.table({k: str(v) for k, v in result["drivers"].items()})

        st.subheader(t("briefing_label", lang))
        st.write(narrative)
        render_translation_widget(narrative, lang, api_key, key_prefix="mining")

        st.subheader(t("controls_label", lang))
        for control in controls:
            st.markdown(f"- {control}")

        st.markdown("---")
        render_official_report(st, result=result, narrative=narrative, controls=controls, lang=lang)

    st.markdown("---")
    render_virtual_library(st, lang, module="Mining & Quarrying")


# ===========================================================================
# Module 8: Marine & Port Construction
# ===========================================================================

def render_marine_port_construction():
    """UI for calculate_marine_port_kinetic_risk(). Tide level, night-ops
    flag, illuminance, and hardware age/exposure class are all site/
    operational facts rather than generic weather-API fields, so this
    module is manual-input only (same reasoning as Underground/High-Rise/
    Data Center: no natural live-feed source exists for these readings)."""
    st.set_page_config(page_title="MAKU - Marine & Port Construction", page_icon="⚓", layout="wide")
    inject_mobile_css()

    lang = language_selector(st)
    country_thresholds = render_country_selector(lang)
    _sidebar_brand(lang)
    render_logout_control(st)
    api_key = _render_ai_layer_sidebar(lang)
    enable_web_search = render_web_search_toggle(st, lang, "marineport")

    st.title(t("marineport_header", lang))
    st.caption(t("marineport_caption", lang))
    render_remote_comms_banner_if_required(lang, country_thresholds["country_code"])

    st.subheader(t("marineport_env_data_header", lang))
    col1, col2 = st.columns(2)
    with col1:
        current_tide_level_m = st.slider(t("marineport_tide_label", lang), 0.0, 4.0, 2.0, 0.1)
        required_min_clearance_m = st.slider(t("marineport_clearance_label", lang), 0.0, 3.0, 1.0, 0.1)
    with col2:
        is_night_operation = st.checkbox(t("marineport_night_toggle", lang))
        measured_illuminance_lux = st.slider(t("marineport_illuminance_label", lang), 0.0, 300.0, 150.0, 5.0)

    col3, col4 = st.columns(2)
    with col3:
        hardware_years_in_service = st.slider(t("marineport_hardware_years_label", lang), 0.0, 30.0, 3.0, 0.5)
    with col4:
        exposure_options = ["C3_moderate", "C4_high", "C5M_marine_splash_zone"]
        hardware_exposure_class = st.selectbox(
            t("marineport_exposure_class_label", lang), options=exposure_options, index=2,
            format_func=lambda v: v.replace("_", " "),
        )

    st.markdown("---")

    if render_critical_action_button(t("run_button", lang), key="marineport_run"):
        result = calculate_marine_port_kinetic_risk(
            current_tide_level_m=current_tide_level_m,
            required_min_clearance_m=required_min_clearance_m,
            is_night_operation=is_night_operation,
            measured_illuminance_lux=measured_illuminance_lux,
            hardware_years_in_service=hardware_years_in_service,
            hardware_exposure_class=hardware_exposure_class,
            regulatory_profile=country_thresholds,
        )
        controls = get_controls(result)
        narrative = generate_narrative(
            result, controls, api_key=api_key, lang=lang, enable_web_search=enable_web_search
        )

        log_assessment(st, result)
        st.session_state["latest_risk_result"] = result
        st.session_state["latest_ai_narrative"] = narrative
        st.session_state["latest_controls"] = controls

    if st.session_state.get("latest_risk_result", {}).get("module") == "Marine & Port Construction":
        result = st.session_state["latest_risk_result"]
        narrative = st.session_state["latest_ai_narrative"]
        controls = st.session_state["latest_controls"]

        if result["safety_override"]:
            st.error(t("safety_override", lang))
            st.error(alert_with_regulation(t("marineport_critical_alert", lang), result))
            render_tts_button(alert_with_regulation(t("marineport_critical_alert", lang), result), lang, key="marineport_tts")
        elif result["risk_band"] in ("HIGH", "MODERATE"):
            st.warning(t("marineport_high_alert", lang))
        else:
            st.success(t("marineport_standard_ok", lang))

        col1, col2, col3 = st.columns(3)
        col1.metric(t("tide_margin_label", lang), f"{result['tide_clearance_margin_m']} m")
        col2.metric(t("hardware_capacity_label", lang), f"{result['hardware_remaining_capacity_pct']}%")
        col3.metric(t("risk_band_label", lang), result["risk_band"])

        st.subheader(t("drivers_label", lang))
        st.table({k: str(v) for k, v in result["drivers"].items()})

        st.subheader(t("briefing_label", lang))
        st.write(narrative)
        render_translation_widget(narrative, lang, api_key, key_prefix="marineport")

        st.subheader(t("controls_label", lang))
        for control in controls:
            st.markdown(f"- {control}")

        st.markdown("---")
        render_official_report(st, result=result, narrative=narrative, controls=controls, lang=lang)

    st.markdown("---")
    render_virtual_library(st, lang, module="Marine & Port Construction")


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
page_windenergy = st.Page(render_wind_energy, title="Wind Energy", icon="💨")
page_mining = st.Page(render_mining_quarrying, title="Mining & Quarrying", icon="⛏️")
page_marineport = st.Page(render_marine_port_construction, title="Marine & Port", icon="⚓")

# Maps each SITE_COORDINATES module name to its Page object, so the closest-
# site lookup in render_field_inspection_section() can route straight there.
MODULE_PAGES = {
    "Solar (Desert)": page_solar,
    "Offshore (Marine)": page_offshore,
    "Underground (Tunnel/Metro)": page_underground,
    "High-Rise (Vertical Urban)": page_highrise,
    "Data Center (Controlled Critical Environment)": page_datacenter,
    "Wind Energy (Onshore/Offshore)": page_windenergy,
    "Mining & Quarrying": page_mining,
    "Marine & Port Construction": page_marineport,
}

pg = st.navigation([
    page_dashboard, page_solar, page_offshore, page_underground, page_highrise, page_datacenter,
    page_windenergy, page_mining, page_marineport,
])
pg.run()
