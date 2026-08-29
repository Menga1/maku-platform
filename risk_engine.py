"""
MAKU Risk Engine
================
Rule-based, formula-driven risk calculations for five construction
environments. Every formula here is a recognized/adapted industry method
(WBGT approximation, Humidex, ACGIH TLV heat-stress action limits, OEL
exceedance logic, wind power-law profiles, the Lee open-air arc-flash
equation) so outputs are transparent and auditable - not a black box.
This is the "AI" reasoning layer's foundation; the LLM layer (see
ai_advisor.py) sits on top of these numbers to explain results and
suggest controls in plain language.

NOTE ON DATA: all environmental inputs (GHI, humidity, sea state, OEL
readings, wind telemetry, electrical load, etc.) are entered by the user
or simulated via sliders in this MVP. In production these fields would be
wired to live satellite/GIS, buoy telemetry, underground sensor networks,
building anemometers/BIM, and rack-level IoT - the architecture below is
built so that swap is a data-source change only, not a logic change.
"""

from __future__ import annotations

import math

from regulatory_country_thresholds import get_regulatory_profile

# The harmonized default profile used whenever a caller doesn't supply
# regulatory_profile explicitly. Deliberately USA, since regulatory_country_
# thresholds.py's USA entry was designed to exactly match every number this
# file used to hardcode before this refactor - so every pre-existing call
# site and every existing test keeps producing identical results with zero
# changes required at the call site.
_DEFAULT_REGULATORY_PROFILE = get_regulatory_profile("USA")


def _resolve_profile(regulatory_profile: dict | None) -> dict:
    """Every calculate_*_kinetic_risk() function below funnels its incoming
    regulatory_profile argument through this so 'not supplied' and
    'explicitly None' both mean exactly the same thing: fall back to the
    harmonized USA default, never crash on a missing profile."""
    return regulatory_profile if regulatory_profile is not None else _DEFAULT_REGULATORY_PROFILE


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def vapor_pressure_hpa(temp_c: float, rh_pct: float) -> float:
    """Saturation-based actual vapor pressure (hPa) from dry-bulb temp and RH."""
    saturation = 6.105 * math.exp((17.27 * temp_c) / (237.7 + temp_c))
    return (rh_pct / 100.0) * saturation


def wbgt_outdoor_approx(temp_c: float, rh_pct: float) -> float:
    """
    Approximated outdoor WBGT (Australian Bureau of Meteorology method)
    when no direct wet-bulb/globe thermometer reading is available.
    WBGT = 0.567*Ta + 0.393*e + 3.94
    """
    e = vapor_pressure_hpa(temp_c, rh_pct)
    return 0.567 * temp_c + 0.393 * e + 3.94


def humidex(temp_c: float, rh_pct: float) -> float:
    """Environment Canada Humidex formula."""
    e = vapor_pressure_hpa(temp_c, rh_pct)
    return temp_c + 0.5555 * (e - 10.0)


# ---------------------------------------------------------------------------
# Global-expansion shared helpers: Humidex classification (Canada heat
# cutoff), Wind Chill (Canada cold stress), UV Index and bushfire-smoke
# PM2.5 classification (Australia). All additive, pure functions - no
# existing function's signature or behavior changes. Every classification
# function below reuses the same risk_band() ascending-threshold helper
# already used throughout this file, rather than inventing a second pattern.
# ---------------------------------------------------------------------------

HUMIDEX_BANDS = [
    (29.9, "Little to no discomfort"),
    (39.9, "Some discomfort"),
    (44.9, "Great discomfort - avoid exertion"),
    (53.9, "Dangerous - heat stroke possible"),
    (999.0, "Heat stroke imminent"),
]


def classify_humidex(value: float) -> str:
    """Environment Canada's published Humidex comfort/danger categories.
    45 (the top of the 'Dangerous' band) is Canada's critical safety
    cutoff - see regulatory_country_thresholds.REGULATORY_PROFILES['CANADA']."""
    return risk_band(value, HUMIDEX_BANDS)


def wind_chill_c(temp_c: float, wind_speed_kmh: float) -> float:
    """
    Environment and Climate Change Canada Wind Chill Index.
    WCI = 13.12 + 0.6215*T - 11.37*V^0.16 + 0.3965*T*V^0.16
    Valid for T <= 10 degC and wind_speed_kmh > 4.8 km/h - outside that
    domain the formula is not meaningful (no material wind-chill effect
    above 10C, or in near-still air), so this returns temp_c unchanged
    rather than extrapolating the formula outside its validated range.
    """
    if temp_c > 10.0 or wind_speed_kmh <= 4.8:
        return round(temp_c, 1)
    v16 = wind_speed_kmh ** 0.16
    return round(13.12 + 0.6215 * temp_c - 11.37 * v16 + 0.3965 * temp_c * v16, 1)


# Severity is expressed as -wind_chill_c (so "more negative wind chill" maps
# to "higher severity score"), letting this reuse risk_band()'s ascending-
# threshold convention directly instead of a separate descending-order helper.
WIND_CHILL_SEVERITY_BANDS = [
    (9.0, "Low risk"),
    (27.0, "Moderate risk - frostbite possible in 10-30 min"),
    (39.0, "High risk - frostbite possible in 5-10 min"),
    (47.0, "Very high risk - frostbite possible in 2-5 min"),
    (54.0, "Severe risk - frostbite possible in under 2 min"),
    (9999.0, "Extreme danger - exposed skin can freeze almost instantly"),
]


def classify_wind_chill(wind_chill_value_c: float) -> str:
    """Environment Canada's published Wind Chill Index hazard categories."""
    return risk_band(-wind_chill_value_c, WIND_CHILL_SEVERITY_BANDS)


def classify_uv_index(uv_index: float, uv_index_bands: list) -> str:
    """Classifies a UV Index reading against a country profile's
    uv_index_bands (e.g. regulatory_country_thresholds's Australia
    'uv_heat' config - Bureau of Meteorology / SunSmart scale). Bands are
    supplied by the caller (never hardcoded here) so this stays a generic,
    reusable classifier rather than an Australia-specific formula."""
    return risk_band(uv_index, uv_index_bands)


