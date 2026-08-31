"""
MAKU Risk Engine
================
Rule-based, formula-driven risk calculations for five construction
environments. Every formula here is a recognized/adapted industry method
(WBGT approximation, Humidex, ACGIH TLV heat-stress action limits, OEL
exceedance logic, an exponential wind-with-height scaling heuristic, the
Lee open-air arc-flash equation) so outputs are transparent and auditable -
not a black box.
This is the "AI" reasoning layer's foundation; the LLM layer (see
ai_advisor.py) sits on top of these numbers to explain results and
suggest controls in plain language.

REGULATORY ALGORITHM VALIDATION (HSE audit corrective action): every named
formula/table above is cross-referenced against its claimed standard - and
honestly flagged where a formula is an illustrative screening heuristic
rather than a certified standards implementation - in
regulatory_references.FORMULA_STANDARDS_MAP (see get_formula_standard()).
That table is the single citable source for "which formulas really
implement ISO 7243/ACGIH/OSHA/IEEE 1584 vs. which ones are this app's own
MVP approximations" - consult it before treating any number here as a
certified compliance figure.

NOTE ON DATA: all environmental inputs (GHI, humidity, sea state, OEL
readings, wind telemetry, electrical load, etc.) are entered by the user
or simulated via sliders in this MVP. In production these fields would be
wired to live satellite/GIS, buoy telemetry, underground sensor networks,
building anemometers/BIM, and rack-level IoT - the architecture below is
built so that swap is a data-source change only, not a logic change.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from regulatory_country_thresholds import get_regulatory_profile
from risk_matrix import score_hazard, aggregate_risk_matrix, severity_from_band, likelihood_from_margin

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


# ---------------------------------------------------------------------------
# ISO 7243 / ACGIH TLV Heat-Stress Upgrade
# ---------------------------------------------------------------------------
# HSE audit corrective action: the pre-existing ACGIH_WBGT_LIMITS/
# acgih_action_level() pair above (unacclimatized, light/moderate/heavy
# only, no clothing correction) is extended - never replaced - with:
#   - a "very_heavy" workload row (ACGIH's 4th metabolic category)
#   - an acclimatized-worker table (commonly-cited ~1 degC upward shift)
#   - a Clothing Adjustment Factor (CAF) table, applied as a WBGT-effective
#     addition per the ACGIH TLV booklet / OSHA Technical Manual Section
#     III Chapter 4 convention
#   - a work/rest ratio SOLVER that walks 100/0 -> 75/25 -> 50/50 -> 25/75
#     and returns the least-restrictive ratio that brings the worker into
#     ACGIH compliance, which is what "work/rest calculations ... justified
#     against ACGIH TLV/OSHA tables" means in practice: not a single
#     pass/fail check, but the actual regimen recommendation those tables
#     exist to produce.
# Every existing key (ACGIH_WBGT_LIMITS, acgih_action_level) is untouched;
# this is purely additive.
#
# HONESTY CAVEAT (matching this codebase's existing convention for
# secondary/approximated regulatory figures - see regulatory_country_
# thresholds.py and wbgt_outdoor_approx()'s own docstring): the
# "very_heavy" row and the acclimatized-worker shift below are commonly-
# cited approximations reconstructed from the general shape of the
# published ACGIH TLV Heat Stress and Strain tables, not a verbatim
# transcription of the current copyrighted booklet. Verify the current
# edition's exact figures before using this for a real compliance
# decision - the same caveat this codebase already applies elsewhere.

# ACGIH's own workload categories map to approximate ISO 8996 metabolic
# rate ranges (W/m2, illustrative midpoints from the published typical-
# activity examples) - shown in the UI as context for which category to
# pick, not used as a second, independent calculation path (ACGIH TLV
# limits are looked up by category label, not integrated from W/m2 the way
# ISO 7243's own reference-WBGT curve is; mixing the two methods inside
# one number would misrepresent both standards).
METABOLIC_RATE_WM2_BY_CATEGORY = {
    "light": (115, 220),      # e.g. seated/standing light hand-arm work, slow walking
    "moderate": (220, 360),   # e.g. sustained moderate hand/arm and trunk work, walking with some load
    "heavy": (360, 520),      # e.g. intense arm/trunk work, carrying, digging
    "very_heavy": (520, 650), # e.g. very intense pace, heavy shovel/pick work
}

# 4th ACGIH workload category (100% work, 75/25, 50/50, 25/75), unacclimatized.
# Continuous (100/0) very-heavy work is generally not represented in the
# published table (sustained very-heavy exertion without rest is not a
# realistic occupational regimen) - modeled here as None so callers that
# request it are told explicitly "not applicable", not given a fabricated
# number.
ACGIH_WBGT_LIMITS_VERY_HEAVY_UNACCLIMATIZED = [None, 27.0, 28.0, 29.0]

# ACGIH acclimatized-worker limits are commonly cited as approximately
# 1 degC higher than the unacclimatized table across every cell - built
# programmatically off the single already-audited unacclimatized table
# below rather than hand-duplicating a second full set of numbers, so the
# two tables can never silently drift apart.
ACGIH_ACCLIMATIZATION_SHIFT_C = 1.0


def _acgih_table(acclimatized: bool) -> dict:
    """Returns the full 4-workload-category ACGIH WBGT action-limit table
    (light/moderate/heavy/very_heavy, each a 4-element [100/0, 75/25,
    50/50, 25/75] list), unacclimatized or acclimatized. Built from the
    single pre-existing ACGIH_WBGT_LIMITS table plus the very_heavy row
    above, so the base numbers are defined in exactly one place."""
    base = dict(ACGIH_WBGT_LIMITS)
    base["very_heavy"] = ACGIH_WBGT_LIMITS_VERY_HEAVY_UNACCLIMATIZED
    if not acclimatized:
        return base
    return {
        category: [
            None if v is None else round(v + ACGIH_ACCLIMATIZATION_SHIFT_C, 1)
            for v in limits
        ]
        for category, limits in base.items()
    }


# Clothing Adjustment Factor (CAF): WBGT-effective addition (degC) applied
# on top of the ambient/measured WBGT before comparing to the ACGIH table,
# since the ACGIH base table assumes standard single-layer woork clothing.
# Sourced from the commonly-cited ACGIH TLV booklet / OSHA Technical Manual
# Section III Chapter 4 CAF table (see HONESTY CAVEAT above).
CLOTHING_ADJUSTMENT_FACTOR_C = {
    "work_clothes": 0.0,                    # single-layer woven work clothes (baseline, no correction)
    "sms_polypropylene_coveralls": 0.5,
    "polyolefin_coveralls": 1.0,
    "double_layer_woven_coveralls": 3.0,
    "vapor_barrier_coveralls": 11.0,         # see VAPOR_BARRIER_REQUIRES_MONITORING note below
}

# ACGIH is explicit that for vapor-barrier/limited-use encapsulating
# ensembles, a simple additive WBGT correction is not considered adequate
# on its own - direct physiological monitoring is recommended instead.
# This flag drives an explicit safety_override / stop-work note rather
# than silently trusting the additive correction the way the other
# clothing categories are trusted.
CLOTHING_REQUIRES_PHYSIOLOGICAL_MONITORING = {"vapor_barrier_coveralls"}

_WORK_REST_RATIOS_ASCENDING = ["100/0", "75/25", "50/50", "25/75"]


def recommended_work_rest_ratio(effective_wbgt: float, workload_category: str, acclimatized: bool) -> dict:
    """
    Solves for the least-restrictive ACGIH work/rest ratio that brings
    effective_wbgt into compliance for the given workload category and
    acclimatization state - the actual "recommendation" ACGIH's tables are
    designed to produce, not just a single pass/fail check against one
    caller-chosen ratio.

    Returns {"ratio": str | None, "limit": float | None, "compliant": bool}.
    ratio/limit are None (compliant False) when even the most conservative
    25/75 ratio does not bring the worker into compliance at this
    workload/acclimatization/clothing combination - a stop-work condition,
    not merely a "restrict to 25/75" recommendation.
    """
    table = _acgih_table(acclimatized)
    limits = table.get(workload_category, table["moderate"])
    for ratio, limit in zip(_WORK_REST_RATIOS_ASCENDING, limits):
        if limit is not None and effective_wbgt <= limit:
            return {"ratio": ratio, "limit": limit, "compliant": True}
    # Not compliant at any ratio: report the most conservative (25/75)
    # limit for reference, but flag non-compliance explicitly.
    most_conservative_limit = limits[-1]
    return {"ratio": None, "limit": most_conservative_limit, "compliant": False}


ISO7243_HEAT_SEVERITY_RANK = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


def calculate_iso7243_heat_stress(
    workload_category: str = "moderate",
    clothing_type: str = "work_clothes",
    acclimatized: bool = False,
    requested_work_rest_ratio: str = "100/0",
    wbgt_measured_c: float | None = None,
    air_temp_c: float | None = None,
    relative_humidity_pct: float | None = None,
    regulatory_profile: dict | None = None,
) -> dict:
    """
    Comprehensive occupational heat-stress screen following ACGIH TLV
    methodology (ISO 7243 is the WBGT measurement standard the ACGIH TLV
    itself is built on - both describe the same WBGT-based screening
    approach): WBGT (measured directly by a sensor, or approximated from
    ambient temp/RH if no direct reading is available), workload/metabolic
    category, clothing adjustment, and acclimatization status all feed
    into a work/rest-ratio recommendation and an explicit stop-work
    condition when no ratio suffices.

    wbgt_measured_c: pass this when a real WBGT meter/globe-thermometer
    reading is available (the preferred, more accurate path per ISO 7243).
    If omitted, air_temp_c/relative_humidity_pct are required and WBGT is
    approximated via wbgt_outdoor_approx() (the same approximation already
    used elsewhere in this file) - the result notes which path was used,
    for the "Data Source: Live sensor vs. approximated" traceability the
    audit also requires.

    regulatory_profile: accepted for interface consistency with every
    other calculate_*_kinetic_risk() function; ACGIH TLV heat-stress
    action limits are the harmonized reference used across all 3 baseline
    jurisdictions in this deployment, so no per-country override is
    currently modeled here.
    Ref: HSE Auditor corrective action #2 - Occupational Heat-Stress Upgrade
    """
    profile = _resolve_profile(regulatory_profile)

    if wbgt_measured_c is not None:
        raw_wbgt = wbgt_measured_c
        wbgt_source = "Direct WBGT meter/globe-thermometer reading"
    else:
        if air_temp_c is None or relative_humidity_pct is None:
            raise ValueError(
                "calculate_iso7243_heat_stress requires either wbgt_measured_c, "
                "or both air_temp_c and relative_humidity_pct to approximate it."
            )
        raw_wbgt = wbgt_outdoor_approx(air_temp_c, relative_humidity_pct)
        wbgt_source = "Approximated from ambient temperature/RH (wbgt_outdoor_approx)"

    caf = CLOTHING_ADJUSTMENT_FACTOR_C.get(clothing_type, 0.0)
    effective_wbgt = round(raw_wbgt + caf, 1)
    requires_monitoring = clothing_type in CLOTHING_REQUIRES_PHYSIOLOGICAL_MONITORING

    # The pre-existing acgih_action_level() always reads the unacclimatized,
    # light/moderate/heavy-only table (its signature and behavior are never
    # changed here - other code may still depend on that exact contract).
    # This function needs the acclimatized/unacclimatized + very_heavy-aware
    # table instead, so it looks the requested ratio's limit up directly
    # from _acgih_table() rather than calling acgih_action_level().
    table = _acgih_table(acclimatized)
    limits = table.get(workload_category, table["moderate"])
    idx = _WORK_REST_RATIOS_ASCENDING.index(requested_work_rest_ratio) \
        if requested_work_rest_ratio in _WORK_REST_RATIOS_ASCENDING else 0
    requested_limit = limits[idx]
    requested_exceeds = None if requested_limit is None else effective_wbgt > requested_limit
    requested_margin = None if requested_limit is None else round(effective_wbgt - requested_limit, 1)

    recommendation = recommended_work_rest_ratio(effective_wbgt, workload_category, acclimatized)
    stop_work = (not recommendation["compliant"]) or requires_monitoring

    if stop_work:
        heat_band = "CRITICAL"
    elif requested_exceeds:
        heat_band = "HIGH"
    elif recommendation["ratio"] != "100/0":
        heat_band = "MODERATE"
    else:
        heat_band = "LOW"

    metabolic_range = METABOLIC_RATE_WM2_BY_CATEGORY.get(workload_category, METABOLIC_RATE_WM2_BY_CATEGORY["moderate"])

    reference_limit_for_matrix = recommendation["limit"] if recommendation["limit"] is not None else (
        requested_limit if requested_limit is not None else effective_wbgt
    )
    risk_matrix = aggregate_risk_matrix([
        score_hazard(
            "WBGT heat-strain (clothing- and workload-adjusted)",
            5 if stop_work else likelihood_from_margin(effective_wbgt, reference_limit_for_matrix, 3.0),
            severity_from_band(heat_band),
            note=f"Effective WBGT {effective_wbgt} C (raw {round(raw_wbgt, 1)} C + CAF {caf} C) vs "
                 f"{reference_limit_for_matrix} C ACGIH limit ({workload_category}, "
                 f"{'acclimatized' if acclimatized else 'unacclimatized'})",
        ),
    ])

    return {
        "module": "Occupational Heat Stress (ISO 7243 / ACGIH TLV)",
        "wbgt_source": wbgt_source,
        "raw_wbgt_c": round(raw_wbgt, 1),
        "clothing_type": clothing_type,
        "clothing_adjustment_factor_c": caf,
        "effective_wbgt_c": effective_wbgt,
        "workload_category": workload_category,
        "metabolic_rate_wm2_range": f"{metabolic_range[0]}-{metabolic_range[1]} W/m2 (ISO 8996 illustrative range)",
        "acclimatized": acclimatized,
        "requested_work_rest_ratio": requested_work_rest_ratio,
        "requested_ratio_limit_c": requested_limit,
        "requested_ratio_exceeds": requested_exceeds,
        "requested_ratio_margin_c": requested_margin,
        "recommended_work_rest_ratio": recommendation["ratio"],
        "recommended_ratio_limit_c": recommendation["limit"],
        "requires_physiological_monitoring": requires_monitoring,
        "risk_band": heat_band,
        "safety_override": stop_work,
        "risk_matrix": risk_matrix,
        "primary_hazard": "Heat strain from WBGT exposure, adjusted for clothing insulation, workload/metabolic "
                           "rate, and acclimatization status, screened against ACGIH TLV action limits",
        "regulatory_country_code": profile["country_code"],
        "regulatory_profile_label": profile["label"],
        "drivers": {
            "WBGT data source": wbgt_source,
            "Raw WBGT (C)": round(raw_wbgt, 1),
            "Clothing type": clothing_type,
            "Clothing Adjustment Factor (C)": caf,
            "Effective WBGT (C)": effective_wbgt,
            "Workload/metabolic category": workload_category,
            "Metabolic rate range (W/m2)": f"{metabolic_range[0]}-{metabolic_range[1]}",
            "Acclimatized": acclimatized,
            "Requested work/rest ratio": requested_work_rest_ratio,
            "Requested ratio ACGIH limit (C)": requested_limit,
            "Requested ratio exceeded": requested_exceeds,
            "Recommended work/rest ratio": recommendation["ratio"] or "NONE - STOP WORK (no compliant ratio)",
            "Recommended ratio ACGIH limit (C)": recommendation["limit"],
            "Requires physiological monitoring (vapor-barrier PPE)": requires_monitoring,
        },
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

    # ---- Risk matrix breakdown (item 1: individual hazards scored and
    # rated separately before aggregation) ----------------------------------
    # Heat and UV are decomposed into their own bands using EXACTLY the same
    # cutoffs (45/38/32 for temp, 11/8 for UV) already governing risk_level
    # above - this is a re-expression of the existing if/elif logic on the
    # matrix's numeric axis, not a second, independently-invented judgment.
    _heat_band = "Extreme" if perceived_thermal_temp >= 45.0 else (
        "High" if perceived_thermal_temp >= 38.0 else ("Moderate" if perceived_thermal_temp >= 32.0 else "Low")
    )
    _uv_band = "Extreme" if uv_index >= 11.0 else ("High" if uv_index >= 8.0 else "Low")
    risk_matrix = aggregate_risk_matrix([
        score_hazard(
            "Perceived thermal temperature (heat/UV amplification)",
            likelihood_from_margin(perceived_thermal_temp, 45.0, 13.0),
            severity_from_band(_heat_band),
            note=f"{round(perceived_thermal_temp, 1)} C vs 45.0 C critical threshold",
        ),
        score_hazard(
            "UV index",
            likelihood_from_margin(uv_index, 11.0, 3.0),
            severity_from_band(_uv_band),
            note=f"UV index {uv_index} vs 11.0 critical threshold",
        ),
    ])

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
        "risk_matrix": risk_matrix,
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

    # ---- Risk matrix breakdown: heat (Humidex) and wind (crane/lifting)
    # scored independently, using the SAME band/status this function
    # already computed above. ------------------------------------------
    _wind_severity = 5 if wind_risk_status.startswith("Suspended") else (
        4 if wind_risk_status.startswith("Restricted") else 1
    )
    risk_matrix = aggregate_risk_matrix([
        score_hazard(
            "Humidex heat stress",
            likelihood_from_margin(hmdx, 40.0, 11.0),
            severity_from_band(band),
            note=f"Humidex {round(hmdx, 1)} vs 40.0 High/Extreme threshold",
        ),
        score_hazard(
            "Wind (crane/lifting)",
            likelihood_from_margin(wind_speed, OFFSHORE_WIND_SUSPEND_KNOTS,
                                    OFFSHORE_WIND_SUSPEND_KNOTS - OFFSHORE_WIND_RESTRICT_KNOTS),
            _wind_severity,
            note=f"{wind_speed} kn vs {OFFSHORE_WIND_SUSPEND_KNOTS} kn suspend threshold - {wind_risk_status}",
        ),
    ])

    return {
        "module": "Offshore (Marine)",
        "humidex": round(hmdx, 1),
        "wind_risk_status": wind_risk_status,
        "risk_band": band,  # compatibility field for ai_advisor.offshore_controls / generate_narrative
        "safety_override": safety_override,
        "risk_matrix": risk_matrix,
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

    # ---- Risk matrix breakdown: heat, CO, and PM2.5 dust scored
    # independently, reusing the bands already computed above. -------------
    risk_matrix = aggregate_risk_matrix([
        score_hazard(
            "Trapped-heat / geothermal humidity (perceived temp)",
            likelihood_from_margin(perceived_temp, UNDERGROUND_PERCEIVED_TEMP_OVERRIDE_C, 10.0),
            severity_from_band(heat_band),
            note=f"{round(perceived_temp, 1)} C vs {UNDERGROUND_PERCEIVED_TEMP_OVERRIDE_C} C override threshold",
        ),
        score_hazard(
            "Carbon monoxide (CO) OEL",
            likelihood_from_margin(gas_co_ppm, co_oel, co_oel * 0.5),
            severity_from_band(co_band),
            note=f"{gas_co_ppm} ppm vs {co_oel} ppm OEL",
        ),
        score_hazard(
            "Respirable dust (PM2.5) OEL",
            likelihood_from_margin(particulate_matter_pm25, pm25_oel, pm25_oel * 0.5),
            severity_from_band(pm25_band),
            note=f"{particulate_matter_pm25} ug/m3 vs {pm25_oel} ug/m3 OEL",
        ),
    ])

    return {
        "module": "Underground (Tunnel/Metro)",
        "perceived_temp": round(perceived_temp, 1),
        "gas_exceeds": gas_exceeds,
        "dust_exceeds": dust_exceeds,
        "risk_band": band,  # compatibility field for ai_advisor.underground_controls / generate_narrative
        "safety_override": safety_override,
        "risk_matrix": risk_matrix,
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

    # ---- Risk matrix breakdown: crane wind-shear and load-oscillation
    # scored independently, reusing the bands already computed above. ------
    risk_matrix = aggregate_risk_matrix([
        score_hazard(
            "Wind shear (crane gate)",
            likelihood_from_margin(scaled_wind_speed, suspend_knots, suspend_knots - restrict_knots),
            severity_from_band(wind_band),
            note=f"{round(scaled_wind_speed, 1)} kn (scaled) vs {suspend_knots} kn suspend threshold",
        ),
        score_hazard(
            "Crane-load oscillation index",
            likelihood_from_margin(oscillation_index, 50.0, 25.0),
            severity_from_band(oscillation_band),
            note=f"Oscillation index {round(oscillation_index, 1)} vs 50.0 High/Critical threshold",
        ),
    ])

    return {
        "module": "High-Rise (Vertical Urban)",
        "scaled_wind_speed": round(scaled_wind_speed, 1),
        "oscillation_index": round(oscillation_index, 1),
        "risk_band": band,  # compatibility field for ai_advisor.high_rise_controls / generate_narrative
        "safety_override": safety_override,
        "risk_matrix": risk_matrix,
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

    # ---- Risk matrix breakdown: arc-flash, thermal differential, and
    # confined-space/armed-suppression scored independently. ---------------
    risk_matrix = aggregate_risk_matrix([
        score_hazard(
            "Arc-flash incident energy",
            likelihood_from_margin(arc_flash_energy_cal, DATACENTER_ARC_FLASH_DANGER_CAL, 15.0),
            severity_from_band(arc_flash_band),
            note=f"{round(arc_flash_energy_cal, 1)} cal/cm2 vs {DATACENTER_ARC_FLASH_DANGER_CAL} cal/cm2 danger threshold",
        ),
        score_hazard(
            "Hot/cold-aisle thermal differential",
            likelihood_from_margin(thermal_differential, DATACENTER_THERMAL_DIFF_CRITICAL_C, 10.0),
            severity_from_band(thermal_band),
            note=f"{thermal_differential} C delta vs {DATACENTER_THERMAL_DIFF_CRITICAL_C} C critical threshold",
        ),
        score_hazard(
            "Confined ceiling-void + armed clean-agent suppression",
            5 if confined_armed_danger else 1,
            5 if confined_armed_danger else 1,
            note="Confined space AND suppression armed simultaneously" if confined_armed_danger
                 else "Not both conditions present",
        ),
    ])

    return {
        "module": "Data Center (Controlled Critical Environment)",
        "arc_flash_energy_cal": round(arc_flash_energy_cal, 1),
        "thermal_differential": thermal_differential,
        "risk_band": band,  # compatibility field for ai_advisor.data_center_controls / generate_narrative
        "safety_override": safety_override,
        "risk_matrix": risk_matrix,
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

    risk_matrix = aggregate_risk_matrix([
        score_hazard(
            "Hub-height wind speed (fall-from-height access gate)",
            likelihood_from_margin(hub_height_wind_speed_ms, WIND_TURBINE_HEIGHT_SUSPEND_MS,
                                    WIND_TURBINE_HEIGHT_SUSPEND_MS - WIND_TURBINE_HEIGHT_RESTRICT_MS),
            severity_from_band(wind_band),
            note=f"{hub_height_wind_speed_ms} m/s vs {WIND_TURBINE_HEIGHT_SUSPEND_MS} m/s suspend threshold",
        ),
        score_hazard(
            "Lightning (30-30 rule)",
            5 if lightning_stop else 1,
            severity_from_band(lightning_band),
            note=(f"Flash-to-bang {flash_to_bang_sec}s vs {LIGHTNING_FLASH_TO_BANG_STOP_SEC}s stop threshold"
                  if flash_to_bang_sec is not None else "No lightning observed"),
        ),
        score_hazard(
            "CTV transfer sea state (offshore)",
            likelihood_from_margin(significant_wave_height_m, CTV_TRANSFER_SUSPEND_HS_M,
                                    CTV_TRANSFER_SUSPEND_HS_M - CTV_TRANSFER_RESTRICT_HS_M) if is_offshore else 1,
            severity_from_band(sea_state_band),
            note=f"Hs {significant_wave_height_m} m vs {CTV_TRANSFER_SUSPEND_HS_M} m suspend threshold" if is_offshore
                 else "Not applicable (onshore)",
        ),
    ])

    return {
        "module": "Wind Energy (Onshore/Offshore)",
        "hub_height_wind_speed_ms": hub_height_wind_speed_ms,
        "lightning_status": lightning_status,
        "ctv_transfer_status": ctv_status,
        "is_offshore": is_offshore,
        "risk_band": band,
        "safety_override": safety_override,
        "risk_matrix": risk_matrix,
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

    risk_matrix = aggregate_risk_matrix([
        score_hazard(
            "Respirable crystalline silica (RCS)",
            likelihood_from_margin(respirable_silica_ugm3, SILICA_OEL_UGM3, SILICA_OEL_UGM3 - silica_action_level),
            severity_from_band(silica_band),
            note=f"{respirable_silica_ugm3} ug/m3 vs {SILICA_OEL_UGM3} ug/m3 OEL",
        ),
        score_hazard(
            "Noise dose",
            likelihood_from_margin(noise_dose, 100.0, 50.0),
            severity_from_band(noise_band),
            note=f"Noise dose {noise_dose}% vs 100% permissible dose",
        ),
        score_hazard(
            "Whole-body vibration A(8)",
            likelihood_from_margin(vibration_a8, WBV_LIMIT_VALUE_MS2, WBV_LIMIT_VALUE_MS2 - WBV_ACTION_VALUE_MS2),
            severity_from_band(vibration_band),
            note=f"A(8) {vibration_a8} m/s2 vs {WBV_LIMIT_VALUE_MS2} m/s2 exposure limit value",
        ),
    ])

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
        "risk_matrix": risk_matrix,
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

    risk_matrix = aggregate_risk_matrix([
        score_hazard(
            "Tide clearance margin",
            # Tide clearance margin is inverted relative to every other hazard
            # driver in this codebase: a LARGER clearance_margin is SAFER, not
            # more dangerous, so likelihood_from_margin() (which treats a
            # larger current_value as worse) can't be called on
            # clearance_margin directly - doing so previously produced a
            # spurious high-likelihood score for a comfortably safe clearance.
            # Negating both current_value and threshold flips the axis so the
            # "unsafe direction" (margin shrinking toward/through the critical
            # threshold) is what drives the likelihood, matching every other
            # hazard's convention.
            likelihood_from_margin(-clearance_margin, -TIDE_CLEARANCE_CRITICAL_MARGIN_M,
                                    TIDE_CLEARANCE_RESTRICT_MARGIN_M - TIDE_CLEARANCE_CRITICAL_MARGIN_M),
            severity_from_band(tide_band),
            note=f"Clearance margin {clearance_margin} m vs {TIDE_CLEARANCE_CRITICAL_MARGIN_M} m critical threshold",
        ),
        score_hazard(
            "Night-time visibility",
            5 if night_amplified else 1,
            severity_from_band(night_band),
            note=(f"Illuminance {measured_illuminance_lux} lux vs {NIGHT_MIN_ILLUMINANCE_LUX} lux OSHA minimum"
                  if is_night_operation else "Not a night operation"),
        ),
        score_hazard(
            "Splash-zone hardware corrosion capacity loss",
            # Same inverted-direction case as tide clearance above: remaining
            # capacity is a "higher is safer" reading (100% = undegraded), so
            # it is negated against the negated CRITICAL cutoff (70%) rather
            # than passed to likelihood_from_margin() directly - otherwise a
            # badly corroded (LOW remaining capacity, CRITICAL band) hazard
            # would wrongly score a LOW likelihood.
            likelihood_from_margin(-remaining_capacity, -70.0, 25.0),
            severity_from_band(corrosion_band),
            note=f"Remaining capacity {remaining_capacity}% after {hardware_years_in_service} yrs "
                 f"({hardware_exposure_class})",
        ),
    ])

    return {
        "module": "Marine & Port Construction",
        "tide_clearance_margin_m": clearance_margin,
        "night_amplified": night_amplified,
        "hardware_remaining_capacity_pct": remaining_capacity,
        "risk_band": band,
        "safety_override": safety_override,
        "risk_matrix": risk_matrix,
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


# ===========================================================================
# Stop-Work Trigger Registry
# ===========================================================================
# HSE audit corrective action: "explicitly define/document safety override
# trigger thresholds" (e.g. WBGT>32C, wind>15 m/s for cranes). Every
# calculate_*_kinetic_risk() function above already computes a
# "safety_override" (or, for the Solar module specifically -
# "override_required", a pre-existing naming inconsistency this registry
# documents rather than silently changes, since altering that dict key
# would break Solar's own already-tested call sites) boolean from real,
# already-audited named constants - but that boolean, on its own, doesn't
# tell an auditor or a site supervisor WHICH numeric threshold triggered it
# without reading the source. This registry is a single, citable,
# human-readable index of every one of those thresholds: purely
# descriptive metadata pointing at the SAME constants already used in the
# calculations above (most entries reference the constant by name in
# "source_constant"), not a second, independent set of numbers that could
# drift out of sync with the actual logic.
#
# Some thresholds are country-profile-dependent (occupational exposure
# limits: CO/PM2.5/silica/noise) rather than a single fixed constant - for
# those, source_constant names the profile path and the value shown is the
# harmonized USA default (_DEFAULT_REGULATORY_PROFILE), the same profile
# every calculate_*_kinetic_risk() function falls back to when no
# regulatory_profile is supplied. The actual value used in a given
# assessment can differ by jurisdiction; get_stop_work_triggers() flags
# these with profile_dependent=True so a caller/UI never presents them as
# a single universal number.
STOP_WORK_TRIGGERS = [
    {
        "module": "Solar (Desert)",
        "trigger": "Perceived thermal temperature (heat/UV amplified) at or above 45.0 C, OR UV Index at or above 11",
        "threshold": "45.0 C (perceived) / UV 11",
        "source_constant": "calculate_solar_albedo_heat_risk() inline threshold (perceived_thermal_temp >= 45.0 or uv_index >= 11)",
        "result_key": "override_required",
        "profile_dependent": False,
    },
    {
        "module": "Offshore (Marine)",
        "trigger": "Wind speed at or above the crane/lifting suspend threshold, OR humidex risk band reaches Extreme",
        "threshold": f"{OFFSHORE_WIND_SUSPEND_KNOTS} kn wind",
        "source_constant": "OFFSHORE_WIND_SUSPEND_KNOTS",
        "result_key": "safety_override",
        "profile_dependent": False,
    },
    {
        "module": "Underground (Tunnel/Metro)",
        "trigger": "Perceived temperature exceeds the override threshold, OR CO exceeds its OEL, OR PM2.5 exceeds its OEL",
        "threshold": f"{UNDERGROUND_PERCEIVED_TEMP_OVERRIDE_C} C perceived temp / CO {CO_OEL_LIMIT_PPM} ppm / PM2.5 {PM25_OEL_LIMIT_UGM3} ug/m3 (USA default)",
        "source_constant": "UNDERGROUND_PERCEIVED_TEMP_OVERRIDE_C; regulatory_profile['air_quality']['co_oel_ppm']/['pm25_oel_ugm3']",
        "result_key": "safety_override",
        "profile_dependent": True,
    },
    {
        "module": "High-Rise (Vertical Urban)",
        "trigger": "Height-scaled wind speed exceeds the crane suspend threshold",
        "threshold": f"{CRANE_SUSPEND_WIND_KNOTS} kn (USA default; wind_shear.crane_suspend_knots per profile)",
        "source_constant": "CRANE_SUSPEND_WIND_KNOTS (regulatory_profile['wind_shear']['crane_suspend_knots'])",
        "result_key": "safety_override",
        "profile_dependent": True,
    },
    {
        "module": "Data Center (Controlled Critical Environment)",
        "trigger": "Arc-flash incident energy exceeds the no-safe-PPE-category threshold, OR confined ceiling void with "
                   "clean-agent suppression armed simultaneously, OR hot/cold-aisle thermal differential is critical",
        "threshold": f"{DATACENTER_ARC_FLASH_DANGER_CAL} cal/cm2 arc-flash / {DATACENTER_THERMAL_DIFF_CRITICAL_C} C thermal delta",
        "source_constant": "DATACENTER_ARC_FLASH_DANGER_CAL; DATACENTER_THERMAL_DIFF_CRITICAL_C",
        "result_key": "safety_override",
        "profile_dependent": False,
    },
    {
        "module": "Wind Energy (Onshore/Offshore)",
        "trigger": "Hub-height wind speed at or above the turbine-access suspend threshold, OR lightning flash-to-bang "
                   "at or below the 30-30 rule stop threshold, OR (offshore) significant wave height at or above the "
                   "CTV transfer suspend threshold",
        "threshold": f"{WIND_TURBINE_HEIGHT_SUSPEND_MS} m/s hub wind / {LIGHTNING_FLASH_TO_BANG_STOP_SEC}s flash-to-bang / {CTV_TRANSFER_SUSPEND_HS_M} m Hs",
        "source_constant": "WIND_TURBINE_HEIGHT_SUSPEND_MS; LIGHTNING_FLASH_TO_BANG_STOP_SEC; CTV_TRANSFER_SUSPEND_HS_M",
        "result_key": "safety_override",
        "profile_dependent": False,
    },
    {
        "module": "Mining & Quarrying",
        "trigger": "Respirable silica exceeds its OEL, OR whole-body vibration A(8) exceeds the exposure limit value, "
                   "OR noise dose reaches 200% of the permissible 8-hour dose",
        "threshold": f"{SILICA_OEL_UGM3} ug/m3 silica (USA/OSHA default) / {WBV_LIMIT_VALUE_MS2} m/s2 WBV A(8) / 200% noise dose",
        "source_constant": "SILICA_OEL_UGM3; WBV_LIMIT_VALUE_MS2; noise_dose_percent() >= 200",
        "result_key": "safety_override",
        "profile_dependent": True,
    },
    {
        "module": "Marine & Port Construction",
        "trigger": "Tide clearance margin at or below the critical margin, OR splash-zone hardware corrosion drops "
                   "remaining capacity below 70%",
        "threshold": f"{TIDE_CLEARANCE_CRITICAL_MARGIN_M} m tide clearance margin / 70% remaining hardware capacity",
        "source_constant": "TIDE_CLEARANCE_CRITICAL_MARGIN_M; corroded_capacity_pct() < 70.0",
        "result_key": "safety_override",
        "profile_dependent": False,
    },
    {
        "module": "Occupational Heat Stress (ISO 7243 / ACGIH TLV)",
        "trigger": "No ACGIH work/rest ratio (up to and including 25/75) brings the clothing- and workload-adjusted "
                   "effective WBGT into compliance, OR the selected clothing requires direct physiological "
                   "monitoring (vapor-barrier/limited-use ensembles) rather than a WBGT table lookup",
        "threshold": "Workload- and acclimatization-dependent (see ACGIH_WBGT_LIMITS / _acgih_table()); "
                     "vapor_barrier_coveralls always triggers regardless of WBGT",
        "source_constant": "recommended_work_rest_ratio() compliant=False; CLOTHING_REQUIRES_PHYSIOLOGICAL_MONITORING",
        "result_key": "safety_override",
        "profile_dependent": False,
    },
]


def get_stop_work_triggers(module: str | None = None) -> list[dict]:
    """Returns the Stop-Work Trigger Registry, optionally filtered to a
    single module (matched against the "module" field, case-insensitive
    substring match so a caller can pass either the short name shown in
    the sidebar navigation or the full module label used in result
    dicts). Returns the full registry when module is None or matches
    nothing, so a caller always gets a usable (if unfiltered) list rather
    than an empty/confusing result for an unrecognized module name."""
    if not module:
        return list(STOP_WORK_TRIGGERS)
    needle = module.strip().lower()
    filtered = [entry for entry in STOP_WORK_TRIGGERS if needle in entry["module"].lower()]
    return filtered if filtered else list(STOP_WORK_TRIGGERS)


# ===========================================================================
# Enterprise-scale vectorized calculations (NumPy/Pandas)
# ===========================================================================
# Every calculate_*_kinetic_risk() function above is deliberately scalar -
# one call, one site - so each formula reads and tests as a single audited
# line-by-line calculation (this file's whole "transparent, not a black
# box" design goal). At enterprise scale, a portfolio might have dozens of
# active sub-zones/sites being scored every refresh cycle; calling a scalar
# function in a Python for-loop per site works fine for a handful of zones
# but doesn't scale gracefully to a fleet. The functions below vectorize
# the closed-form elementwise formulas (WBGT, Humidex, Wind Chill) with
# NumPy so an entire array/Series of sites can be scored in one call, plus
# a Pandas batch runner that attaches those columns to a whole
# sites-DataFrame at once. This is purely additive scale/aggregation on
# top of the exact same audited formulas already defined above (no new
# risk math is invented here) - no existing scalar function's signature or
# behavior changes.

def wbgt_outdoor_approx_vectorized(temp_c, rh_pct):
    """Vectorized form of wbgt_outdoor_approx() - accepts NumPy arrays,
    Pandas Series, or plain floats/lists; returns a NumPy array (or a
    0-d/scalar-like array for scalar input). Identical formula to the
    scalar version, just with NumPy elementwise operators."""
    temp_c = np.asarray(temp_c, dtype=float)
    rh_pct = np.asarray(rh_pct, dtype=float)
    saturation = 6.105 * np.exp((17.27 * temp_c) / (237.7 + temp_c))
    e = (rh_pct / 100.0) * saturation
    return 0.567 * temp_c + 0.393 * e + 3.94


def humidex_vectorized(temp_c, rh_pct):
    """Vectorized form of humidex()."""
    temp_c = np.asarray(temp_c, dtype=float)
    rh_pct = np.asarray(rh_pct, dtype=float)
    saturation = 6.105 * np.exp((17.27 * temp_c) / (237.7 + temp_c))
    e = (rh_pct / 100.0) * saturation
    return temp_c + 0.5555 * (e - 10.0)


def wind_chill_c_vectorized(temp_c, wind_speed_kmh):
    """Vectorized form of wind_chill_c(). Uses np.where to reproduce the
    scalar function's 'outside the formula's valid domain (T>10C or
    near-still air) -> return temp_c unchanged' rule elementwise, rather
    than extrapolating the formula outside its validated range for any
    site in the batch."""
    temp_c = np.asarray(temp_c, dtype=float)
    wind_speed_kmh = np.asarray(wind_speed_kmh, dtype=float)
    v16 = np.power(np.maximum(wind_speed_kmh, 1e-9), 0.16)
    formula = 13.12 + 0.6215 * temp_c - 11.37 * v16 + 0.3965 * temp_c * v16
    valid = (temp_c <= 10.0) & (wind_speed_kmh > 4.8)
    return np.round(np.where(valid, formula, temp_c), 1)


def calculate_multi_site_heat_risk(sites: pd.DataFrame) -> pd.DataFrame:
    """Enterprise fleet-scale batch scorer: takes a DataFrame with one row
    per active sub-zone/site (required columns: 'site_id', 'ambient_temp',
    'relative_humidity'; optional 'wind_speed_kmh' adds a Wind Chill
    column), and returns it with WBGT, Humidex, and (if wind data
    supplied) Wind Chill columns appended - computed vectorized across
    every row in one pass rather than N sequential Python function calls.
    Category labels reuse classify_humidex()/classify_wind_chill() via a
    single pandas .apply() pass each (those are branchy label lookups, not
    the numeric formulas - the formulas themselves are the vectorized
    part).

    Raises ValueError (not a silent empty result) if a required column is
    missing, so a malformed sites feed fails loudly rather than silently
    scoring garbage - consistent with this file's 'never guess at a
    number' discipline."""
    required = {"site_id", "ambient_temp", "relative_humidity"}
    missing = required - set(sites.columns)
    if missing:
        raise ValueError(f"calculate_multi_site_heat_risk: missing required columns {sorted(missing)}")

    out = sites.copy()
    out["wbgt_approx_c"] = np.round(
        wbgt_outdoor_approx_vectorized(out["ambient_temp"].to_numpy(), out["relative_humidity"].to_numpy()), 1
    )
    out["humidex_c"] = np.round(
        humidex_vectorized(out["ambient_temp"].to_numpy(), out["relative_humidity"].to_numpy()), 1
    )
    out["humidex_category"] = out["humidex_c"].apply(classify_humidex)

    if "wind_speed_kmh" in out.columns:
        out["wind_chill_c"] = wind_chill_c_vectorized(
            out["ambient_temp"].to_numpy(), out["wind_speed_kmh"].to_numpy()
        )
        out["wind_chill_category"] = out["wind_chill_c"].apply(classify_wind_chill)

    return out


