"""
MAKU - Live Data Feeds & Simulated Telemetry
=============================================
Centralizes every "Automatique / Temps Reel" data acquisition path:

  - Module 1 (Solar):     live Open-Meteo forecast API (real HTTP call)
  - Module 2 (Offshore):  live Open-Meteo forecast + Marine APIs (real HTTP call)
  - Module 3 (Tunnels):   simulated LoRaWAN IoT sensor-hub stream
  - Module 4 (High-Rise): simulated crane anemometer / oscillation telemetry
  - Module 5 (Data Ctr):  simulated current-transformer / thermal-probe feed

No public, free, keyless real-time API exists for underground gas/dust
sensors, crane-mounted anemometers, or data-center current transformers, so
Modules 3-5 use a bounded random-walk simulator that mimics a live industrial
sensor feed (slow drift + occasional spikes) rather than a static value. This
is clearly labeled "Simulation" in the UI - it is not presented as real data.

Mathematical Isolation rule still applies here: this file only ACQUIRES
numbers (from the network or from the simulator). All risk math stays in
risk_engine.py - nothing in this file computes risk, WBGT, humidex, etc.
"""

from __future__ import annotations

import random
import time

import requests
import streamlit as st

from regulatory_country_thresholds import FALLBACK_COUNTRY_CODE, FALLBACK_WARNING_MESSAGE

REQUEST_TIMEOUT = 6          # seconds - fail fast rather than hang the UI
CACHE_TTL_SECONDS = 30       # avoid hammering the public API on every rerun

# Fixed site coordinates per spec
SOLAR_COORDS = {"lat": 24.4539, "lon": 54.3773}      # desert / solar farm belt
OFFSHORE_COORDS = {"lat": 25.5000, "lon": 53.5000}   # offshore Gulf block

# Small, rare chance a simulated sensor link drops out, so the "fails back
# safely to manual" behavior is exercised for the simulated modules too, not
# only for the two real network calls.
SIM_DROPOUT_PROB = 0.03


class DataFeedError(Exception):
    """Raised whenever a live or simulated feed cannot be retrieved.
    The calling page catches this, shows a dashboard warning, and reverts
    to manual/simulation sliders."""


def _maybe_simulate_dropout(source_label: str) -> None:
    if random.random() < SIM_DROPOUT_PROB:
        raise DataFeedError(f"{source_label}: signal lost / packet timeout")


# ---------------------------------------------------------------------------
# Module 1 - Solar Farms (Open-Meteo standard forecast API)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_solar_live(lat: float = SOLAR_COORDS["lat"], lon: float = SOLAR_COORDS["lon"]) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,uv_index,shortwave_radiation",
        "timezone": "auto",
    }
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        current = resp.json()["current"]
        return {
            "temperature_2m": float(current["temperature_2m"]),
            "uv_index": float(current["uv_index"]),
            "shortwave_radiation": float(current["shortwave_radiation"]),
            "fetched_at": current.get("time"),
            "source": "Open-Meteo /v1/forecast",
        }
    except Exception as exc:  # noqa: BLE001 - any failure -> safe fallback
        raise DataFeedError(f"Open-Meteo forecast API: {exc}") from exc


FORECAST_CACHE_TTL_SECONDS = 1800  # 30 min - daily forecasts don't need 30s freshness