def classify_bushfire_smoke_pm25(pm25_ugm3: float, bushfire_smoke_aqi_bands: list) -> str:
    """Classifies an ambient PM2.5 reading against a country profile's
    bushfire_smoke_aqi_bands (e.g. Australia's illustrative AQI-category
    mapping). Bands are supplied by the caller, never hardcoded here."""
    return risk_band(pm25_ugm3, bushfire_smoke_aqi_bands)


ACGIH_WBGT_LIMITS = {
    # work_rate: (100% work, 75/25, 50/50, 25/75) WBGT deg C action limits, unacclimatized worker
    "light": [29.5, 30.5, 31.5, 32.5],
    "moderate": [27.5, 28.5, 29.5, 31.0],
    "heavy": [26.0, 27.5, 29.0, 30.5],
}


def acgih_action_level(wbgt: float, work_rate: str, work_rest_ratio: str) -> dict:
    """
    Compare WBGT against ACGIH TLV action limits for unacclimatized workers.
    work_rest_ratio in {"100/0", "75/25", "50/50", "25/75"}
    Returns exceedance flag and margin.
    """
    idx_map = {"100/0": 0, "75/25": 1, "50/50": 2, "25/75": 3}
    idx = idx_map.get(work_rest_ratio, 0)
    limit = ACGIH_WBGT_LIMITS[work_rate][idx]
    return {
        "limit": limit,
        "exceeds": wbgt > limit,
        "margin": round(wbgt - limit, 1),
    }


def risk_band(score: float, bands: list) -> str:
    """bands = [(threshold, label), ...] ascending; returns first matching label."""
    for threshold, label in bands:
        if score <= threshold:
            return label
    return bands[-1][1]


# ---------------------------------------------------------------------------
# Module 1: Utility-Scale Solar Farms (Desert)
# ---------------------------------------------------------------------------

# Standardized reflection factors (albedo). Sand reflects ~30% of incoming
# heat; silicon PV panels absorb more but re-radiate intense heat back at
# close range; the hybrid assembly zone mixes both plus metal MEP structures.
SOLAR_ALBEDO_FACTORS = {
    "pure_desert_sand": 0.30,
    "silicon_pv_panels": 0.15,
    "hybrid_assembly_zone": 0.25,
}


def calculate_solar_albedo_heat_risk(ghi: float, uv_index: float, ambient_temp: float, surface_type: str,
                                      regulatory_profile: dict | None = None) -> dict:
    """
    Computes local thermal accumulation driven by the albedo effect and
    returns the kinetic risk index for Solar (Desert) MEP crews.

    regulatory_profile: accepted for interface consistency with every other
    calculate_*_kinetic_risk() function and tagged onto the result so the
    UI can state which regulatory framework was active, but this module's
    own perceived-temperature bands are NOT country-varying - they're a
    custom GHI/albedo/UV formula unique to this module, not a WBGT/Humidex
    calculation with documented per-country divergence. See this app's
    ACGIH TLV Reference Panel (risk_engine.resolve_heat_stress_limit) for
    the genuinely workload/country-driven heat-stress cross-check.
    Ref: MAKU Project Concept - Module 1 (Desert Environment)
    """
    profile = _resolve_profile(regulatory_profile)
    albedo = SOLAR_ALBEDO_FACTORS.get(surface_type, 0.25)

    # Simplified predictive equation for local (induced-microclimate) thermal
    # accumulation: GHI and albedo amplify the perceived ground-level temperature.
    thermal_amplification = (ghi * albedo) / 100.0
    perceived_thermal_temp = ambient_temp + thermal_amplification + (uv_index * 0.5)

    # Risk level + OEL (Occupational Exposure Limit) safety margin
    if perceived_thermal_temp >= 45.0 or uv_index >= 11:
        risk_level = "CRITICAL"
        band = "Extreme"
        color = "red"
        max_shift_duration = "15 minutes per hour"
        override_required = True
    elif perceived_thermal_temp >= 38.0 or uv_index >= 8:
        risk_level = "HIGH"
        band = "High"
        color = "orange"
        max_shift_duration = "30 minutes per hour"
        override_required = False
    elif perceived_thermal_temp >= 32.0:
        risk_level = "MODERATE"
        band = "Moderate"
        color = "yellow"
        max_shift_duration = "45 minutes per hour"
        override_required = False
    else:
        risk_level = "LOW"
        band = "Low"
        color = "green"
        max_shift_duration = "Continuous operations"
        override_required = False

    return {
        "module": "Solar (Desert)",
        "perceived_temp": round(perceived_thermal_temp, 1),
        "thermal_amplification": round(thermal_amplification, 1),
        "risk_level": risk_level,
        "risk_band": band,  # compatibility field for ai_advisor.solar_controls / generate_narrative
        "color": color,
        "max_shift_duration": max_shift_duration,
        "override_required": override_required,
        "safety_override": override_required,
        "primary_hazard": "Acute heat stroke / UV-driven heat exhaustion - MEP tracker & module assembly crews",
        "regulatory_country_code": profile["country_code"],
        "regulatory_profile_label": profile["label"],
        "drivers": {
            "GHI (W/m2)": ghi,
            "UV index": uv_index,
            "Surface type": surface_type,
            "Albedo factor applied": albedo,
        },
    }


# ---------------------------------------------------------------------------
# Module 2: Offshore Oil & Gas (Marine)
# ---------------------------------------------------------------------------

OFFSHORE_WIND_SUSPEND_KNOTS = 25.0   # suspend crane/lifting operations
OFFSHORE_WIND_RESTRICT_KNOTS = 18.0  # restrict lifting, monitor closely

OFFSHORE_HUMIDEX_BANDS = [
    (29, "Low"), (35, "Moderate"), (40, "High"), (999, "Extreme"),
]


