"""
MAKU test suite
================
Covers all 5 risk_engine.py modules and their handoff into ai_advisor.py.
Per the project's Mathematical Isolation rule, these tests exercise the
engine functions directly (not the Streamlit pages, which are UI-only).

Run with:
    pytest
or:
    pytest -v test_app.py
"""

import pytest

from risk_engine import (
    calculate_solar_albedo_heat_risk,
    calculate_marine_humidex_risk,
    calculate_underground_kinetic_risk,
    calculate_high_rise_kinetic_risk,
    calculate_datacenter_kinetic_risk,
)
from ai_advisor import get_controls, generate_narrative, CONTROLS_MAP


REQUIRED_KEYS = {"module", "risk_band", "primary_hazard", "drivers", "safety_override"}


def _assert_standard_shape(result: dict):
    """Every module's return dict must carry the shared ai_advisor-compatible fields."""
    missing = REQUIRED_KEYS - result.keys()
    assert not missing, f"Missing compatibility fields: {missing}"
    assert result["module"] in CONTROLS_MAP, f"No CONTROLS_MAP entry for module {result['module']!r}"
    assert isinstance(result["safety_override"], bool)
    assert isinstance(result["drivers"], dict) and result["drivers"]


# ---------------------------------------------------------------------------
# Module 1: Solar (Desert)
# ---------------------------------------------------------------------------

class TestSolar:
    def test_low_risk_shape(self):
        r = calculate_solar_albedo_heat_risk(ghi=300, uv_index=3, ambient_temp=24, surface_type="pure_desert_sand")
        _assert_standard_shape(r)
        assert r["risk_level"] == "LOW"
        assert r["safety_override"] is False

    def test_critical_via_high_temp(self):
        r = calculate_solar_albedo_heat_risk(ghi=1100, uv_index=6, ambient_temp=48, surface_type="silicon_pv_panels")
        assert r["risk_level"] == "CRITICAL"
        assert r["override_required"] is True

    def test_critical_via_uv_alone(self):
        r = calculate_solar_albedo_heat_risk(ghi=200, uv_index=11, ambient_temp=25, surface_type="pure_desert_sand")
        assert r["risk_level"] == "CRITICAL"

    def test_unknown_surface_falls_back_to_default_albedo(self):
        r = calculate_solar_albedo_heat_risk(ghi=500, uv_index=5, ambient_temp=30, surface_type="not_a_real_surface")
        assert r["drivers"]["Albedo factor applied"] == pytest.approx(0.25)

    def test_pipeline_into_ai_advisor(self):
        r = calculate_solar_albedo_heat_risk(ghi=950, uv_index=9, ambient_temp=42, surface_type="hybrid_assembly_zone")
        controls = get_controls(r)
        assert isinstance(controls, list) and controls
        for lang in ("fr", "en"):
            narrative = generate_narrative(r, controls, api_key=None, lang=lang)
            assert isinstance(narrative, str) and narrative


# ---------------------------------------------------------------------------
# Module 2: Offshore (Marine)
# ---------------------------------------------------------------------------

class TestOffshore:
    def test_low_risk_normal_wind(self):
        r = calculate_marine_humidex_risk(ambient_temp=24, relative_humidity=55, wind_speed=8)
        _assert_standard_shape(r)
        assert r["risk_band"] == "Low"
        assert r["wind_risk_status"] == "Normal Operations"
        assert r["safety_override"] is False

    def test_wind_restricted_band(self):
        r = calculate_marine_humidex_risk(ambient_temp=25, relative_humidity=60, wind_speed=20)
        assert r["wind_risk_status"] == "Restricted - Monitor Closely"

    def test_wind_suspended_forces_override(self):
        r = calculate_marine_humidex_risk(ambient_temp=25, relative_humidity=60, wind_speed=27)
        assert r["wind_risk_status"] == "Suspended - Crane/Lifting Danger"
        assert r["safety_override"] is True

    def test_extreme_humidex_forces_override(self):
        r = calculate_marine_humidex_risk(ambient_temp=34, relative_humidity=98, wind_speed=5)
        assert r["risk_band"] == "Extreme"
        assert r["safety_override"] is True

    def test_pipeline_into_ai_advisor(self):
        r = calculate_marine_humidex_risk(ambient_temp=33, relative_humidity=92, wind_speed=15)
        controls = get_controls(r)
        assert isinstance(controls, list) and controls
        for lang in ("fr", "en"):
            narrative = generate_narrative(r, controls, api_key=None, lang=lang)
            assert isinstance(narrative, str) and narrative