# ===========================================================================
# Worker Physiology & Wearables (HSE Heart Pattern)
# ===========================================================================
# MEDICAL DISCLAIMER: this module estimates relative cardiovascular
# workload from wearable/manual heart-rate data using standard published
# formulas for occupational heat-stress screening; it is a workplace
# safety triage tool, not a medical device, and does not diagnose,
# monitor, or treat any medical condition - always follow site first-aid/
# emergency medical procedures for a worker in actual distress.

# Tanaka et al. (2001) age-predicted maximum heart rate - a widely cited,
# more accurate revision of the older "220 - age" rule of thumb.
def tanaka_max_heart_rate(age: float) -> float:
    """HRmax = 208 - 0.7 x age (Tanaka, Monahan & Seals, 2001)."""
    return 208.0 - 0.7 * age


# Workload-intensity heart-rate reserve add-on: how much additional %HRmax
# a given labeled workload band typically demands on top of ambient-heat
# load alone, expressed as a simple additive percentage-point nudge to the
# ambient-driven estimate below. Illustrative/harmonized, not a clinical
# calibration - see PHYSIOLOGICAL_STRAIN_SOURCE_NOTE.
_WORKLOAD_INTENSITY_STRAIN_PP = {"light": 0.0, "moderate": 6.0, "heavy": 14.0}