def calculate_marine_humidex_risk(ambient_temp: float, relative_humidity: float, wind_speed: float,
                                   regulatory_profile: dict | None = None) -> dict:
    """
    Computes the Marine Humidex heat-stress index (Environment Canada Humidex
    formula, built on the shared saturation-vapor-pressure helper) and
    cross-references it against offshore wind-gust kinetic risk thresholds
    for crane/lifting operations on exposed platforms/lay-barges.

    regulatory_profile: accepted for interface consistency and tagged onto
    the result; the Humidex bands and wind-gate thresholds here are NOT
    country-varying (Humidex is a public comfort index without documented
    per-country occupational divergence, and offshore wind-gate limits are
    OEM/vessel-specific in all three baseline jurisdictions).
    Ref: MAKU Project Concept - Module 2 (Marine Environment)

    wind_speed is expected in knots.
    """
    profile = _resolve_profile(regulatory_profile)
    hmdx = humidex(ambient_temp, relative_humidity)
    band = risk_band(hmdx, OFFSHORE_HUMIDEX_BANDS)

    # Operational wind-gust gating, independent of thermal risk - marine ops limits
    if wind_speed >= OFFSHORE_WIND_SUSPEND_KNOTS:
        wind_risk_status = "Suspended - Crane/Lifting Danger"
    elif wind_speed >= OFFSHORE_WIND_RESTRICT_KNOTS:
        wind_risk_status = "Restricted - Monitor Closely"
    else:
        wind_risk_status = "Normal Operations"

    safety_override = band == "Extreme" or wind_risk_status.startswith("Suspended")

    return {
        "module": "Offshore (Marine)",
        "humidex": round(hmdx, 1),
        "wind_risk_status": wind_risk_status,
        "risk_band": band,  # compatibility field for ai_advisor.offshore_controls / generate_narrative
        "safety_override": safety_override,
        "primary_hazard": "Heat retention / thermal stress + wind-driven crane/lifting risk - "
                           "welding, pipe-fitting, scaffolding crews",
        "regulatory_country_code": profile["country_code"],
        "regulatory_profile_label": profile["label"],
        "drivers": {
            "Ambient temperature (C)": ambient_temp,
            "Relative humidity (%)": relative_humidity,
            "Wind speed (knots)": wind_speed,
        },
    }


# ---------------------------------------------------------------------------
# Module 3: Metros & Tunnels (Underground)
# ---------------------------------------------------------------------------

UNDERGROUND_PERCEIVED_TEMP_OVERRIDE_C = 42.0  # forces safety override above this perceived temp

# Backward-compatible module-level constants - equal to the harmonized USA
# default profile's air_quality values, kept as named constants since other
# code/tests may still reference them directly.
PM25_OEL_LIMIT_UGM3 = _DEFAULT_REGULATORY_PROFILE["air_quality"]["pm25_oel_ugm3"]
CO_OEL_LIMIT_PPM = _DEFAULT_REGULATORY_PROFILE["air_quality"]["co_oel_ppm"]

UNDERGROUND_HEAT_BANDS = [
    (32, "LOW"), (38, "MODERATE"), (42, "HIGH"), (999, "CRITICAL"),
]
UNDERGROUND_SEVERITY_RANK = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


def _oel_scaled_bands(oel_limit: float, low_ratio: float, moderate_ratio: float) -> list:
    """Builds a [LOW, MODERATE, HIGH, CRITICAL] risk_band() table proportional
    to a country's actual OEL limit, preserving the same ratio structure this
    module always used (HIGH boundary sits exactly at the OEL limit; LOW/
    MODERATE sit at the same fractions of it that were hardcoded before this
    refactor) - so a profile with the harmonized default OEL reproduces the
    exact same band edges as before, and a future country with a genuinely
    different OEL scales proportionally instead of needing new magic numbers."""
    return [
        (oel_limit * low_ratio, "LOW"),
        (oel_limit * moderate_ratio, "MODERATE"),
        (oel_limit, "HIGH"),
        (oel_limit * 1e6, "CRITICAL"),
    ]


def calculate_underground_kinetic_risk(ambient_temp: float, geothermal_humidity: float,
                                        particulate_matter_pm25: float, gas_co_ppm: float,
                                        regulatory_profile: dict | None = None) -> dict:
    """
    Models trapped-heat accumulation in enclosed tunnel/metro excavation faces
    (TBM heat emissions + near-saturated geothermal humidity, screened via the
    shared Humidex helper) alongside real-time OEL (Occupational Exposure
    Limit) checks for CO and PM2.5, generating a predictive safety override
    for MEP electrical crews pulling high-voltage cabling ahead of permanent
    ventilation commissioning.

    regulatory_profile: a dict from regulatory_country_thresholds.
    get_regulatory_profile(country_code), or None to use the harmonized USA
    default (see that module's honesty note on why PM2.5/CO OEL don't
    actually diverge by country in published guidance for any of the 3
    baseline jurisdictions - the parameter exists so a future country WITH
    a genuinely documented different OEL can be added without touching this
    function's code).
    Ref: MAKU Project Concept - Module 3 (Underground Substructure Infrastructure)
    """
    profile = _resolve_profile(regulatory_profile)
    pm25_oel = profile["air_quality"]["pm25_oel_ugm3"]
    co_oel = profile["air_quality"]["co_oel_ppm"]

    # Trapped-heat + geothermal-humidity perceived temperature. Stagnant,
    # near-saturated tunnel air behaves like a Humidex problem rather than a
    # dry desert WBGT one, so this reuses the same helper as the marine module.
    perceived_temp = humidex(ambient_temp, geothermal_humidity)

    heat_band = risk_band(perceived_temp, UNDERGROUND_HEAT_BANDS)
    pm25_band = risk_band(particulate_matter_pm25, _oel_scaled_bands(pm25_oel, 0.14, 0.6))
    co_band = risk_band(gas_co_ppm, _oel_scaled_bands(co_oel, 0.36, 0.6))

    gas_exceeds = gas_co_ppm > co_oel
    dust_exceeds = particulate_matter_pm25 > pm25_oel

    band = max((heat_band, pm25_band, co_band), key=lambda b: UNDERGROUND_SEVERITY_RANK[b])

    safety_override = gas_exceeds or dust_exceeds or perceived_temp > UNDERGROUND_PERCEIVED_TEMP_OVERRIDE_C
    if safety_override:
        band = "CRITICAL"

    return {
        "module": "Underground (Tunnel/Metro)",
        "perceived_temp": round(perceived_temp, 1),
        "gas_exceeds": gas_exceeds,
        "dust_exceeds": dust_exceeds,
        "risk_band": band,  # compatibility field for ai_advisor.underground_controls / generate_narrative
        "safety_override": safety_override,
        "primary_hazard": "Heat stress + air-quality (CO/PM2.5) exposure - MEP electrical crews "
                           "pulling high-voltage cabling pre-ventilation commissioning",
        "regulatory_country_code": profile["country_code"],
        "regulatory_profile_label": profile["label"],
        "drivers": {
            "Ambient temperature (C)": ambient_temp,
            "Geothermal humidity (%)": geothermal_humidity,
            "PM2.5 (ug/m3)": particulate_matter_pm25,
            "CO (ppm)": gas_co_ppm,
        },
    }


