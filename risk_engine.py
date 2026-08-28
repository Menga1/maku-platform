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

import math


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


def calculate_solar_albedo_heat_risk(ghi: float, uv_index: float, ambient_temp: float, surface_type: str) -> dict:
    """
    Computes local thermal accumulation driven by the albedo effect and
    returns the kinetic risk index for Solar (Desert) MEP crews.
    Ref: MAKU Project Concept - Module 1 (Desert Environment)
    """
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


def calculate_marine_humidex_risk(ambient_temp: float, relative_humidity: float, wind_speed: float) -> dict:
    """
    Computes the Marine Humidex heat-stress index (Environment Canada Humidex
    formula, built on the shared saturation-vapor-pressure helper) and
    cross-references it against offshore wind-gust kinetic risk thresholds
    for crane/lifting operations on exposed platforms/lay-barges.
    Ref: MAKU Project Concept - Module 2 (Marine Environment)

    wind_speed is expected in knots.
    """
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
PM25_OEL_LIMIT_UGM3 = 250.0                   # critical PM2.5 OEL threshold (ug/m3)
CO_OEL_LIMIT_PPM = 25.0                       # critical CO OEL threshold (ppm)

UNDERGROUND_HEAT_BANDS = [
    (32, "LOW"), (38, "MODERATE"), (42, "HIGH"), (999, "CRITICAL"),
]
PM25_BANDS = [
    (35, "LOW"), (150, "MODERATE"), (250, "HIGH"), (999999, "CRITICAL"),
]
CO_BANDS = [
    (9, "LOW"), (15, "MODERATE"), (25, "HIGH"), (9999, "CRITICAL"),
]
UNDERGROUND_SEVERITY_RANK = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


def calculate_underground_kinetic_risk(ambient_temp: float, geothermal_humidity: float,
                                        particulate_matter_pm25: float, gas_co_ppm: float) -> dict:
    """
    Models trapped-heat accumulation in enclosed tunnel/metro excavation faces
    (TBM heat emissions + near-saturated geothermal humidity, screened via the
    shared Humidex helper) alongside real-time OEL (Occupational Exposure
    Limit) checks for CO and PM2.5, generating a predictive safety override
    for MEP electrical crews pulling high-voltage cabling ahead of permanent
    ventilation commissioning.
    Ref: MAKU Project Concept - Module 3 (Underground Substructure Infrastructure)
    """
    # Trapped-heat + geothermal-humidity perceived temperature. Stagnant,
    # near-saturated tunnel air behaves like a Humidex problem rather than a
    # dry desert WBGT one, so this reuses the same helper as the marine module.
    perceived_temp = humidex(ambient_temp, geothermal_humidity)

    heat_band = risk_band(perceived_temp, UNDERGROUND_HEAT_BANDS)
    pm25_band = risk_band(particulate_matter_pm25, PM25_BANDS)
    co_band = risk_band(gas_co_ppm, CO_BANDS)

    gas_exceeds = gas_co_ppm > CO_OEL_LIMIT_PPM
    dust_exceeds = particulate_matter_pm25 > PM25_OEL_LIMIT_UGM3

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
CRANE_SUSPEND_WIND_KNOTS = 30.0     # scaled wind threshold forcing crane/lift suspension

WIND_SEVERITY_BANDS = [
    (15, "LOW"), (22, "MODERATE"), (30, "HIGH"), (999, "CRITICAL"),
]
OSCILLATION_SEVERITY_BANDS = [
    (10, "LOW"), (25, "MODERATE"), (50, "HIGH"), (999999, "CRITICAL"),
]
HIGH_RISE_SEVERITY_RANK = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


def calculate_high_rise_kinetic_risk(ground_wind_speed_knots: float, floor_level: float,
                                      crane_load_mass_tons: float) -> dict:
    """
    Models vertical wind-shear amplification through the urban boundary layer
    and the resulting crane-load oscillation risk for suspended lifts and
    facade/curtain-wall crews working at height.
    Ref: MAKU Project Concept - Module 4 (Vertical Urban Environment)
    """
    # Exponential wind-shear scaling: wind speed compounds with floor height
    # as the urban boundary layer thins and turbulence/shear intensify.
    scaled_wind_speed = ground_wind_speed_knots * math.exp(HIGH_RISE_WIND_GROWTH_RATE * floor_level)

    # Oscillation risk index: drag energy (~v^2) divided by load mass - lighter,
    # high-surface-area facade/curtain-wall loads oscillate far worse than dense
    # heavy structural loads under the same wind loading.
    safe_mass = max(crane_load_mass_tons, 0.5)
    oscillation_index = (scaled_wind_speed ** 2) / safe_mass

    wind_band = risk_band(scaled_wind_speed, WIND_SEVERITY_BANDS)
    oscillation_band = risk_band(oscillation_index, OSCILLATION_SEVERITY_BANDS)
    band = wind_band if HIGH_RISE_SEVERITY_RANK[wind_band] >= HIGH_RISE_SEVERITY_RANK[oscillation_band] else oscillation_band

    safety_override = scaled_wind_speed > CRANE_SUSPEND_WIND_KNOTS
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
                                       ceiling_void_confined: bool, gas_system_armed: bool) -> dict:
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
        "drivers": {
            "Electrical load (kW)": electrical_load_kw,
            "Hot-aisle temperature (C)": hot_aisle_temp,
            "Assumed cold-aisle target (C)": assumed_cold_aisle_c,
            "Confined ceiling-void space": ceiling_void_confined,
            "Gaseous suppression system armed": gas_system_armed,
        },
    }