PHYSIOLOGICAL_STRAIN_SOURCE_NOTE = (
    "Screening heuristic combining Tanaka et al. (2001) age-predicted HRmax "
    "with ACGIH-aligned heat-strain reasoning (rising ambient WBGT/Humidex "
    "materially increases cardiovascular strain at a given external "
    "workload) and a simple hydration-loss proxy. This is a workplace "
    "triage signal, not a clinical or diagnostic measurement - it does not "
    "replace direct medical evaluation of a worker in distress."
)


def calculate_physiological_strain(
    heart_rate: float,
    age: float,
    ambient_temp: float,
    workload_intensity: str = "moderate",
) -> dict:
    """
    Screens relative cardiovascular strain from a real-time or manually
    logged heart-rate reading, cross-referenced against the worker's
    Tanaka-formula max heart rate, ambient heat, and workload intensity.

    heart_rate: current measured HR in bpm (wearable stream or manual
    safety check-in).
    age: worker age in years (never store a name/ID alongside this beyond
    an anonymous profile marker - see app.py's worker-strain dashboard).
    ambient_temp: current ambient temperature in deg C (drives the heat-
    amplification term and the illustrative core-temperature-drift proxy).
    workload_intensity: "light" | "moderate" | "heavy" (same vocabulary as
    the sidebar Workload Intensity selector already used for heat-stress
    reference panels elsewhere in this app).

    Returns a dict with: heart_rate, max_heart_rate, pct_hr_max,
    estimated_core_temp_c (Tci proxy), dehydration_risk_multiplier,
    status ("SAFE" | "WARNING" | "CRITICAL"), primary_hazard, drivers,
    and medical_disclaimer.
    """
    hr_max = tanaka_max_heart_rate(age)
    pct_hr_max = round(100.0 * heart_rate / hr_max, 1) if hr_max > 0 else 0.0

    intensity_pp = _WORKLOAD_INTENSITY_STRAIN_PP.get(workload_intensity, _WORKLOAD_INTENSITY_STRAIN_PP["moderate"])
    # Heat-amplification term: ambient temp above a 25C neutral baseline
    # adds proportional cardiovascular strain (illustrative, not a
    # clinical model) - matches the qualitative ACGIH/NIOSH observation
    # that heat load and physical workload compound on the heart, not just
    # on core temperature independently.
    heat_amplification_pp = max(0.0, (ambient_temp - 25.0) * 0.8)

    # Estimated Core Body Temperature (Tci) proxy: a simple, clearly-
    # labeled illustrative estimate (NOT a clinical core-temperature
    # measurement) combining resting baseline (37.0C), ambient heat load,
    # and workload/HR-driven metabolic heat, capped at a physiologically
    # plausible ceiling so an extreme HR reading can't produce a
    # nonsensical output.
    estimated_core_temp_c = round(
        min(41.0, 37.0 + 0.015 * max(0.0, heart_rate - 70.0) + 0.02 * max(0.0, ambient_temp - 25.0) + 0.01 * intensity_pp),
        2,
    )

    # Dehydration risk multiplier: a simple 1.0-3.0x illustrative scale
    # driven by sustained %HRmax and ambient heat - not a fluid-balance
    # measurement, purely a screening signal for "encourage a hydration/
    # rest break now" messaging.
    dehydration_risk_multiplier = round(
        1.0 + max(0.0, (pct_hr_max - 60.0) / 40.0) + max(0.0, (ambient_temp - 30.0) / 25.0),
        2,
    )
    dehydration_risk_multiplier = min(dehydration_risk_multiplier, 3.0)

    # Strict physiological status bands, driven primarily by %HRmax (the
    # single most established real-time cardiovascular-strain proxy),
    # with the heat-amplification and core-temp proxy able to escalate
    # (never downgrade) the band - a worker sitting at a borderline %HRmax
    # in extreme heat should not read as merely SAFE.
    if pct_hr_max >= 90.0 or estimated_core_temp_c >= 39.0:
        status = "CRITICAL"
    elif pct_hr_max >= 75.0 or estimated_core_temp_c >= 38.0 or heat_amplification_pp >= 12.0:
        status = "WARNING"
    else:
        status = "SAFE"

    return {
        "module": "Worker Physiology & Wearables",
        "heart_rate": heart_rate,
        "age": age,
        "max_heart_rate": round(hr_max, 1),
        "pct_hr_max": pct_hr_max,
        "estimated_core_temp_c": estimated_core_temp_c,
        "dehydration_risk_multiplier": dehydration_risk_multiplier,
        "status": status,
        "risk_band": status,
        "safety_override": status == "CRITICAL",
        "primary_hazard": "Excessive cardiovascular strain / heat-driven physiological overload",
        "workload_intensity": workload_intensity,
        "ambient_temp": ambient_temp,
        "drivers": {
            "Heart rate (bpm)": heart_rate,
            "Tanaka max HR (bpm)": round(hr_max, 1),
            "% of max HR": pct_hr_max,
            "Estimated core temp proxy (Tci, deg C)": estimated_core_temp_c,
            "Dehydration risk multiplier": dehydration_risk_multiplier,
            "Ambient temperature (deg C)": ambient_temp,
            "Workload intensity": workload_intensity,
        },
        "medical_disclaimer": (
            "This is a workplace safety screening estimate, not a medical diagnosis or "
            "device - a worker in genuine distress must receive immediate first aid / "
            "emergency medical attention regardless of this reading."
        ),
        "source_note": PHYSIOLOGICAL_STRAIN_SOURCE_NOTE,
    }