# ---------------------------------------------------------------------------
# Module 3: Underground (Tunnel/Metro)
# ---------------------------------------------------------------------------

class TestUnderground:
    def test_low_risk_shape(self):
        r = calculate_underground_kinetic_risk(
            ambient_temp=22, geothermal_humidity=55, particulate_matter_pm25=20, gas_co_ppm=5,
        )
        _assert_standard_shape(r)
        assert r["risk_band"] == "LOW"
        assert r["safety_override"] is False

    def test_critical_via_heat(self):
        r = calculate_underground_kinetic_risk(
            ambient_temp=35, geothermal_humidity=95, particulate_matter_pm25=40, gas_co_ppm=8,
        )
        assert r["risk_band"] == "CRITICAL"
        assert r["perceived_temp"] > 42.0
        assert r["safety_override"] is True

    def test_critical_via_co_oel(self):
        r = calculate_underground_kinetic_risk(
            ambient_temp=25, geothermal_humidity=60, particulate_matter_pm25=40, gas_co_ppm=30,
        )
        assert r["gas_exceeds"] is True
        assert r["safety_override"] is True
        assert r["risk_band"] == "CRITICAL"

    def test_critical_via_pm25_oel(self):
        r = calculate_underground_kinetic_risk(
            ambient_temp=25, geothermal_humidity=60, particulate_matter_pm25=300, gas_co_ppm=8,
        )
        assert r["dust_exceeds"] is True
        assert r["safety_override"] is True

    def test_pipeline_into_ai_advisor(self):
        r = calculate_underground_kinetic_risk(
            ambient_temp=30, geothermal_humidity=80, particulate_matter_pm25=90, gas_co_ppm=12,
        )
        controls = get_controls(r)
        assert isinstance(controls, list) and controls
        for lang in ("fr", "en"):
            narrative = generate_narrative(r, controls, api_key=None, lang=lang)
            assert isinstance(narrative, str) and narrative


# ---------------------------------------------------------------------------
# Module 4: High-Rise (Vertical Urban)
# ---------------------------------------------------------------------------

class TestHighRise:
    def test_low_risk_shape(self):
        r = calculate_high_rise_kinetic_risk(ground_wind_speed_knots=8, floor_level=5, crane_load_mass_tons=10)
        _assert_standard_shape(r)
        assert r["risk_band"] == "LOW"
        assert r["safety_override"] is False

    def test_high_wind_forces_override(self):
        r = calculate_high_rise_kinetic_risk(ground_wind_speed_knots=25, floor_level=90, crane_load_mass_tons=15)
        assert r["scaled_wind_speed"] > 30.0
        assert r["safety_override"] is True
        assert r["risk_band"] == "CRITICAL"

    def test_light_load_oscillation_escalates_band_without_override(self):
        # Light crane load at moderate scaled wind should push oscillation-driven
        # severity up even while staying under the hard 30-knot override.
        r = calculate_high_rise_kinetic_risk(ground_wind_speed_knots=18, floor_level=60, crane_load_mass_tons=1)
        assert r["scaled_wind_speed"] <= 30.0
        assert r["safety_override"] is False
        assert r["risk_band"] in ("HIGH", "CRITICAL")

    def test_wind_scales_up_with_floor_level(self):
        low = calculate_high_rise_kinetic_risk(ground_wind_speed_knots=15, floor_level=1, crane_load_mass_tons=10)
        high = calculate_high_rise_kinetic_risk(ground_wind_speed_knots=15, floor_level=100, crane_load_mass_tons=10)
        assert high["scaled_wind_speed"] > low["scaled_wind_speed"]

    def test_pipeline_into_ai_advisor(self):
        r = calculate_high_rise_kinetic_risk(ground_wind_speed_knots=20, floor_level=150, crane_load_mass_tons=4)
        controls = get_controls(r)
        assert isinstance(controls, list) and controls
        for lang in ("fr", "en"):
            narrative = generate_narrative(r, controls, api_key=None, lang=lang)
            assert isinstance(narrative, str) and narrative