@st.cache_data(ttl=FORECAST_CACHE_TTL_SECONDS, show_spinner=False)
def fetch_solar_forecast(lat: float = SOLAR_COORDS["lat"], lon: float = SOLAR_COORDS["lon"],
                          days: int = 7) -> dict:
    """
    Real 7-day-ahead meteorology forecast (Open-Meteo daily forecast API,
    same free/keyless source as fetch_solar_live) - daily max temperature,
    max UV index, and total shortwave radiation, for forward risk planning
    (e.g. "heat risk is trending up over the next 3 days").
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,uv_index_max,shortwave_radiation_sum",
        "forecast_days": max(1, min(days, 16)),
        "timezone": "auto",
    }
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        daily = resp.json()["daily"]
        return {
            "dates": daily["time"],
            "temperature_2m_max": [float(v) for v in daily["temperature_2m_max"]],
            "uv_index_max": [float(v) for v in daily["uv_index_max"]],
            "shortwave_radiation_sum": [float(v) for v in daily["shortwave_radiation_sum"]],
            "source": "Open-Meteo /v1/forecast (daily)",
        }
    except Exception as exc:  # noqa: BLE001
        raise DataFeedError(f"Open-Meteo daily forecast API: {exc}") from exc


# ---------------------------------------------------------------------------
# Module 2 - Offshore / Marine (Open-Meteo Marine + standard forecast APIs)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_offshore_live(lat: float = OFFSHORE_COORDS["lat"], lon: float = OFFSHORE_COORDS["lon"]) -> dict:
    forecast_url = "https://api.open-meteo.com/v1/forecast"
    marine_url = "https://marine-api.open-meteo.com/v1/marine"

    try:
        f_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "wind_speed_unit": "kn",
            "timezone": "auto",
        }
        f_resp = requests.get(forecast_url, params=f_params, timeout=REQUEST_TIMEOUT)
        f_resp.raise_for_status()
        f_current = f_resp.json()["current"]

        m_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "wave_height,ocean_current_velocity",
            "timezone": "auto",
        }
        m_resp = requests.get(marine_url, params=m_params, timeout=REQUEST_TIMEOUT)
        m_resp.raise_for_status()
        m_current = m_resp.json()["current"]

        return {
            "temperature_2m": float(f_current["temperature_2m"]),
            "relative_humidity_2m": float(f_current["relative_humidity_2m"]),
            "wind_speed_10m_kn": float(f_current["wind_speed_10m"]),
            "wave_height_m": float(m_current.get("wave_height") or 0.0),
            "ocean_current_velocity_ms": float(m_current.get("ocean_current_velocity") or 0.0),
            "fetched_at": f_current.get("time"),
            "source": "Open-Meteo /v1/forecast + Marine API",
        }
    except Exception as exc:  # noqa: BLE001 - any failure -> safe fallback
        raise DataFeedError(f"Open-Meteo forecast/marine API: {exc}") from exc


@st.cache_data(ttl=FORECAST_CACHE_TTL_SECONDS, show_spinner=False)
def fetch_offshore_forecast(lat: float = OFFSHORE_COORDS["lat"], lon: float = OFFSHORE_COORDS["lon"],
                             days: int = 7) -> dict:
    """
    Real 7-day-ahead meteorology forecast for the offshore block (Open-Meteo
    daily forecast API, same free/keyless source as fetch_offshore_live) -
    daily max temperature and max wind speed, for forward risk planning
    (e.g. "wind-gate risk rising later this week").
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,wind_speed_10m_max",
        "wind_speed_unit": "kn",
        "forecast_days": max(1, min(days, 16)),
        "timezone": "auto",
    }
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        daily = resp.json()["daily"]
        return {
            "dates": daily["time"],
            "temperature_2m_max": [float(v) for v in daily["temperature_2m_max"]],
            "wind_speed_10m_max_kn": [float(v) for v in daily["wind_speed_10m_max"]],
            "source": "Open-Meteo /v1/forecast (daily)",
        }
    except Exception as exc:  # noqa: BLE001
        raise DataFeedError(f"Open-Meteo daily forecast API: {exc}") from exc


# ---------------------------------------------------------------------------
# Shared bounded random-walk helper for the three simulated telemetry feeds
# ---------------------------------------------------------------------------
def _walk(state_key: str, base: float, lo: float, hi: float, step: float,
          spike_chance: float = 0.06, spike_mult: float = 2.5) -> float:
    prev = st.session_state.get(state_key, base)
    delta = random.uniform(-step, step)
    if random.random() < spike_chance:
        delta *= spike_mult
    new_val = min(hi, max(lo, prev + delta))
    st.session_state[state_key] = new_val
    return round(new_val, 2)