# ===========================================================================
# Acoustic Noise Exposure (equipment distance -> estimated dB -> legal dose)
# ===========================================================================

def estimate_noise_dba_at_distance(
    source_dba_at_reference_m: float,
    distance_m: float,
    reference_distance_m: float = 1.0,
) -> float:
    """
    Estimates sound pressure level at a given distance from a point-source
    noise emitter (generator, compressor, pile driver, etc.) using the
    inverse-square-law free-field approximation: a 6 dB reduction for
    every doubling of distance from the reference measurement point.
        L(d) = L(d0) - 20 * log10(d / d0)
    This is a free-field estimate (no reflective surfaces/enclosures
    modeled) - a genuine dosimeter reading always takes precedence over
    this estimate when available; use this for pre-task planning /
    screening when only the equipment's rated/reference noise level and
    approximate working distance are known.
    """
    distance_m = max(distance_m, 0.1)
    reference_distance_m = max(reference_distance_m, 0.1)
    return round(source_dba_at_reference_m - 20.0 * math.log10(distance_m / reference_distance_m), 1)


def calculate_acoustic_noise_exposure(
    source_dba_at_reference_m: float,
    distance_m: float,
    exposure_hours: float,
    reference_distance_m: float = 1.0,
    regulatory_profile: dict | None = None,
) -> dict:
    """
    Combines the inverse-square-law distance estimate above with the
    existing noise_dose_percent() formula (already used by Module 7 -
    Mining & Quarrying) to answer "at this working distance from this
    piece of equipment, for this many hours, what fraction of the
    selected country's legal daily noise dose does this represent?".
    Country-aware via regulatory_profile (noise_criterion_dba/
    noise_exchange_rate_db), same pattern as every other regulatory-
    profile-driven function in this file.
    """
    profile = _resolve_profile(regulatory_profile)
    estimated_dba = estimate_noise_dba_at_distance(source_dba_at_reference_m, distance_m, reference_distance_m)
    dose_pct = noise_dose_percent(
        estimated_dba, exposure_hours, profile["noise_criterion_dba"], profile["noise_exchange_rate_db"]
    )

    if dose_pct >= 200:
        band = "CRITICAL"
    elif dose_pct >= 100:
        band = "HIGH"
    elif dose_pct >= 50:
        band = "MODERATE"
    else:
        band = "LOW"

    return {
        "module": "Acoustic Noise Exposure",
        "estimated_dba_at_distance": estimated_dba,
        "distance_m": distance_m,
        "exposure_hours": exposure_hours,
        "noise_dose_pct": dose_pct,
        "risk_band": band,
        "safety_override": band == "CRITICAL",
        "primary_hazard": "Excessive occupational noise dose at estimated working distance",
        "regulatory_country_code": profile["country_code"],
        "regulatory_profile_label": profile["label"],
        "drivers": {
            "Source level at reference distance (dBA)": source_dba_at_reference_m,
            "Reference distance (m)": reference_distance_m,
            "Working distance (m)": distance_m,
            "Estimated level at working distance (dBA)": estimated_dba,
            "Exposure duration (hours)": exposure_hours,
            "Legal daily noise dose (%)": dose_pct,
            "Noise criterion (dBA)": profile["noise_criterion_dba"],
            "Exchange rate (dB)": profile["noise_exchange_rate_db"],
        },
    }