# ---------------------------------------------------------------------------
# Module 4: High-Rise Building Construction (Vertical Urban)
# ---------------------------------------------------------------------------

HIGH_RISE_WIND_GROWTH_RATE = 0.008  # exponential per-floor amplification constant (urban boundary layer)

# Backward-compatible module-level constant - equal to the harmonized USA
# default profile's wind_shear.crane_suspend_knots value.
CRANE_SUSPEND_WIND_KNOTS = _DEFAULT_REGULATORY_PROFILE["wind_shear"]["crane_suspend_knots"]

OSCILLATION_SEVERITY_BANDS = [
    (10, "LOW"), (25, "MODERATE"), (50, "HIGH"), (999999, "CRITICAL"),
]
HIGH_RISE_SEVERITY_RANK = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


def _crane_wind_bands(suspend_knots: float, restrict_knots: float) -> list:
    """Builds the [LOW, MODERATE, HIGH, CRITICAL] wind-severity table from a
    profile's two named crane thresholds - restrict_knots becomes the
    MODERATE/HIGH boundary and suspend_knots becomes the HIGH/CRITICAL
    boundary, with LOW set at half the suspend threshold (same 15/30 = 0.5
    ratio this module always used)."""
    return [
        (suspend_knots * 0.5, "LOW"),
        (restrict_knots, "MODERATE"),
        (suspend_knots, "HIGH"),
        (suspend_knots * 1e6, "CRITICAL"),
    ]


def calculate_high_rise_kinetic_risk(ground_wind_speed_knots: float, floor_level: float,
                                      crane_load_mass_tons: float,
                                      regulatory_profile: dict | None = None) -> dict:
    """
    Models vertical wind-shear amplification through the urban boundary layer
    and the resulting crane-load oscillation risk for suspended lifts and
    facade/curtain-wall crews working at height.

    regulatory_profile: a dict from regulatory_country_thresholds.
    get_regulatory_profile(country_code), or None to use the harmonized USA
    default. See that module's honesty note - no country in the 3 baseline
    jurisdictions has a single fixed statutory crane wind-speed number in
    law; France's modestly more conservative default here reflects common
    EN 13000 equipment practice (automatic anemometer cutouts), not a
    specific cited regulation.
    Ref: MAKU Project Concept - Module 4 (Vertical Urban Environment)
    """
    profile = _resolve_profile(regulatory_profile)
    suspend_knots = profile["wind_shear"]["crane_suspend_knots"]
    restrict_knots = profile["wind_shear"]["crane_restrict_knots"]

    # Exponential wind-shear scaling: wind speed compounds with floor height
    # as the urban boundary layer thins and turbulence/shear intensify.
    scaled_wind_speed = ground_wind_speed_knots * math.exp(HIGH_RISE_WIND_GROWTH_RATE * floor_level)

    # Oscillation risk index: drag energy (~v^2) divided by load mass - lighter,
    # high-surface-area facade/curtain-wall loads oscillate far worse than dense
    # heavy structural loads under the same wind loading.
    safe_mass = max(crane_load_mass_tons, 0.5)
    oscillation_index = (scaled_wind_speed ** 2) / safe_mass

    wind_band = risk_band(scaled_wind_speed, _crane_wind_bands(suspend_knots, restrict_knots))
    oscillation_band = risk_band(oscillation_index, OSCILLATION_SEVERITY_BANDS)
    band = wind_band if HIGH_RISE_SEVERITY_RANK[wind_band] >= HIGH_RISE_SEVERITY_RANK[oscillation_band] else oscillation_band

    safety_override = scaled_wind_speed > suspend_knots
    if safety_override:
        band = "CRITICAL"

    return {
        "module": "High-Rise (Vertical Urban)",
        "scaled_wind_speed": round(scaled_wind_speed, 1),
        "oscillation_index": round(oscillation_index, 1),
        "risk_band": band,  # compatibility field for ai_advisor.high_rise_controls / generate_narrative
        "safety_override": safety_override,
        "primary_hazard": "Wind-shear-driven crane load-swing and fall-from-height risk - "
                           "MEP riser & external-wall crews",
        "regulatory_country_code": profile["country_code"],
        "regulatory_profile_label": profile["label"],
        "drivers": {
            "Ground wind speed (knots)": ground_wind_speed_knots,
            "Floor level": floor_level,
            "Crane load mass (tons)": crane_load_mass_tons,
        },
    }


# ---------------------------------------------------------------------------
# Module 5: Data Center Construction & Commissioning (Controlled Critical
# Environment)
# ---------------------------------------------------------------------------

ARC_FLASH_PPE = [
    (1.2, "Category 1"),
    (8.0, "Category 2"),
    (25.0, "Category 3"),
    (40.0, "Category 4"),
    (float("inf"), "DANGER - exceeds max PPE rating, de-energize / no-go"),
]


def lee_arc_flash_incident_energy(voltage_kv: float, fault_current_ka: float,
                                   clearing_time_s: float, working_distance_mm: float) -> float:
    """
    Ralph Lee open-air arc-flash incident-energy approximation (a widely
    published, order-of-magnitude method used for early-stage/illustrative
    hazard screening - not a substitute for a full IEEE 1584 arc-flash
    study before live work is authorized):
        IE = 2.142e3 * V(kV) * Isc(kA) * t(s) / D(mm)^2   [cal/cm^2]

    Kept as the full voltage/fault-current/clearing-time/working-distance
    reference implementation. calculate_datacenter_kinetic_risk() below uses
    a simplified load-only variant per the current module spec (only
    electrical_load_kw is collected from the UI); this function/PPE mapping
    remain available if those individual switchgear parameters are wired in
    later.
    """
    working_distance_mm = max(working_distance_mm, 1.0)
    return 2.142e3 * voltage_kv * fault_current_ka * clearing_time_s / (working_distance_mm ** 2)