# ---------------------------------------------------------------------------
# Module 3 - Metros & Tunnels (simulated LoRaWAN sensor-hub stream)
# ---------------------------------------------------------------------------
def simulate_tunnel_telemetry() -> dict:
    _maybe_simulate_dropout("LoRaWAN Tunnel Sensor Hub")
    return {
        "ambient_temp": _walk("tun_temp", 30.0, 18.0, 42.0, 0.6),
        "geothermal_humidity": _walk("tun_hum", 80.0, 55.0, 100.0, 1.2),
        "pm25": _walk("tun_pm25", 60.0, 10.0, 380.0, 8.0),
        "gas_co_ppm": _walk("tun_co", 12.0, 0.0, 55.0, 1.5),
        "fetched_at": time.strftime("%H:%M:%S"),
        "source": "LoRaWAN Tunnel Sensor Hub (simulated MQTT stream)",
    }


# ---------------------------------------------------------------------------
# Module 4 - High-Rise (simulated crane anemometer / oscillation telemetry)
# ---------------------------------------------------------------------------
def simulate_crane_telemetry(floor_level: int) -> dict:
    _maybe_simulate_dropout("Crane Anemometer / Oscillation Sensor")
    # Altitude shear-stress factor: wind load amplifies with height (power-law
    # style boost), consistent with the physical model already used in
    # risk_engine.calculate_high_rise_kinetic_risk.
    shear_factor = 1.0 + (floor_level / 120.0) * 0.6
    return {
        "ground_wind_speed_knots": _walk("hr_wind", 15.0, 2.0, 55.0, 1.2),
        "crane_load_mass_tons": _walk("hr_load", 4.0, 0.5, 24.0, 0.4),
        "shear_factor": round(shear_factor, 2),
        "fetched_at": time.strftime("%H:%M:%S"),
        "source": "Crane Anemometer & Oscillation Sensors (simulated telemetry)",
    }


# ---------------------------------------------------------------------------
# Module 5 - Data Centers (simulated current transformer / thermal probes)
# ---------------------------------------------------------------------------
def simulate_datacenter_telemetry() -> dict:
    _maybe_simulate_dropout("Current Transformer / Thermal Probe array")
    return {
        "electrical_load_kw": _walk("dc_load", 400.0, 20.0, 1950.0, 25.0),
        "hot_aisle_temp": _walk("dc_temp", 34.0, 20.0, 54.0, 0.5),
        "fetched_at": time.strftime("%H:%M:%S"),
        "source": "Current Transformers & Thermal Probes (simulated telemetry)",
    }


# ---------------------------------------------------------------------------
# Universal weather ingestion (Module 3) - live GPS-driven weather for the
# Field Inspection map and the 3 new modules (Wind Energy, Marine & Port).
#
# Provider chain, in order:
#   1. OpenWeatherMap One Call API, IF a key is supplied (session state,
#      st.secrets, or the api_key parameter) - richer fields (wind gusts,
#      barometric pressure) that Open-Meteo's free tier doesn't expose.
#   2. Open-Meteo (free, keyless) - the same provider already used
#      elsewhere in this file, so a missing/invalid OpenWeatherMap key
#      degrades to a still-real, still-live data source rather than mock
#      data immediately.
#   3. Mock fallback - deterministic-ish illustrative values, clearly
#      labeled as such, so unit tests and offline demos never depend on
#      network access. This is the "include mock fallback data for
#      testing" requirement - it is a fallback path here, not the primary
#      behavior of the app.
#
# Mathematical Isolation rule still applies: this section only ACQUIRES
# numbers, exactly like every other function in this file.
# ---------------------------------------------------------------------------

OPENWEATHERMAP_URL = "https://api.openweathermap.org/data/2.5/onecall"