# ===========================================================================
# Extended Ambient Air Quality (PM2.5 / PM10 / O3 / NO2) screening
# ===========================================================================
# WHO Global Air Quality Guidelines (2021) 24-hour reference levels - a
# general ambient-air screening bar, NOT an occupational exposure limit
# and NOT a substitute for the module-specific, country-sourced
# respirable-crystalline-silica limits already in regulatory_country_
# thresholds.py (silica_action_level_ugm3 / SILICA_OEL_UGM3 above). This
# section answers a different question: "is today's general ambient air
# bad enough, independent of any dust the work itself generates, that
# respiratory PPE (FFP3) is warranted before work starts" - the kind of
# cross-check UK HSE/Safe Work Australia guidance both point to under
# their general 'control of substances hazardous to health' duties.
WHO_AQG_2021_24H_REFERENCE = {
    "pm25_ugm3": 15.0,
    "pm10_ugm3": 45.0,
    "o3_ugm3": 100.0,     # 8-hour peak season reference, used here as a same-day screening bar
    "no2_ugm3": 25.0,
}

AIR_QUALITY_SOURCE_NOTE = (
    "WHO Global Air Quality Guidelines (2021), 24-hour reference levels - a general "
    "ambient-air screening bar, not a country-specific occupational exposure limit. "
    "Cross-check against the module's own dust/silica OEL (regulatory_country_"
    "thresholds.py) for the legally binding figure that applies to generated dust."
)