def arc_flash_ppe_category(incident_energy_cal_cm2: float) -> str:
    return risk_band(incident_energy_cal_cm2, ARC_FLASH_PPE)


DATACENTER_ARC_FLASH_DANGER_CAL = 40.0  # incident energy above which no PPE category permits live work
DATACENTER_THERMAL_DIFF_CRITICAL_C = 25.0  # hot/cold-aisle delta considered critical for commissioning crews
DATACENTER_HOT_AISLE_CRITICAL_C = 45.0     # hot-aisle temp considered critical on its own

DATACENTER_ARC_FLASH_BANDS = [
    (4, "LOW"), (8, "MODERATE"), (25, "HIGH"), (999999, "CRITICAL"),
]
DATACENTER_THERMAL_BANDS = [
    (8, "LOW"), (15, "MODERATE"), (25, "HIGH"), (999, "CRITICAL"),
]
DATACENTER_SEVERITY_RANK = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


def calculate_datacenter_kinetic_risk(electrical_load_kw: float, hot_aisle_temp: float,
                                       ceiling_void_confined: bool, gas_system_armed: bool,
                                       regulatory_profile: dict | None = None) -> dict:
    """
    Evaluates electrical (arc-flash) and thermal (hot-aisle/cold-aisle) risk
    for MEP electrical, mechanical, and fire-suppression commissioning crews
    in a live/energizing data center. Arc-flash incident energy scales
    sharply with electrical load - a simplified, load-driven variant of the
    Ralph Lee open-air arc-flash approximation used elsewhere in this engine
    (see lee_arc_flash_incident_energy for the full voltage/Isc/time/distance
    form used when those parameters are known individually).
    Ref: MAKU Project Concept - Module 5 (Controlled Critical Environment)
    """
    profile = _resolve_profile(regulatory_profile)
    # Simplified load-driven arc-flash incident-energy scaling: incident
    # energy grows with the square of electrical load, reflecting how fault
    # current/available energy compounds as switchgear capacity increases.
    # (2.5 cal/cm2 per (100 kW)^2 is a tuned illustrative coefficient, not a
    # measured constant - documented here as an MVP assumption.)
    arc_flash_energy_cal = 2.5 * (electrical_load_kw / 100.0) ** 2

    # Standard cold-aisle containment target is assumed ~22 degC; the thermal
    # differential is what matters for commissioning crews moving between
    # aisles, not the absolute hot-aisle reading alone.
    assumed_cold_aisle_c = 22.0
    thermal_differential = round(hot_aisle_temp - assumed_cold_aisle_c, 1)

    arc_flash_band = risk_band(arc_flash_energy_cal, DATACENTER_ARC_FLASH_BANDS)
    thermal_band = risk_band(thermal_differential, DATACENTER_THERMAL_BANDS)
    band = max((arc_flash_band, thermal_band), key=lambda b: DATACENTER_SEVERITY_RANK[b])

    arc_flash_danger = arc_flash_energy_cal > DATACENTER_ARC_FLASH_DANGER_CAL
    thermal_critical = (
        thermal_differential >= DATACENTER_THERMAL_DIFF_CRITICAL_C
        or hot_aisle_temp >= DATACENTER_HOT_AISLE_CRITICAL_C
    )
    # Crews inside a confined/pressurized ceiling-void space while a gaseous
    # clean-agent suppression system is armed risk accidental discharge and
    # asphyxiation - an automatic safety override regardless of thermal/arc state.
    confined_armed_danger = ceiling_void_confined and gas_system_armed

    safety_override = arc_flash_danger or confined_armed_danger or thermal_critical
    if safety_override:
        band = "CRITICAL"

    return {
        "module": "Data Center (Controlled Critical Environment)",
        "arc_flash_energy_cal": round(arc_flash_energy_cal, 1),
        "thermal_differential": thermal_differential,
        "risk_band": band,  # compatibility field for ai_advisor.data_center_controls / generate_narrative
        "safety_override": safety_override,
        "arc_flash_danger": arc_flash_danger,
        "confined_armed_danger": confined_armed_danger,
        "ceiling_void_confined": ceiling_void_confined,
        "gas_system_armed": gas_system_armed,
        "primary_hazard": "Arc-flash incident energy + hot/cold-aisle thermal stress + confined-space "
                           "clean-agent risk - MEP electrical/mechanical/fire-suppression commissioning crews",
        "regulatory_country_code": profile["country_code"],
        "regulatory_profile_label": profile["label"],
        "drivers": {
            "Electrical load (kW)": electrical_load_kw,
            "Hot-aisle temperature (C)": hot_aisle_temp,
            "Assumed cold-aisle target (C)": assumed_cold_aisle_c,
            "Confined ceiling-void space": ceiling_void_confined,
            "Gaseous suppression system armed": gas_system_armed,
        },
    }


# ---------------------------------------------------------------------------
# Module 6: Wind Energy (Onshore/Offshore)
# ---------------------------------------------------------------------------
# Three independent gating checks, each drawn from a real, named industry
# practice rather than an invented number:
#   1. Working-at-height wind speed thresholds - modeled on Global Wind
#      Organisation (GWO) Basic Safety Training guidance and typical OEM
#      turbine O&M manuals, which commonly gate nacelle/blade access work
#      in three bands. Exact OEM limits vary by turbine model - these are
#      representative, illustrative thresholds, not a specific OEM's figures.
#   2. Lightning risk - the NOAA/OSHA "30-30 rule": if the flash-to-bang
#      interval is under 30 seconds (~10 km away, sound travels ~343 m/s),
#      suspend outdoor work immediately; wait 30 minutes after the last
#      strike before resuming. This is a real, citable public-safety rule,
#      not an MAKU invention.
#   3. Sea-state gating for offshore crew-transfer vessels (CTVs) - Hs
#      (significant wave height) thresholds representative of typical
#      CTV-class personnel-transfer limits used in offshore wind O&M.
#      Specific vessel/gangway systems (e.g. motion-compensated gangways)
#      tolerate higher Hs - these are conservative, illustrative defaults.

