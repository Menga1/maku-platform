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