def classify_ambient_air_quality(pm25_ugm3: float, pm10_ugm3: float = 0.0,
                                  o3_ugm3: float = 0.0, no2_ugm3: float = 0.0) -> dict:
    """
    Screens live PM2.5/PM10/O3/NO2 ambient readings against the WHO 2021
    reference levels above and recommends respiratory PPE (FFP3 mask)
    when ANY pollutant is materially exceeded (>1.5x reference - a
    precautionary screening multiplier, not itself a published health
    threshold). Never overrides or replaces a module's own silica-specific
    OEL exceedance logic - this is an independent, additive cross-check.
    """
    ratios = {
        "PM2.5": pm25_ugm3 / WHO_AQG_2021_24H_REFERENCE["pm25_ugm3"] if pm25_ugm3 else 0.0,
        "PM10": pm10_ugm3 / WHO_AQG_2021_24H_REFERENCE["pm10_ugm3"] if pm10_ugm3 else 0.0,
        "O3": o3_ugm3 / WHO_AQG_2021_24H_REFERENCE["o3_ugm3"] if o3_ugm3 else 0.0,
        "NO2": no2_ugm3 / WHO_AQG_2021_24H_REFERENCE["no2_ugm3"] if no2_ugm3 else 0.0,
    }
    worst_pollutant = max(ratios, key=ratios.get)
    worst_ratio = ratios[worst_pollutant]

    if worst_ratio >= 3.0:
        band = "CRITICAL"
    elif worst_ratio >= 1.5:
        band = "HIGH"
    elif worst_ratio >= 1.0:
        band = "MODERATE"
    else:
        band = "LOW"

    ffp3_required = worst_ratio >= 1.5

    return {
        "pm25_ugm3": pm25_ugm3,
        "pm10_ugm3": pm10_ugm3,
        "o3_ugm3": o3_ugm3,
        "no2_ugm3": no2_ugm3,
        "worst_pollutant": worst_pollutant,
        "worst_pollutant_ratio_to_reference": round(worst_ratio, 2),
        "risk_band": band,
        "ffp3_mask_required": ffp3_required,
        "source_note": AIR_QUALITY_SOURCE_NOTE,
    }