WIND_TURBINE_HEIGHT_SUSPEND_MS = 20.0    # m/s at hub height - suspend all blade/nacelle access work
WIND_TURBINE_HEIGHT_RESTRICT_MS = 14.0   # m/s - restrict to essential tasks only, enhanced fall-arrest checks
LIGHTNING_FLASH_TO_BANG_STOP_SEC = 30.0  # NOAA/OSHA 30-30 rule stop-work threshold
LIGHTNING_RESUME_WAIT_MIN = 30.0         # minutes to wait after last strike before resuming
CTV_TRANSFER_SUSPEND_HS_M = 2.0          # significant wave height (m) - suspend all personnel transfer
CTV_TRANSFER_RESTRICT_HS_M = 1.5         # significant wave height (m) - restrict to essential transfers

WIND_ENERGY_SEVERITY_RANK = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


def lightning_risk_status(flash_to_bang_sec: float | None) -> str:
    """Applies the NOAA/OSHA 30-30 rule. flash_to_bang_sec=None means no
    thunder/lightning currently observed."""
    if flash_to_bang_sec is None:
        return "No lightning activity observed"
    if flash_to_bang_sec <= LIGHTNING_FLASH_TO_BANG_STOP_SEC:
        return f"STOP WORK - flash-to-bang {flash_to_bang_sec:.0f}s (30-30 rule triggered)"
    return f"Monitoring - flash-to-bang {flash_to_bang_sec:.0f}s (above 30s threshold)"


def calculate_wind_energy_kinetic_risk(
    hub_height_wind_speed_ms: float,
    is_offshore: bool = False,
    significant_wave_height_m: float = 0.0,
    flash_to_bang_sec: float | None = None,
    regulatory_profile: dict | None = None,
) -> dict:
    """
    Gates turbine working-at-height access against hub-height wind speed,
    screens active lightning risk via the 30-30 rule, and (offshore only)
    gates crew-transfer-vessel personnel transfer against sea state.

    regulatory_profile: accepted for interface consistency and tagged onto
    the result. Turbine hub-height access wind limits follow GWO's
    internationally harmonized Basic Safety Training guidance (not a
    national statute in any of the 3 baseline jurisdictions), and the
    30-30 lightning rule is itself an international public-safety
    convention - genuinely no country-specific divergence to model here.
    Ref: MAKU Project Concept - Module 6 (Wind Energy, Onshore/Offshore)
    """
    profile = _resolve_profile(regulatory_profile)
    if hub_height_wind_speed_ms >= WIND_TURBINE_HEIGHT_SUSPEND_MS:
        wind_band = "CRITICAL"
    elif hub_height_wind_speed_ms >= WIND_TURBINE_HEIGHT_RESTRICT_MS:
        wind_band = "HIGH"
    elif hub_height_wind_speed_ms >= 10.0:
        wind_band = "MODERATE"
    else:
        wind_band = "LOW"

    lightning_status = lightning_risk_status(flash_to_bang_sec)
    lightning_stop = flash_to_bang_sec is not None and flash_to_bang_sec <= LIGHTNING_FLASH_TO_BANG_STOP_SEC
    lightning_band = "CRITICAL" if lightning_stop else "LOW"

    sea_state_band = "LOW"
    ctv_status = "Not applicable (onshore)"
    if is_offshore:
        if significant_wave_height_m >= CTV_TRANSFER_SUSPEND_HS_M:
            sea_state_band = "CRITICAL"
            ctv_status = f"Suspended - Hs {significant_wave_height_m:.1f} m exceeds CTV transfer limit"
        elif significant_wave_height_m >= CTV_TRANSFER_RESTRICT_HS_M:
            sea_state_band = "HIGH"
            ctv_status = f"Restricted - Hs {significant_wave_height_m:.1f} m, essential transfers only"
        else:
            ctv_status = f"Normal transfer operations - Hs {significant_wave_height_m:.1f} m"

    band = max(
        (wind_band, lightning_band, sea_state_band),
        key=lambda b: WIND_ENERGY_SEVERITY_RANK[b],
    )
    safety_override = band == "CRITICAL"

    return {
        "module": "Wind Energy (Onshore/Offshore)",
        "hub_height_wind_speed_ms": hub_height_wind_speed_ms,
        "lightning_status": lightning_status,
        "ctv_transfer_status": ctv_status,
        "is_offshore": is_offshore,
        "risk_band": band,
        "safety_override": safety_override,
        "primary_hazard": "Wind-driven fall-from-height risk during blade/nacelle access, lightning "
                           "strike exposure, and (offshore) crew-transfer-vessel sea-state risk",
        "regulatory_country_code": profile["country_code"],
        "regulatory_profile_label": profile["label"],
        "drivers": {
            "Hub-height wind speed (m/s)": hub_height_wind_speed_ms,
            "Lightning flash-to-bang (s)": flash_to_bang_sec if flash_to_bang_sec is not None else "None observed",
            "Offshore": is_offshore,
            "Significant wave height (m)": significant_wave_height_m if is_offshore else "N/A",
        },
    }


# ---------------------------------------------------------------------------
# Module 7: Mining & Quarrying
# ---------------------------------------------------------------------------
# Three independent OEL/exposure-limit checks, each a real named regulatory
# or ISO figure (not invented):
#   1. Respirable crystalline silica (RCS) - OSHA construction PEL is
#      50 ug/m3 (8-hr TWA, 29 CFR 1926.1153); ACGIH TLV for quartz is the
#      same order of magnitude (0.025 mg/m3 = 25 ug/m3), used here as the
#      more conservative action level.
#   2. Noise dose - standard exchange-rate dose formula:
#          allowed_hours = 8 / 2^((L - criterion) / exchange_rate)
#          dose_pct = 100 * actual_hours / allowed_hours
#      Defaults below are OSHA's 90 dBA criterion / 5 dB exchange rate;
#      country_thresholds.py supplies the stricter 85 dBA / 3 dB EU/France
#      variant, since noise limits are one of the few places where
#      jurisdictions genuinely diverge rather than converge on ACGIH.
#   3. Whole-body vibration (WBV) - ISO 2631-1 / EU Physical Agents
#      (Vibration) Directive 2002/44/EC: daily exposure action value
#      A(8) = 0.5 m/s^2, exposure limit value A(8) = 1.15 m/s^2.
#      A(8) = a_w * sqrt(T / 8h)

