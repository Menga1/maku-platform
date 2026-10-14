"""
Module registry: the inputs each risk module accepts, as data.
==============================================================
Field names are exactly the keyword arguments of the risk_engine.py
function, so the web app, an API and the tests all describe an assessment
the same way. Ranges are physical plausibility bounds (reject typos and
unit mistakes such as Fahrenheit-for-Celsius), not safety thresholds - the
thresholds live in risk_engine.py and regulatory_country_thresholds.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import risk_engine as engine


@dataclass(frozen=True)
class Field:
    name: str
    kind: str                      # "number" | "bool" | "choice"
    unit: str = ""
    minimum: float | None = None
    maximum: float | None = None
    choices: tuple[str, ...] = ()
    required: bool = True
    default: object = None
    description: str = ""


@dataclass(frozen=True)
class ModuleSpec:
    key: str
    name: str                      # result["module"] label used across MAKU
    function: Callable[..., dict]
    fields: tuple[Field, ...] = field(default_factory=tuple)
    description: str = ""


def num(name, unit, lo, hi, *, required=True, default=None, description=""):
    return Field(name, "number", unit, lo, hi, (), required, default, description)


def flag(name, *, default=False, description=""):
    return Field(name, "bool", "", None, None, (), False, default, description)


def choice(name, options, *, default=None, description=""):
    return Field(name, "choice", "", None, None, tuple(options), default is None, default, description)


MODULES: dict[str, ModuleSpec] = {m.key: m for m in [
    ModuleSpec("solar", "Solar (Desert)", engine.calculate_solar_albedo_heat_risk, (
        num("ghi", "W/m²", 0, 1500, description="Global horizontal irradiance"),
        num("uv_index", "", 0, 20),
        num("ambient_temp", "°C", -40, 65),
        choice("surface_type", engine.SOLAR_ALBEDO_FACTORS),
    ), "Desert heat stress from irradiance, UV and surface albedo"),
    ModuleSpec("offshore", "Offshore (Marine)", engine.calculate_marine_humidex_risk, (
        num("ambient_temp", "°C", -40, 60),
        num("relative_humidity", "%", 0, 100),
        num("wind_speed", "kn", 0, 250),
    ), "Marine Humidex and wind gate for crane/lifting"),
    ModuleSpec("underground", "Underground (Tunnel/Metro)", engine.calculate_underground_kinetic_risk, (
        num("ambient_temp", "°C", -20, 70),
        num("geothermal_humidity", "%", 0, 100),
        num("particulate_matter_pm25", "µg/m³", 0, 50000),
        num("gas_co_ppm", "ppm", 0, 10000),
    ), "Tunnel heat, CO and PM2.5 against occupational limits"),
    ModuleSpec("high_rise", "High-Rise (Vertical Urban)", engine.calculate_high_rise_kinetic_risk, (
        num("ground_wind_speed_knots", "kn", 0, 200, description="10 m reference wind"),
        num("floor_level", "floor", 0, 300),
        num("crane_load_mass_tons", "t", 0, 2000),
        choice("terrain", engine.WIND_TERRAIN_EXPONENTS, default=engine.DEFAULT_WIND_TERRAIN),
        num("floor_height_m", "m", 2, 12, required=False, default=3.5),
        num("measured_hook_wind_knots", "kn", 0, 200, required=False,
            description="Measured wind at working height; overrides the power-law estimate"),
    ), "Wind at working height (power law) versus crane lifts"),
    ModuleSpec("data_center", "Data Center (Controlled Critical Environment)", engine.calculate_datacenter_kinetic_risk, (
        num("electrical_load_kw", "kW", 0, 1_000_000, required=False,
            description="Recorded for context only; never used to estimate arc-flash energy"),
        num("hot_aisle_temp", "°C", -10, 80),
        flag("ceiling_void_confined"),
        flag("gas_system_armed"),
        num("label_incident_energy_cal", "cal/cm²", 0, 1000, required=False,
            description="From the equipment's arc-flash label (preferred source)"),
        num("voltage_kv", "kV", 0.05, 50, required=False),
        num("fault_current_ka", "kA", 0, 300, required=False),
        num("clearing_time_s", "s", 0, 10, required=False),
        num("working_distance_mm", "mm", 100, 3000, required=False, default=455.0),
        num("cold_aisle_temp_c", "°C", -10, 60, required=False, default=22.0),
        flag("energized_work_planned", default=True),
    ), "Arc-flash energy (label, else Lee screening, else unknown), aisle heat, confined space"),
    ModuleSpec("wind_energy", "Wind Energy (Onshore/Offshore)", engine.calculate_wind_energy_kinetic_risk, (
        num("hub_height_wind_speed_ms", "m/s", 0, 100),
        flag("is_offshore"),
        num("significant_wave_height_m", "m", 0, 30, required=False, default=0.0),
        num("flash_to_bang_sec", "s", 0, 600, required=False),
    ), "Hub-height access limits, lightning 30-30 rule, crew-transfer sea state"),
    ModuleSpec("mining_quarrying", "Mining & Quarrying", engine.calculate_mining_quarrying_kinetic_risk, (
        num("respirable_silica_ugm3", "µg/m³", 0, 100000),
        num("measured_noise_dba", "dB(A)", 0, 160),
        num("noise_exposure_hours", "h", 0, 24),
        num("measured_vibration_aw_ms2", "m/s²", 0, 30),
        num("vibration_exposure_hours", "h", 0, 24),
        num("noise_criterion_dba", "dB(A)", 70, 100, required=False),
        num("noise_exchange_rate_db", "dB", 3, 6, required=False),
    ), "Silica dust, noise dose and whole-body vibration"),
    ModuleSpec("marine_port", "Marine & Port Construction", engine.calculate_marine_port_kinetic_risk, (
        num("current_tide_level_m", "m", -10, 20),
        num("required_min_clearance_m", "m", 0, 20),
        flag("is_night_operation"),
        num("measured_illuminance_lux", "lx", 0, 200000),
        num("hardware_years_in_service", "years", 0, 100),
        choice("hardware_exposure_class", engine.CORROSION_ANNUAL_DERATE_PCT, default="C5M_marine_splash_zone"),
    ), "Tide clearance, night lighting and splash-zone corrosion"),
    ModuleSpec("heat_stress", "Occupational Heat Stress (ISO 7243 / ACGIH TLV)", engine.calculate_iso7243_heat_stress, (
        choice("workload_category", ("light", "moderate", "heavy", "very_heavy"), default="moderate"),
        choice("clothing_type", engine.CLOTHING_ADJUSTMENT_FACTOR_C, default="work_clothes"),
        flag("acclimatized"),
        choice("requested_work_rest_ratio", ("100/0", "75/25", "50/50", "25/75"), default="100/0"),
        num("wbgt_measured_c", "°C", 0, 60, required=False),
        num("air_temp_c", "°C", -40, 65, required=False),
        num("relative_humidity_pct", "%", 0, 100, required=False),
    ), "ACGIH TLV work/rest screening from WBGT, workload and clothing"),
]}

MODULE_KEY_BY_NAME = {m.name: k for k, m in MODULES.items()}