# New illustrative site coordinates for the 3 new modules, following the
# same "reused where a real live feed already targets that spot" pattern
# as SOLAR_COORDS/OFFSHORE_COORDS. See app.py's SITE_COORDINATES docstring
# for the full honesty note on these being illustrative MVP reference
# points, not real facility locations.
WIND_ENERGY_COORDS = {"lat": 24.9500, "lon": 53.9000}   # onshore/offshore wind corridor, illustrative
MINING_COORDS = {"lat": 24.2000, "lon": 55.7500}        # quarry belt, illustrative
MARINE_PORT_COORDS = {"lat": 25.2700, "lon": 55.3500}   # port construction zone, illustrative


def _mock_universal_weather(lat: float, lon: float) -> dict:
    """Deterministic-ish mock fallback: no network call, no randomness that
    would make a test flaky, but varied enough by coordinate to look
    plausible in a demo. Used only when both the OpenWeatherMap and
    Open-Meteo calls fail (or in explicit offline/test mode)."""
    seed = abs(hash((round(lat, 2), round(lon, 2)))) % 1000
    return {
        "temperature_2m": round(28.0 + (seed % 15), 1),
        "relative_humidity_2m": round(40.0 + (seed % 40), 1),
        "wind_speed_10m_kn": round(5.0 + (seed % 20), 1),
        "wind_gusts_10m_kn": round(8.0 + (seed % 25), 1),
        "uv_index": round((seed % 12), 1),
        "pressure_hpa": round(1008.0 + (seed % 12), 1),
        "fetched_at": time.strftime("%H:%M:%S"),
        "source": "Mock fallback data (no live network reachable)",
    }


def _mock_air_quality(lat: float, lon: float) -> dict:
    """Deterministic-ish mock fallback for ambient PM2.5, following the same
    pattern (and honesty framing) as _mock_universal_weather() above -
    used only when the real Open-Meteo Air Quality API is unreachable."""
    seed = abs(hash((round(lat, 2), round(lon, 2), "aq"))) % 1000
    return {
        "pm2_5_ugm3": round(5.0 + (seed % 60), 1),
        "fetched_at": time.strftime("%H:%M:%S"),
        "source": "Mock fallback data (no live network reachable)",
    }


AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_air_quality_live(lat: float, lon: float, allow_mock_fallback: bool = True) -> dict:
    """
    Real, free, keyless ambient PM2.5 reading (Open-Meteo Air Quality API -
    a different endpoint/service than the weather forecast API used
    elsewhere in this file, but the same provider and the same
    keyless/free-tier pattern). Added for the Australia 'bushfire smoke'
    ambient air-quality feature (regulatory_country_thresholds.py's
    AUSTRALIA profile 'bushfire_smoke_aqi_bands'), but the function itself
    is country-agnostic - any module/country could use a real ambient
    PM2.5 reading.

    Returns {"pm2_5_ugm3": float, "fetched_at": str, "source": str}.
    Falls back to mock data on any failure unless allow_mock_fallback=False
    (in which case it raises DataFeedError), matching
    fetch_live_weather_universal()'s honest fallback pattern.
    """
    try:
        params = {"latitude": lat, "longitude": lon, "current": "pm2_5", "timezone": "auto"}
        resp = requests.get(AIR_QUALITY_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        current = resp.json()["current"]
        return {
            "pm2_5_ugm3": float(current["pm2_5"]),
            "fetched_at": current.get("time"),
            "source": "Open-Meteo Air Quality API",
        }
    except Exception as exc:  # noqa: BLE001
        if allow_mock_fallback:
            return _mock_air_quality(lat, lon)
        raise DataFeedError(f"Open-Meteo Air Quality API: {exc}") from exc


def _fetch_openweathermap(lat: float, lon: float, api_key: str) -> dict:
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
        "exclude": "minutely,hourly,daily,alerts",
    }
    resp = requests.get(OPENWEATHERMAP_URL, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    current = resp.json()["current"]
    wind_ms = float(current.get("wind_speed", 0.0))
    gust_ms = float(current.get("wind_gust", wind_ms))
    return {
        "temperature_2m": float(current["temp"]),
        "relative_humidity_2m": float(current["humidity"]),
        "wind_speed_10m_kn": round(wind_ms * 1.94384, 1),   # m/s -> knots
        "wind_gusts_10m_kn": round(gust_ms * 1.94384, 1),
        "uv_index": float(current.get("uvi", 0.0)),
        "pressure_hpa": float(current.get("pressure", 1013.0)),
        "fetched_at": time.strftime("%H:%M:%S", time.localtime(current.get("dt", time.time()))),
        "source": "OpenWeatherMap One Call API",
    }


def _fetch_open_meteo_universal(lat: float, lon: float) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m,"
                    "uv_index,surface_pressure",
        "wind_speed_unit": "kn",
        "timezone": "auto",
    }
    resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    current = resp.json()["current"]
    return {
        "temperature_2m": float(current["temperature_2m"]),
        "relative_humidity_2m": float(current["relative_humidity_2m"]),
        "wind_speed_10m_kn": float(current["wind_speed_10m"]),
        "wind_gusts_10m_kn": float(current.get("wind_gusts_10m", current["wind_speed_10m"])),
        "uv_index": float(current.get("uv_index", 0.0)),
        "pressure_hpa": float(current.get("surface_pressure", 1013.0)),
        "fetched_at": current.get("time"),
        "source": "Open-Meteo /v1/forecast",
    }


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_live_weather_universal(lat: float, lon: float, api_key: str | None = None,
                                  allow_mock_fallback: bool = True) -> dict:
    """
    GPS-driven weather ingestion with a three-tier provider chain:
    OpenWeatherMap (if api_key given) -> Open-Meteo (free/keyless) -> mock.

    Returns: temperature_2m (C), relative_humidity_2m (%), wind_speed_10m_kn,
    wind_gusts_10m_kn, uv_index, pressure_hpa, fetched_at, source.

    Raises DataFeedError only if allow_mock_fallback=False and every real
    provider fails - callers that want the "mock is a fallback, not a
    silent default" behavior enforced (e.g. a unit test asserting the real
    API path) should pass allow_mock_fallback=False.
    """
    if api_key:
        try:
            return _fetch_openweathermap(lat, lon, api_key)
        except Exception:  # noqa: BLE001 - fall through to next provider
            pass
    try:
        return _fetch_open_meteo_universal(lat, lon)
    except Exception as exc:  # noqa: BLE001
        if allow_mock_fallback:
            return _mock_universal_weather(lat, lon)
        raise DataFeedError(f"All live weather providers failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Reverse geocoding: GPS coordinates -> regulatory country code
# ---------------------------------------------------------------------------
# Auto-detects which regulatory_country_thresholds.py profile applies to a
# live GPS fix, so the Field Inspection section's country selector can
# default to "wherever the phone actually is" instead of always requiring
# a manual pick.
#
# Two-tier fallback, same honest pattern as fetch_live_weather_universal():
#   1. Nominatim (OpenStreetMap) reverse geocoding - a real, free, keyless
#      API. Its usage policy requires a descriptive User-Agent header and
#      a max of ~1 request/second for the public instance, both honored
#      below. This will be blocked in some restricted network sandboxes
#      (exactly like Open-Meteo is elsewhere in this file) but works from
#      a normal deployment with outbound internet access.
#   2. A tiny offline bounding-box lookup covering only the 3 baseline
#      countries this app ships regulatory profiles for. This is
#      deliberately approximate (rectangular boxes overlap real borders in
#      places) and documented as such - it exists so country detection
#      never hard-fails, not as a substitute for a real geocoder. Extend
#      COUNTRY_BOUNDING_BOXES with more entries as regulatory_country_
#      thresholds.py gains more country profiles.
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_USER_AGENT = "MAKU-HSE-Platform/1.0 (construction-site-risk-assessment MVP)"

# Rough bounding boxes (min_lat, max_lat, min_lon, max_lon) for every
# regulatory_country_thresholds.py profile that has one registered.
# Deliberately coarse - see docstring above.
COUNTRY_BOUNDING_BOXES = {
    "USA": (24.0, 49.5, -125.0, -66.0),
    "FRANCE": (41.0, 51.1, -5.5, 9.7),
    "UAE": (22.5, 26.5, 51.0, 56.5),
    "UK": (49.8, 60.9, -8.7, 1.8),
    "CANADA": (41.6, 83.1, -141.0, -52.6),
    "AUSTRALIA": (-43.7, -10.0, 112.9, 153.7),
}

_NOMINATIM_COUNTRY_CODE_MAP = {
    "us": "USA", "fr": "FRANCE", "ae": "UAE",
    "gb": "UK", "ca": "CANADA", "au": "AUSTRALIA",
}


def _bounding_box_country_lookup(lat: float, lon: float) -> str | None:
    for country_code, (min_lat, max_lat, min_lon, max_lon) in COUNTRY_BOUNDING_BOXES.items():
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return country_code
    return None


def _fetch_nominatim_country(lat: float, lon: float) -> tuple[str | None, bool]:
    """Returns (regulatory_country_thresholds.py country code or None,
    resolved_real_country: bool). resolved_real_country is True whenever
    Nominatim successfully identified SOME real-world country - even one
    MAKU has no profile for yet - which lets reverse_geocode_country()
    distinguish 'genuinely could not geocode this position' from
    'geocoded fine, just not a registered jurisdiction' (the latter should
    trigger the GLOBAL fallback + warning toast, not a silent no-op)."""
    params = {"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 3}
    resp = requests.get(
        NOMINATIM_URL, params=params, timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": NOMINATIM_USER_AGENT},
    )
    resp.raise_for_status()
    data = resp.json()
    iso2 = (data.get("address", {}).get("country_code") or "").lower()
    return _NOMINATIM_COUNTRY_CODE_MAP.get(iso2), bool(iso2)


@st.cache_data(ttl=FORECAST_CACHE_TTL_SECONDS, show_spinner=False)
def reverse_geocode_country(lat: float, lon: float) -> dict:
    """
    Resolves a GPS fix to a regulatory_country_thresholds.py country code.

    Returns {"country_code": str | None, "source": str, "note": str,
    "used_fallback": bool}.

    Three outcomes:
      1. A registered jurisdiction (USA/FRANCE/UAE/UK/CANADA/AUSTRALIA) -
         country_code is that code, used_fallback is False.
      2. A real, successfully-geocoded country that simply has no
         registered profile yet (e.g. a site in Germany) - country_code is
         regulatory_country_thresholds.FALLBACK_COUNTRY_CODE ("GLOBAL"),
         used_fallback is True, and note carries the exact
         FALLBACK_WARNING_MESSAGE the UI should show as a toast:
         "Local legislation profile not found. Falling back to Global
         ACGIH/OSHA reference guidelines."
      3. Geocoding itself failed entirely (network unreachable, and the
         offline bounding-box fallback also missed) - country_code is
         None, used_fallback is False. Callers should treat this as "keep
         whatever country the user last selected manually", not as an
         error.
    """
    try:
        code, resolved_real_country = _fetch_nominatim_country(lat, lon)
        if code:
            return {
                "country_code": code, "source": "Nominatim (OpenStreetMap) reverse geocoding",
                "note": "", "used_fallback": False,
            }
        if resolved_real_country:
            return {
                "country_code": FALLBACK_COUNTRY_CODE,
                "source": "Nominatim (OpenStreetMap) reverse geocoding",
                "note": FALLBACK_WARNING_MESSAGE, "used_fallback": True,
            }
        return {
            "country_code": None, "source": "Nominatim (OpenStreetMap) reverse geocoding",
            "note": "Could not resolve a country for this position.", "used_fallback": False,
        }
    except Exception:  # noqa: BLE001 - fall through to offline bounding-box fallback
        code = _bounding_box_country_lookup(lat, lon)
        return {
            "country_code": code,
            "source": "Offline bounding-box fallback (Nominatim unreachable)",
            "note": "Approximate - rectangular boxes, not real border polygons." if code else
                    "Position falls outside all registered country bounding boxes.",
            "used_fallback": False,
        }