SILICA_OEL_UGM3 = 50.0            # OSHA 1926.1153 construction PEL, 8-hr TWA
SILICA_ACTION_LEVEL_UGM3 = 25.0   # ACGIH TLV for quartz, used as the conservative action level

NOISE_CRITERION_DEFAULT_DBA = 90.0
NOISE_EXCHANGE_RATE_DEFAULT_DB = 5.0

WBV_ACTION_VALUE_MS2 = 0.5    # EU Directive 2002/44/EC daily exposure action value A(8)
WBV_LIMIT_VALUE_MS2 = 1.15    # EU Directive 2002/44/EC daily exposure limit value A(8)

MINING_SEVERITY_RANK = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


def noise_dose_percent(measured_dba: float, exposure_hours: float,
                        criterion_dba: float = NOISE_CRITERION_DEFAULT_DBA,
                        exchange_rate_db: float = NOISE_EXCHANGE_RATE_DEFAULT_DB) -> float:
    """Standard occupational noise-dose formula. Returns dose as a percent
    of the allowable 8-hour dose (100% = exactly at the permissible limit;
    values are commonly reported well above 100% for loud plant/equipment)."""
    allowed_hours = 8.0 / (2.0 ** ((measured_dba - criterion_dba) / exchange_rate_db))
    if allowed_hours <= 0:
        return float("inf")
    return round(100.0 * exposure_hours / allowed_hours, 1)


def whole_body_vibration_a8(measured_aw_ms2: float, exposure_hours: float) -> float:
    """ISO 2631-1 / EU Directive 2002/44/EC daily exposure value A(8),
    normalizing a measured frequency-weighted acceleration to an 8-hour
    reference exposure duration."""
    return round(measured_aw_ms2 * math.sqrt(max(exposure_hours, 0.0) / 8.0), 3)


def calculate_mining_quarrying_kinetic_risk(
    respirable_silica_ugm3: float,
    measured_noise_dba: float,
    noise_exposure_hours: float,
    measured_vibration_aw_ms2: float,
    vibration_exposure_hours: float,
    noise_criterion_dba: float | None = None,
    noise_exchange_rate_db: float | None = None,
    regulatory_profile: dict | None = None,
) -> dict:
    """
    Screens three independent occupational exposure limits for heavy
    plant/quarry-face crews: respirable crystalline silica dust, noise
    dose, and whole-body vibration from mobile/fixed machinery.

    regulatory_profile: a dict from regulatory_country_thresholds.
    get_regulatory_profile(country_code), or None to use the harmonized
    USA default. Supplies the country's noise_criterion_dba/
    noise_exchange_rate_db (e.g. France's stricter 85 dBA / 3 dB EU
    variant) and silica_action_level_ugm3.

    noise_criterion_dba/noise_exchange_rate_db can still be passed
    explicitly to override the profile's values for a specific
    measurement scenario - if omitted (the default), they're resolved
    from regulatory_profile instead, preserving every existing call site
    and test that doesn't pass either.
    Ref: MAKU Project Concept - Module 7 (Mining & Quarrying)
    """
    profile = _resolve_profile(regulatory_profile)
    resolved_criterion_dba = noise_criterion_dba if noise_criterion_dba is not None else profile["noise_criterion_dba"]
    resolved_exchange_rate_db = noise_exchange_rate_db if noise_exchange_rate_db is not None else profile["noise_exchange_rate_db"]
    silica_action_level = profile["silica_action_level_ugm3"]

    silica_exceeds = respirable_silica_ugm3 > SILICA_OEL_UGM3
    silica_action = respirable_silica_ugm3 > silica_action_level

    noise_dose = noise_dose_percent(
        measured_noise_dba, noise_exposure_hours, resolved_criterion_dba, resolved_exchange_rate_db
    )
    vibration_a8 = whole_body_vibration_a8(measured_vibration_aw_ms2, vibration_exposure_hours)
    vibration_exceeds_limit = vibration_a8 >= WBV_LIMIT_VALUE_MS2
    vibration_exceeds_action = vibration_a8 >= WBV_ACTION_VALUE_MS2

    if silica_exceeds:
        silica_band = "CRITICAL"
    elif silica_action:
        silica_band = "HIGH"
    else:
        silica_band = "LOW"

    if noise_dose >= 200:
        noise_band = "CRITICAL"
    elif noise_dose >= 100:
        noise_band = "HIGH"
    elif noise_dose >= 50:
        noise_band = "MODERATE"
    else:
        noise_band = "LOW"

    if vibration_exceeds_limit:
        vibration_band = "CRITICAL"
    elif vibration_exceeds_action:
        vibration_band = "HIGH"
    else:
        vibration_band = "LOW"

    band = max(
        (silica_band, noise_band, vibration_band),
        key=lambda b: MINING_SEVERITY_RANK[b],
    )
    safety_override = silica_exceeds or vibration_exceeds_limit or noise_dose >= 200

    return {
        "module": "Mining & Quarrying",
        "respirable_silica_ugm3": respirable_silica_ugm3,
        "silica_exceeds_oel": silica_exceeds,
        "noise_dose_pct": noise_dose,
        "vibration_a8_ms2": vibration_a8,
        "vibration_exceeds_action": vibration_exceeds_action,
        "vibration_exceeds_limit": vibration_exceeds_limit,
        "risk_band": band,
        "safety_override": safety_override,
        "primary_hazard": "Respirable crystalline silica exposure, noise-induced hearing loss risk, "
                           "and whole-body-vibration injury risk - quarry-face and mobile-plant crews",
        "regulatory_country_code": profile["country_code"],
        "regulatory_profile_label": profile["label"],
        "drivers": {
            "Respirable silica (ug/m3)": respirable_silica_ugm3,
            "Noise level (dBA)": measured_noise_dba,
            "Noise exposure (hours)": noise_exposure_hours,
            "Noise dose (%)": noise_dose,
            "Vibration a_w (m/s2)": measured_vibration_aw_ms2,
            "Vibration exposure (hours)": vibration_exposure_hours,
            "Vibration A(8) (m/s2)": vibration_a8,
        },
    }