# ---------------------------------------------------------------------------
# Module 5: Data Center (Controlled Critical Environment)
# ---------------------------------------------------------------------------

class TestDataCenter:
    def test_low_risk_shape(self):
        r = calculate_datacenter_kinetic_risk(
            electrical_load_kw=100, hot_aisle_temp=26,
            ceiling_void_confined=False, gas_system_armed=False,
        )
        _assert_standard_shape(r)
        assert r["risk_band"] == "LOW"
        assert r["safety_override"] is False

    def test_arc_flash_danger_forces_override(self):
        r = calculate_datacenter_kinetic_risk(
            electrical_load_kw=1300, hot_aisle_temp=30,
            ceiling_void_confined=False, gas_system_armed=False,
        )
        assert r["arc_flash_danger"] is True
        assert r["safety_override"] is True
        assert r["risk_band"] == "CRITICAL"

    def test_thermal_critical_forces_override(self):
        r = calculate_datacenter_kinetic_risk(
            electrical_load_kw=200, hot_aisle_temp=48,
            ceiling_void_confined=False, gas_system_armed=False,
        )
        assert r["safety_override"] is True

    def test_confined_plus_armed_forces_override_even_at_low_load(self):
        r = calculate_datacenter_kinetic_risk(
            electrical_load_kw=150, hot_aisle_temp=28,
            ceiling_void_confined=True, gas_system_armed=True,
        )
        assert r["confined_armed_danger"] is True
        assert r["safety_override"] is True

    def test_confined_alone_without_armed_system_is_not_dangerous(self):
        r = calculate_datacenter_kinetic_risk(
            electrical_load_kw=150, hot_aisle_temp=28,
            ceiling_void_confined=True, gas_system_armed=False,
        )
        assert r["confined_armed_danger"] is False

    def test_thermal_control_reflects_actual_thermal_reading_not_overall_band(self):
        # Regression test for the bug caught during development: the
        # "thermal differential elevated" control must be driven by the
        # actual thermal_differential value, not by an overall CRITICAL
        # band caused purely by arc-flash danger.
        r = calculate_datacenter_kinetic_risk(
            electrical_load_kw=1300, hot_aisle_temp=30,
            ceiling_void_confined=False, gas_system_armed=False,
        )
        assert r["thermal_differential"] < 15.0
        controls = get_controls(r)
        assert not any("thermal differential" in c.lower() for c in controls)

    def test_pipeline_into_ai_advisor(self):
        r = calculate_datacenter_kinetic_risk(
            electrical_load_kw=400, hot_aisle_temp=36,
            ceiling_void_confined=False, gas_system_armed=True,
        )
        controls = get_controls(r)
        assert isinstance(controls, list) and controls
        for lang in ("fr", "en"):
            narrative = generate_narrative(r, controls, api_key=None, lang=lang)
            assert isinstance(narrative, str) and narrative


# ---------------------------------------------------------------------------
# Cross-module: every module registered in ai_advisor.CONTROLS_MAP
# ---------------------------------------------------------------------------

def test_all_five_modules_registered_in_controls_map():
    expected_modules = {
        "Solar (Desert)",
        "Offshore (Marine)",
        "Underground (Tunnel/Metro)",
        "High-Rise (Vertical Urban)",
        "Data Center (Controlled Critical Environment)",
    }
    assert expected_modules == set(CONTROLS_MAP.keys())