# ---------------------------------------------------------------------------
# Module 8: Marine & Port Construction
# ---------------------------------------------------------------------------
# Three independent gating variables:
#   1. Tide clearance - simple margin check between the current tide level
#      and the minimum clearance a given task requires (e.g. pile-driving
#      templates, jetty underside access) - a standard marine-construction
#      planning check, not a novel formula.
#   2. Night-time visibility modifier - OSHA 1926.56 Table D-3 sets minimum
#      construction-site illumination (general construction areas: 5 fc:
#      ~54 lux; more demanding tasks require more). Below the task's
#      required illuminance, a documented night-work risk amplification
#      factor is applied - night construction work has well-documented
#      elevated incident rates in the literature; 1.3x is an illustrative,
#      conservative screening multiplier, not a measured coefficient.
#   3. Salt-spray corrosion degradation - splash-zone steel hardware
#      (scaffold, lifting points, temporary works) loses rated capacity
#      over time in a marine splash-zone environment. This uses a simple
#      linear derating model against ISO 12944 durability-category-style
#      corrosivity classes (C5-M "very high, marine" being the relevant
#      splash-zone category) - an illustrative screening model for MVP
#      purposes, not a substitute for a certified structural inspection.

TIDE_CLEARANCE_CRITICAL_MARGIN_M = 0.3   # under this clearance margin, halt access/work
TIDE_CLEARANCE_RESTRICT_MARGIN_M = 0.8   # under this, restrict to essential/monitored access

NIGHT_MIN_ILLUMINANCE_LUX = 54.0   # OSHA 1926.56 Table D-3, general construction areas (~5 fc)
NIGHT_RISK_AMPLIFICATION = 1.3     # illustrative multiplier when illuminance is below the minimum

# Illustrative annual capacity-derating rates by corrosivity exposure class,
# loosely modeled on ISO 12944 exposure-category severity ordering
# (C3 moderate -> C5-M very-high/marine). Splash-zone hardware in C5-M
# conditions is assumed to lose rated capacity fastest.
CORROSION_ANNUAL_DERATE_PCT = {
    "C3_moderate": 0.5,
    "C4_high": 1.2,
    "C5M_marine_splash_zone": 2.5,
}

MARINE_PORT_SEVERITY_RANK = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


def corroded_capacity_pct(years_in_service: float, exposure_class: str = "C5M_marine_splash_zone") -> float:
    """Simplified linear capacity-derating screening model for splash-zone
    hardware. Returns remaining rated capacity as a percent of original
    (never below 0)."""
    annual_rate = CORROSION_ANNUAL_DERATE_PCT.get(exposure_class, CORROSION_ANNUAL_DERATE_PCT["C5M_marine_splash_zone"])
    remaining = 100.0 - (annual_rate * max(years_in_service, 0.0))
    return round(max(remaining, 0.0), 1)


def calculate_marine_port_kinetic_risk(
    current_tide_level_m: float,
    required_min_clearance_m: float,
    is_night_operation: bool,
    measured_illuminance_lux: float,
    hardware_years_in_service: float,
    hardware_exposure_class: str = "C5M_marine_splash_zone",
    regulatory_profile: dict | None = None,
) -> dict:
    """
    Gates marine/port construction access against tide clearance margin,
    applies a night-visibility risk amplification when task-area lighting
    falls below the OSHA 1926.56 minimum, and screens splash-zone hardware
    for corrosion-driven capacity loss.

    regulatory_profile: accepted for interface consistency and tagged onto
    the result. Tide clearance, illumination minimums, and corrosion
    derating are site-physics/equipment-condition checks, not areas with
    documented per-country regulatory divergence across the 3 baseline
    jurisdictions.
    Ref: MAKU Project Concept - Module 8 (Marine & Port Construction)
    """
    profile = _resolve_profile(regulatory_profile)
    clearance_margin = round(current_tide_level_m - required_min_clearance_m, 2)
    if clearance_margin <= TIDE_CLEARANCE_CRITICAL_MARGIN_M:
        tide_band = "CRITICAL"
    elif clearance_margin <= TIDE_CLEARANCE_RESTRICT_MARGIN_M:
        tide_band = "HIGH"
    else:
        tide_band = "LOW"

    night_amplified = is_night_operation and measured_illuminance_lux < NIGHT_MIN_ILLUMINANCE_LUX
    night_band = "HIGH" if night_amplified else "LOW"

    remaining_capacity = corroded_capacity_pct(hardware_years_in_service, hardware_exposure_class)
    if remaining_capacity < 70.0:
        corrosion_band = "CRITICAL"
    elif remaining_capacity < 85.0:
        corrosion_band = "HIGH"
    elif remaining_capacity < 95.0:
        corrosion_band = "MODERATE"
    else:
        corrosion_band = "LOW"

    band = max(
        (tide_band, night_band, corrosion_band),
        key=lambda b: MARINE_PORT_SEVERITY_RANK[b],
    )
    # Night amplification compounds whichever base band applies, matching
    # the documented "elevated incident rate at night" effect, without
    # inventing a new numeric hazard score.
    if night_amplified and band in ("MODERATE", "HIGH"):
        band = "HIGH" if band == "MODERATE" else "CRITICAL"

    safety_override = tide_band == "CRITICAL" or corrosion_band == "CRITICAL"

    return {
        "module": "Marine & Port Construction",
        "tide_clearance_margin_m": clearance_margin,
        "night_amplified": night_amplified,
        "hardware_remaining_capacity_pct": remaining_capacity,
        "risk_band": band,
        "safety_override": safety_override,
        "primary_hazard": "Tide-clearance access risk, reduced night-time visibility, and "
                           "corrosion-degraded splash-zone lifting/scaffold hardware capacity",
        "regulatory_country_code": profile["country_code"],
        "regulatory_profile_label": profile["label"],
        "drivers": {
            "Current tide level (m)": current_tide_level_m,
            "Required min. clearance (m)": required_min_clearance_m,
            "Tide clearance margin (m)": clearance_margin,
            "Night operation": is_night_operation,
            "Measured illuminance (lux)": measured_illuminance_lux,
            "Hardware years in service": hardware_years_in_service,
            "Hardware exposure class": hardware_exposure_class,
            "Hardware remaining capacity (%)": remaining_capacity,
        },
    }
