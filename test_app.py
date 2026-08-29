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
from unittest.mock import patch, MagicMock

import streamlit as st

from risk_engine import (
    calculate_solar_albedo_heat_risk,
    calculate_marine_humidex_risk,
    calculate_underground_kinetic_risk,
    calculate_high_rise_kinetic_risk,
    calculate_datacenter_kinetic_risk,
    calculate_wind_energy_kinetic_risk,
    calculate_mining_quarrying_kinetic_risk,
    calculate_marine_port_kinetic_risk,
    noise_dose_percent,
    whole_body_vibration_a8,
    corroded_capacity_pct,
)
from ai_advisor import (
    get_controls, generate_narrative, get_regulatory_references, get_bibliography, CONTROLS_MAP,
    translate_narrative, generate_daily_briefing, predict_forecast_breach,
    generate_predictive_alert, classify_api_error,
)
from regulatory_references import get_references, get_further_reading, REGULATORY_REFERENCES
from regulatory_country_thresholds import (
    get_country_thresholds, is_midday_outdoor_ban_active, get_regulatory_profile, resolve_heat_stress_limit,
)
from ui_helpers import _build_report_pdf
from analytics import (
    log_assessment, get_log_dataframe, merge_uploaded_csv,
    monthly_summary, build_monthly_excel, LOG_COLUMNS,
)
from data_feeds import (
    fetch_solar_forecast, fetch_offshore_forecast, DataFeedError,
    fetch_live_weather_universal, _mock_universal_weather,
)


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

    def test_regulatory_profile_changes_real_safety_outcome(self):
        # Same physical wind speed: France's stricter (illustrative) crane
        # suspend threshold triggers a safety override that the harmonized
        # USA default does not - proves the profile genuinely drives the
        # engine's decision, not just a cosmetic label.
        r_usa = calculate_high_rise_kinetic_risk(20.5, 40, 4)
        r_fr = calculate_high_rise_kinetic_risk(20.5, 40, 4, regulatory_profile=get_regulatory_profile("FRANCE"))
        assert r_usa["safety_override"] is False
        assert r_fr["safety_override"] is True
        assert r_usa["regulatory_country_code"] == "USA"
        assert r_fr["regulatory_country_code"] == "FRANCE"

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
# Module 6: Wind Energy (Onshore/Offshore)
# ---------------------------------------------------------------------------

class TestWindEnergy:
    def test_low_wind_onshore_shape(self):
        r = calculate_wind_energy_kinetic_risk(6.0)
        _assert_standard_shape(r)
        assert r["risk_band"] == "LOW"
        assert r["safety_override"] is False

    def test_high_wind_forces_critical_and_override(self):
        r = calculate_wind_energy_kinetic_risk(21.0)
        assert r["risk_band"] == "CRITICAL"
        assert r["safety_override"] is True

    def test_restricted_band_between_thresholds(self):
        r = calculate_wind_energy_kinetic_risk(16.0)
        assert r["risk_band"] == "HIGH"
        assert r["safety_override"] is False

    def test_lightning_30_30_rule_forces_override_even_at_low_wind(self):
        r = calculate_wind_energy_kinetic_risk(5.0, flash_to_bang_sec=12.0)
        assert "STOP WORK" in r["lightning_status"]
        assert r["safety_override"] is True

    def test_lightning_above_30s_does_not_trigger_stop(self):
        r = calculate_wind_energy_kinetic_risk(5.0, flash_to_bang_sec=45.0)
        assert "STOP WORK" not in r["lightning_status"]
        assert r["safety_override"] is False

    def test_offshore_rough_seas_suspend_ctv_and_forces_override(self):
        r = calculate_wind_energy_kinetic_risk(5.0, is_offshore=True, significant_wave_height_m=2.5)
        assert "Suspended" in r["ctv_transfer_status"]
        assert r["safety_override"] is True

    def test_onshore_ignores_sea_state(self):
        r = calculate_wind_energy_kinetic_risk(5.0, is_offshore=False, significant_wave_height_m=5.0)
        assert r["ctv_transfer_status"] == "Not applicable (onshore)"
        assert r["safety_override"] is False

    def test_pipeline_into_ai_advisor(self):
        r = calculate_wind_energy_kinetic_risk(22.0, is_offshore=True, significant_wave_height_m=2.5, flash_to_bang_sec=10)
        controls = get_controls(r)
        assert isinstance(controls, list) and controls
        assert any("SAFETY OVERRIDE" in c for c in controls)
        for lang in ("fr", "en", "ar", "es"):
            narrative = generate_narrative(r, controls, api_key=None, lang=lang)
            assert isinstance(narrative, str) and narrative


# ---------------------------------------------------------------------------
# Module 7: Mining & Quarrying
# ---------------------------------------------------------------------------

class TestMiningQuarrying:
    def test_low_risk_shape(self):
        r = calculate_mining_quarrying_kinetic_risk(
            respirable_silica_ugm3=10, measured_noise_dba=75, noise_exposure_hours=8,
            measured_vibration_aw_ms2=0.2, vibration_exposure_hours=8,
        )
        _assert_standard_shape(r)
        assert r["risk_band"] == "LOW"
        assert r["safety_override"] is False

    def test_silica_over_oel_forces_override(self):
        r = calculate_mining_quarrying_kinetic_risk(
            respirable_silica_ugm3=60, measured_noise_dba=75, noise_exposure_hours=8,
            measured_vibration_aw_ms2=0.2, vibration_exposure_hours=8,
        )
        assert r["silica_exceeds_oel"] is True
        assert r["safety_override"] is True
        assert r["risk_band"] == "CRITICAL"

    def test_silica_action_level_high_band_no_override(self):
        r = calculate_mining_quarrying_kinetic_risk(
            respirable_silica_ugm3=35, measured_noise_dba=75, noise_exposure_hours=8,
            measured_vibration_aw_ms2=0.2, vibration_exposure_hours=8,
        )
        assert r["silica_exceeds_oel"] is False
        assert r["safety_override"] is False
        assert r["risk_band"] == "HIGH"

    def test_vibration_exceeds_limit_forces_override(self):
        r = calculate_mining_quarrying_kinetic_risk(
            respirable_silica_ugm3=10, measured_noise_dba=75, noise_exposure_hours=8,
            measured_vibration_aw_ms2=1.5, vibration_exposure_hours=8,
        )
        assert r["vibration_exceeds_limit"] is True
        assert r["safety_override"] is True

    def test_noise_dose_formula_matches_standard_exchange_rate_math(self):
        # At exactly the 90 dBA criterion for a full 8h shift, dose should be 100%.
        assert noise_dose_percent(90.0, 8.0) == 100.0
        # 3 dB above criterion with a 3 dB exchange rate halves the allowed time.
        assert noise_dose_percent(93.0, 8.0, criterion_dba=90.0, exchange_rate_db=3.0) == 200.0

    def test_whole_body_vibration_a8_normalizes_duration(self):
        # Same instantaneous a_w, shorter exposure -> lower A(8).
        full_day = whole_body_vibration_a8(1.0, 8.0)
        half_day = whole_body_vibration_a8(1.0, 2.0)
        assert half_day < full_day
        assert full_day == 1.0

    def test_pipeline_into_ai_advisor(self):
        r = calculate_mining_quarrying_kinetic_risk(
            respirable_silica_ugm3=60, measured_noise_dba=100, noise_exposure_hours=8,
            measured_vibration_aw_ms2=1.5, vibration_exposure_hours=8,
        )
        controls = get_controls(r)
        assert isinstance(controls, list) and controls
        assert any("SAFETY OVERRIDE" in c for c in controls)
        for lang in ("fr", "en", "ar", "es"):
            narrative = generate_narrative(r, controls, api_key=None, lang=lang)
            assert isinstance(narrative, str) and narrative


# ---------------------------------------------------------------------------
# Module 8: Marine & Port Construction
# ---------------------------------------------------------------------------

class TestMarinePortConstruction:
    def test_low_risk_shape(self):
        r = calculate_marine_port_kinetic_risk(
            current_tide_level_m=2.0, required_min_clearance_m=1.0,
            is_night_operation=False, measured_illuminance_lux=200,
            hardware_years_in_service=1,
        )
        _assert_standard_shape(r)
        assert r["risk_band"] == "LOW"
        assert r["safety_override"] is False

    def test_critical_tide_clearance_forces_override(self):
        r = calculate_marine_port_kinetic_risk(
            current_tide_level_m=1.1, required_min_clearance_m=1.0,
            is_night_operation=False, measured_illuminance_lux=200,
            hardware_years_in_service=1,
        )
        assert r["tide_clearance_margin_m"] <= 0.3
        assert r["safety_override"] is True

    def test_night_amplification_escalates_band(self):
        night_r = calculate_marine_port_kinetic_risk(
            current_tide_level_m=1.7, required_min_clearance_m=1.0,
            is_night_operation=True, measured_illuminance_lux=20,
            hardware_years_in_service=1,
        )
        day_r = calculate_marine_port_kinetic_risk(
            current_tide_level_m=1.7, required_min_clearance_m=1.0,
            is_night_operation=False, measured_illuminance_lux=20,
            hardware_years_in_service=1,
        )
        assert night_r["night_amplified"] is True
        assert day_r["night_amplified"] is False

    def test_adequate_night_lighting_does_not_amplify(self):
        r = calculate_marine_port_kinetic_risk(
            current_tide_level_m=2.0, required_min_clearance_m=1.0,
            is_night_operation=True, measured_illuminance_lux=200,
            hardware_years_in_service=1,
        )
        assert r["night_amplified"] is False

    def test_old_hardware_forces_override_via_low_remaining_capacity(self):
        r = calculate_marine_port_kinetic_risk(
            current_tide_level_m=2.0, required_min_clearance_m=1.0,
            is_night_operation=False, measured_illuminance_lux=200,
            hardware_years_in_service=15, hardware_exposure_class="C5M_marine_splash_zone",
        )
        assert r["hardware_remaining_capacity_pct"] < 70.0
        assert r["safety_override"] is True

    def test_corrosion_derating_never_goes_negative(self):
        assert corroded_capacity_pct(1000, "C5M_marine_splash_zone") == 0.0

    def test_pipeline_into_ai_advisor(self):
        r = calculate_marine_port_kinetic_risk(
            current_tide_level_m=1.1, required_min_clearance_m=1.0,
            is_night_operation=True, measured_illuminance_lux=20,
            hardware_years_in_service=15,
        )
        controls = get_controls(r)
        assert isinstance(controls, list) and controls
        assert any("SAFETY OVERRIDE" in c for c in controls)
        for lang in ("fr", "en", "ar", "es"):
            narrative = generate_narrative(r, controls, api_key=None, lang=lang)
            assert isinstance(narrative, str) and narrative


# ---------------------------------------------------------------------------
# Module 5a: Country-specific regulatory thresholds
# ---------------------------------------------------------------------------

class TestCountryThresholds:
    def test_us_matches_harmonized_defaults(self):
        cfg = get_country_thresholds("USA")
        assert cfg["noise_criterion_dba"] == 90.0
        assert cfg["noise_exchange_rate_db"] == 5.0
        assert cfg["midday_outdoor_work_ban"] is False

    def test_france_uses_stricter_eu_noise_limits(self):
        cfg = get_country_thresholds("FRANCE")
        assert cfg["noise_criterion_dba"] == 85.0
        assert cfg["noise_exchange_rate_db"] == 3.0

    def test_uae_has_midday_ban_flag(self):
        cfg = get_country_thresholds("UAE")
        assert cfg["midday_outdoor_work_ban"] is True

    def test_unknown_country_falls_back_to_harmonized_default(self):
        cfg = get_country_thresholds("ZZ_NOT_REAL")
        assert cfg["country_code"] == "USA"
        assert cfg["noise_criterion_dba"] == 90.0

    def test_noise_formula_accepts_country_specific_parameters(self):
        # Same 87 dBA / 8h reading: France's stricter criterion should
        # report a higher dose than the US's more lenient one.
        us_dose = noise_dose_percent(87.0, 8.0, criterion_dba=90.0, exchange_rate_db=5.0)
        fr_dose = noise_dose_percent(87.0, 8.0, criterion_dba=85.0, exchange_rate_db=3.0)
        assert fr_dose > us_dose

    def test_uae_midday_ban_active_in_season_and_hours(self):
        from datetime import date
        assert is_midday_outdoor_ban_active("UAE", date(2026, 7, 15), 13, 0) is True
        assert is_midday_outdoor_ban_active("UAE", date(2026, 1, 15), 13, 0) is False
        assert is_midday_outdoor_ban_active("USA", date(2026, 7, 15), 13, 0) is False

    def test_heat_stress_method_differs_between_usa_and_france(self):
        usa = get_country_thresholds("USA")
        france = get_country_thresholds("FRANCE")
        assert usa["heat_stress"]["method"] == "ACGIH"
        assert france["heat_stress"]["method"] == "ISO7243"

    def test_crane_wind_shear_thresholds_present_for_all_three(self):
        for code in ("USA", "FRANCE", "UAE"):
            cfg = get_country_thresholds(code)
            assert cfg["wind_shear"]["crane_suspend_knots"] > cfg["wind_shear"]["crane_restrict_knots"]

    def test_ambient_pm25_differs_by_country_with_distinct_averaging_periods(self):
        usa = get_country_thresholds("USA")
        france = get_country_thresholds("FRANCE")
        uae = get_country_thresholds("UAE")
        assert usa["air_quality"]["ambient_averaging_period"] == "24-hour"
        assert france["air_quality"]["ambient_averaging_period"] == "annual"
        assert uae["air_quality"]["ambient_averaging_period"] == "24-hour"

    def test_occupational_oel_stays_harmonized_across_all_three(self):
        # Per the honesty note in regulatory_country_thresholds.py: no
        # country has a distinct published occupational PM2.5/CO OEL, so
        # all three should be identical (not a fabricated difference).
        profiles = [get_country_thresholds(c) for c in ("USA", "FRANCE", "UAE")]
        pm25_oels = {p["air_quality"]["pm25_oel_ugm3"] for p in profiles}
        co_oels = {p["air_quality"]["co_oel_ppm"] for p in profiles}
        assert len(pm25_oels) == 1
        assert len(co_oels) == 1

    def test_resolve_heat_stress_limit_acgih_uses_work_rest_ratio(self):
        usa = get_country_thresholds("USA")
        light_full = resolve_heat_stress_limit(usa, "light", "100/0")
        light_rested = resolve_heat_stress_limit(usa, "light", "25/75")
        assert light_rested["limit"] > light_full["limit"]

    def test_resolve_heat_stress_limit_iso7243_ignores_work_rest_ratio(self):
        france = get_country_thresholds("FRANCE")
        a = resolve_heat_stress_limit(france, "moderate", "100/0")
        b = resolve_heat_stress_limit(france, "moderate", "25/75")
        assert a["limit"] == b["limit"]


# ---------------------------------------------------------------------------
# Module 1 (i18n part 2): translate_narrative honesty guarantees
# ---------------------------------------------------------------------------

class TestTranslateNarrative:
    def test_no_api_key_returns_original_text_unchanged(self):
        original = "Risk level: HIGH."
        result = translate_narrative(original, "ar", api_key=None)
        assert result["text"] == original
        assert result["translated"] is False
        assert result["error_kind"] == "no_api_key"

    def test_unsupported_language_does_not_crash(self):
        result = translate_narrative("test", "zz_not_a_language", api_key="whatever")
        assert result["translated"] is False
        assert result["error_kind"] == "unsupported_language"

    def test_bad_key_fails_gracefully_without_fabricating_translation(self):
        original = "Risk level: HIGH."
        result = translate_narrative(original, "es", api_key="clearly_invalid_key")
        assert result["translated"] is False
        assert result["text"] == original  # never returns a fabricated/garbled "translation"


# ---------------------------------------------------------------------------
# Module 4: Daily briefing + predictive forecasting
# ---------------------------------------------------------------------------

class TestDailyBriefing:
    def test_fallback_template_used_without_api_key(self):
        result = generate_daily_briefing(
            "Test Site", ["Task A", "Task B"], {"temp": 30}, api_key=None, lang="en",
        )
        assert result["source"] == "template"
        assert "Task A" in result["script"] and "Task B" in result["script"]

    def test_fallback_handles_empty_task_list(self):
        result = generate_daily_briefing("Test Site", [], {"temp": 30}, api_key=None, lang="fr")
        assert isinstance(result["script"], str) and result["script"]


class TestPredictiveForecasting:
    def test_no_breach_when_forecast_stays_in_same_band(self):
        current = {"ghi": 500, "uv_index": 5, "ambient_temp": 30, "surface_type": "hybrid_assembly_zone"}
        forecast = [{"ghi": 510, "uv_index": 5, "ambient_temp": 31, "surface_type": "hybrid_assembly_zone", "label": "in 1h"}]
        result = predict_forecast_breach(calculate_solar_albedo_heat_risk, current, forecast)
        assert result["will_breach"] is False
        assert generate_predictive_alert(result, "en") is None

    def test_breach_detected_and_labeled_correctly(self):
        current = {"ghi": 500, "uv_index": 5, "ambient_temp": 30, "surface_type": "hybrid_assembly_zone"}
        forecast = [
            {"ghi": 700, "uv_index": 8, "ambient_temp": 38, "surface_type": "hybrid_assembly_zone", "label": "in 2h"},
            {"ghi": 950, "uv_index": 11, "ambient_temp": 45, "surface_type": "hybrid_assembly_zone", "label": "in 4h"},
        ]
        result = predict_forecast_breach(calculate_solar_albedo_heat_risk, current, forecast)
        assert result["will_breach"] is True
        assert result["breach_label"] == "in 2h"  # first breach point, not the worst one
        for lang in ("fr", "en", "ar", "es"):
            alert = generate_predictive_alert(result, lang)
            assert isinstance(alert, str) and alert

    def test_already_critical_short_circuits_before_checking_forecast(self):
        current = {"ghi": 1200, "uv_index": 12, "ambient_temp": 48, "surface_type": "hybrid_assembly_zone"}
        forecast = [{"ghi": 100, "uv_index": 1, "ambient_temp": 20, "surface_type": "hybrid_assembly_zone", "label": "in 1h"}]
        result = predict_forecast_breach(calculate_solar_albedo_heat_risk, current, forecast)
        assert result["currently_critical"] is True
        assert result["will_breach"] is False

    def test_works_across_a_different_module_signature_unchanged(self):
        # Same generic function, wind energy's completely different kwargs -
        # proves this isn't hardcoded to the solar module's parameter names.
        current = {"hub_height_wind_speed_ms": 6.0}
        forecast = [{"hub_height_wind_speed_ms": 21.0, "label": "in 3h"}]
        result = predict_forecast_breach(calculate_wind_energy_kinetic_risk, current, forecast)
        assert result["will_breach"] is True
        assert result["breach_label"] == "in 3h"


# ---------------------------------------------------------------------------
# Module 5b: API error classification (offline-first support)
# ---------------------------------------------------------------------------

class TestClassifyApiError:
    def test_connection_error_classified_as_network(self):
        import requests
        assert classify_api_error(requests.exceptions.ConnectionError("no route to host")) == "network"

    def test_timeout_classified_as_timeout(self):
        import requests
        assert classify_api_error(requests.exceptions.Timeout("timed out")) == "timeout"

    def test_auth_failure_classified_as_auth(self):
        assert classify_api_error(Exception("401 Unauthorized: invalid x-api-key")) == "auth"

    def test_rate_limit_classified_correctly(self):
        assert classify_api_error(Exception("429 Too Many Requests - rate limit exceeded")) == "rate_limit"

    def test_unknown_error_classified_as_other(self):
        assert classify_api_error(Exception("something completely unexpected")) == "other"


# ---------------------------------------------------------------------------
# Module 3: Universal weather ingestion fallback chain
# ---------------------------------------------------------------------------

class TestUniversalWeatherFeed:
    def test_mock_fallback_has_all_expected_fields(self):
        mock = _mock_universal_weather(24.95, 53.90)
        expected_fields = {
            "temperature_2m", "relative_humidity_2m", "wind_speed_10m_kn",
            "wind_gusts_10m_kn", "uv_index", "pressure_hpa", "fetched_at", "source",
        }
        assert expected_fields.issubset(mock.keys())

    def test_falls_back_to_mock_when_no_key_and_network_blocked(self):
        # In this sandboxed test environment, api.open-meteo.com is not on
        # the allowed egress list, so this genuinely exercises the real
        # fallback path end-to-end rather than mocking it away.
        result = fetch_live_weather_universal(24.95, 53.90)
        assert result["source"] in ("Mock fallback data (no live network reachable)",
                                     "Open-Meteo /v1/forecast")

    def test_raises_when_mock_fallback_disabled_and_all_providers_fail(self):
        with patch("data_feeds._fetch_open_meteo_universal", side_effect=Exception("simulated network failure")):
            with pytest.raises(DataFeedError):
                fetch_live_weather_universal(1.0, 1.0, allow_mock_fallback=False)


# ---------------------------------------------------------------------------
# Cross-module: every module registered in ai_advisor.CONTROLS_MAP
# ---------------------------------------------------------------------------

def test_all_eight_modules_registered_in_controls_map():
    expected_modules = {
        "Solar (Desert)",
        "Offshore (Marine)",
        "Underground (Tunnel/Metro)",
        "High-Rise (Vertical Urban)",
        "Data Center (Controlled Critical Environment)",
        "Wind Energy (Onshore/Offshore)",
        "Mining & Quarrying",
        "Marine & Port Construction",
    }
    assert expected_modules == set(CONTROLS_MAP.keys())


# ---------------------------------------------------------------------------
# Regulatory references & bibliography
# ---------------------------------------------------------------------------

class TestRegulatoryReferences:
    def test_every_controls_map_module_has_references(self):
        # Every module ai_advisor knows about must have a citation list -
        # a silently-empty references section would be a regression.
        for module in CONTROLS_MAP.keys():
            refs = get_references(module)
            assert len(refs) >= 3, f"{module} has too few regulatory references"

    def test_reference_entries_have_required_fields(self):
        for module, refs in REGULATORY_REFERENCES.items():
            for ref in refs:
                assert ref.get("region")
                assert ref.get("body")
                assert ref.get("doc")
                # Every reference must be a citation (name + optional link),
                # never a large text blob - this is a proxy check against
                # accidentally pasting reproduced regulation/book text in.
                assert len(ref["doc"]) < 300

    def test_unknown_module_returns_empty_list_not_error(self):
        assert get_references("Not A Real Module") == []

    def test_further_reading_cites_brauer_by_name_only(self):
        biblio = get_further_reading()
        authors = [entry["author"] for entry in biblio]
        assert "Roger L. Brauer" in authors
        brauer_entry = next(e for e in biblio if e["author"] == "Roger L. Brauer")
        # Citation only (title/publisher/short note) - not book content.
        assert len(brauer_entry.get("note", "")) < 300

    def test_ai_advisor_wrapper_functions_match_underlying_module(self):
        result = calculate_solar_albedo_heat_risk(500, 5, 30, "pure_desert_sand")
        assert get_regulatory_references(result) == get_references(result["module"])
        assert get_bibliography() == get_further_reading()

    def test_narrative_regulatory_basis_only_names_cited_bodies(self):
        # Regression test: the AI narrative's "regulatory basis" line must be
        # built from the same verified reference list, never a separate
        # hardcoded/unverified list (this caught a real bug where an
        # unverified "Bauer temporary-works principles" claim had been
        # hardcoded directly into the narrative generator).
        result = calculate_underground_kinetic_risk(30, 85, 100, 15)
        controls = get_controls(result)
        narrative = generate_narrative(result, controls, api_key=None, lang="fr")
        cited_bodies = {ref["body"] for ref in get_references(result["module"])}
        assert cited_bodies, "expected at least one cited body for this module"
        assert any(body in narrative for body in cited_bodies)
        assert "Bauer" not in narrative


# ---------------------------------------------------------------------------
# PDF report generation
# ---------------------------------------------------------------------------

class TestPdfReport:
    def test_pdf_is_valid_for_every_module(self):
        cases = [
            calculate_solar_albedo_heat_risk(950, 9, 42, "silicon_pv_panels"),
            calculate_marine_humidex_risk(33, 92, 15),
            calculate_underground_kinetic_risk(30, 80, 90, 12),
            calculate_high_rise_kinetic_risk(20, 150, 4),
            calculate_datacenter_kinetic_risk(400, 36, False, True),
        ]
        for result in cases:
            controls = get_controls(result)
            narrative = generate_narrative(result, controls, api_key=None, lang="fr")
            refs = get_regulatory_references(result)
            biblio = get_bibliography()
            pdf_bytes = _build_report_pdf(result, narrative, controls, refs, biblio, "2026-01-01 00:00 UTC", "fr")
            assert isinstance(pdf_bytes, bytes)
            assert pdf_bytes[:5] == b"%PDF-", f"invalid PDF header for {result['module']}"
            assert len(pdf_bytes) > 1000, f"suspiciously small PDF for {result['module']}"

    def test_pdf_handles_empty_result_gracefully(self):
        # Dashboard report before any assessment has been run - result/
        # narrative/controls/references can all be empty. Must not crash.
        pdf_bytes = _build_report_pdf({}, "", [], [], get_bibliography(), "2026-01-01 00:00 UTC", "en")
        assert pdf_bytes[:5] == b"%PDF-"

    def test_pdf_strips_unencodable_characters_without_crashing(self):
        # fpdf2's core font can't encode emoji/non-Latin-1 characters -
        # _pdf_safe must strip them rather than let the PDF build crash.
        result = {"module": "Solar (Desert)", "risk_band": "CRITICAL", "primary_hazard": "test"}
        controls = ["🚨 emoji-prefixed control that must not crash PDF generation"]
        pdf_bytes = _build_report_pdf(result, "narrative with emoji 🔥", controls, [], [], "2026-01-01 00:00 UTC", "en")
        assert pdf_bytes[:5] == b"%PDF-"


# ---------------------------------------------------------------------------
# Live API request construction (mocked - no real network call)
# ---------------------------------------------------------------------------

class TestGenerateNarrativeRequest:
    """Verifies the actual request built for the Anthropic API - the source
    of the original bug where the prompt instructed the model to invoke
    unverified 'Roger Bauer... principles'. These tests inspect the real
    request payload (via mocking requests.post) rather than just the
    offline fallback text, since that's where the bug actually lived."""

    def _mock_response(self, text="mock narrative"):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"content": [{"type": "text", "text": text}]}
        return mock_resp

    def test_prompt_never_mentions_bauer_or_brauer(self):
        result = calculate_underground_kinetic_risk(30, 85, 100, 15)
        controls = get_controls(result)
        with patch("ai_advisor.requests.post") as mock_post:
            mock_post.return_value = self._mock_response()
            generate_narrative(result, controls, api_key="fake-key-for-test", lang="fr")
            sent_json = mock_post.call_args.kwargs["json"]
            prompt_text = sent_json["messages"][0]["content"]
            assert "Bauer" not in prompt_text
            assert "Brauer" not in prompt_text
            assert "invent" in prompt_text.lower()  # anti-fabrication instruction present

    def test_web_search_tool_absent_by_default(self):
        result = calculate_solar_albedo_heat_risk(500, 5, 30, "pure_desert_sand")
        controls = get_controls(result)
        with patch("ai_advisor.requests.post") as mock_post:
            mock_post.return_value = self._mock_response()
            generate_narrative(result, controls, api_key="fake-key", lang="en", enable_web_search=False)
            sent_json = mock_post.call_args.kwargs["json"]
            assert "tools" not in sent_json

    def test_web_search_tool_present_when_enabled(self):
        result = calculate_solar_albedo_heat_risk(500, 5, 30, "pure_desert_sand")
        controls = get_controls(result)
        with patch("ai_advisor.requests.post") as mock_post:
            mock_post.return_value = self._mock_response()
            generate_narrative(result, controls, api_key="fake-key", lang="en", enable_web_search=True)
            sent_json = mock_post.call_args.kwargs["json"]
            assert "tools" in sent_json
            assert sent_json["tools"][0]["type"] == "web_search_20250305"

    def test_prompt_includes_verified_references_for_module(self):
        result = calculate_datacenter_kinetic_risk(1300, 30, False, False)
        controls = get_controls(result)
        expected_bodies = {ref["body"] for ref in get_references(result["module"])}
        with patch("ai_advisor.requests.post") as mock_post:
            mock_post.return_value = self._mock_response()
            generate_narrative(result, controls, api_key="fake-key", lang="en")
            sent_json = mock_post.call_args.kwargs["json"]
            prompt_text = sent_json["messages"][0]["content"]
            assert any(body in prompt_text for body in expected_bodies)

    def test_no_api_key_never_calls_the_network(self):
        result = calculate_high_rise_kinetic_risk(15, 40, 8)
        controls = get_controls(result)
        with patch("ai_advisor.requests.post") as mock_post:
            narrative = generate_narrative(result, controls, api_key="", lang="fr", enable_web_search=True)
            mock_post.assert_not_called()
            assert isinstance(narrative, str) and narrative


# ---------------------------------------------------------------------------
# Assessment log & monthly Excel export (analytics.py)
# ---------------------------------------------------------------------------

class TestAnalyticsLog:
    def setup_method(self):
        st.session_state.clear()

    def test_log_assessment_appends_row(self):
        r = calculate_solar_albedo_heat_risk(950, 9, 42, "silicon_pv_panels")
        log_assessment(st, r)
        df = get_log_dataframe(st)
        assert len(df) == 1
        assert df.iloc[0]["module"] == "Solar (Desert)"
        assert list(df.columns) == LOG_COLUMNS

    def test_log_accumulates_across_multiple_calls(self):
        log_assessment(st, calculate_solar_albedo_heat_risk(950, 9, 42, "silicon_pv_panels"))
        log_assessment(st, calculate_high_rise_kinetic_risk(25, 90, 15))
        df = get_log_dataframe(st)
        assert len(df) == 2

    def test_empty_log_returns_empty_dataframe_with_correct_columns(self):
        df = get_log_dataframe(st)
        assert df.empty
        assert list(df.columns) == LOG_COLUMNS

    def test_key_metric_extracted_per_module(self):
        r_solar = calculate_solar_albedo_heat_risk(950, 9, 42, "silicon_pv_panels")
        log_assessment(st, r_solar)
        r_dc = calculate_datacenter_kinetic_risk(1300, 30, False, False)
        log_assessment(st, r_dc)
        df = get_log_dataframe(st)
        solar_row = df[df["module"] == "Solar (Desert)"].iloc[0]
        dc_row = df[df["module"] == "Data Center (Controlled Critical Environment)"].iloc[0]
        assert solar_row["key_metric"] == r_solar["perceived_temp"]
        assert dc_row["key_metric"] == r_dc["arc_flash_energy_cal"]

    def test_safety_override_recorded_as_bool(self):
        r = calculate_underground_kinetic_risk(35, 95, 40, 8)  # forces override
        log_assessment(st, r)
        df = get_log_dataframe(st)
        assert bool(df.iloc[0]["safety_override"]) is True


class TestAnalyticsCsvMergeRoundTrip:
    def setup_method(self):
        st.session_state.clear()

    def test_download_then_merge_in_new_session_recovers_data(self):
        import io
        # "Session 1": log something, simulate downloading the CSV
        log_assessment(st, calculate_solar_albedo_heat_risk(950, 9, 42, "silicon_pv_panels"))
        df1 = get_log_dataframe(st)
        csv_bytes = df1.to_csv(index=False).encode("utf-8")

        # "Session 2": fresh session_state, log something new, merge the old CSV back in
        st.session_state.clear()
        log_assessment(st, calculate_high_rise_kinetic_risk(25, 90, 15))
        added = merge_uploaded_csv(st, io.BytesIO(csv_bytes))
        assert added == 1
        df2 = get_log_dataframe(st)
        assert len(df2) == 2
        assert set(df2["module"]) == {"Solar (Desert)", "High-Rise (Vertical Urban)"}

    def test_merging_same_file_twice_does_not_duplicate(self):
        import io
        log_assessment(st, calculate_solar_albedo_heat_risk(950, 9, 42, "silicon_pv_panels"))
        df1 = get_log_dataframe(st)
        csv_bytes = df1.to_csv(index=False).encode("utf-8")

        merge_uploaded_csv(st, io.BytesIO(csv_bytes))
        added_again = merge_uploaded_csv(st, io.BytesIO(csv_bytes))
        assert added_again == 0

    def test_merge_rejects_csv_missing_expected_columns(self):
        import io
        bad_csv = io.BytesIO(b"not,the,right,columns\n1,2,3,4\n")
        with pytest.raises(ValueError):
            merge_uploaded_csv(st, bad_csv)


class TestMonthlySummaryAndExcel:
    def setup_method(self):
        st.session_state.clear()

    def test_monthly_summary_on_empty_log(self):
        df = get_log_dataframe(st)
        summary = monthly_summary(df)
        assert summary.empty
        assert list(summary.columns) == ["month", "module", "assessments", "safety_overrides", "avg_key_metric"]

    def test_monthly_summary_aggregates_by_module(self):
        log_assessment(st, calculate_solar_albedo_heat_risk(950, 9, 42, "silicon_pv_panels"))
        log_assessment(st, calculate_solar_albedo_heat_risk(300, 3, 24, "pure_desert_sand"))
        log_assessment(st, calculate_high_rise_kinetic_risk(25, 90, 15))
        df = get_log_dataframe(st)
        summary = monthly_summary(df)
        solar_row = summary[summary["module"] == "Solar (Desert)"].iloc[0]
        assert solar_row["assessments"] == 2

    def test_build_monthly_excel_is_valid_xlsx_with_three_sheets(self):
        from openpyxl import load_workbook
        import io as io_mod

        log_assessment(st, calculate_solar_albedo_heat_risk(950, 9, 42, "silicon_pv_panels"))
        log_assessment(st, calculate_high_rise_kinetic_risk(25, 90, 15))
        df = get_log_dataframe(st)

        xlsx_bytes = build_monthly_excel(df)
        assert isinstance(xlsx_bytes, bytes)
        assert xlsx_bytes[:2] == b"PK"  # xlsx is a zip archive

        wb = load_workbook(io_mod.BytesIO(xlsx_bytes))
        assert wb.sheetnames == ["Raw Log", "Monthly Summary", "Trend Chart"]
        assert wb["Raw Log"].max_row == 3  # header + 2 rows
        assert len(wb["Trend Chart"]._charts) == 1  # a real embedded chart, not just data

    def test_build_monthly_excel_handles_empty_log_gracefully(self):
        df = get_log_dataframe(st)
        xlsx_bytes = build_monthly_excel(df)
        assert xlsx_bytes[:2] == b"PK"

    def test_excel_export_has_no_timezone_aware_datetime_error(self):
        # Regression test: pandas raises ValueError writing tz-aware
        # datetimes to Excel - build_monthly_excel must strip tz info first.
        log_assessment(st, calculate_solar_albedo_heat_risk(950, 9, 42, "silicon_pv_panels"))
        df = get_log_dataframe(st)
        assert df["timestamp"].dt.tz is not None  # confirm the input IS tz-aware
        build_monthly_excel(df)  # must not raise


# ---------------------------------------------------------------------------
# Meteorology forecast (data_feeds.py) - mocked, no real network call
# ---------------------------------------------------------------------------

class TestMeteorologyForecast:
    def _mock_daily_response(self, fields: dict):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"daily": fields}
        return mock_resp

    def test_solar_forecast_returns_expected_shape(self):
        fetch_solar_forecast.clear()
        fields = {
            "time": ["2026-01-01", "2026-01-02"],
            "temperature_2m_max": [40.0, 41.0],
            "uv_index_max": [9.0, 9.5],
            "shortwave_radiation_sum": [22.0, 23.0],
        }
        with patch("data_feeds.requests.get", return_value=self._mock_daily_response(fields)):
            result = fetch_solar_forecast(days=2)
        assert result["dates"] == ["2026-01-01", "2026-01-02"]
        assert result["temperature_2m_max"] == [40.0, 41.0]
        assert "source" in result

    def test_offshore_forecast_returns_expected_shape(self):
        fetch_offshore_forecast.clear()
        fields = {
            "time": ["2026-01-01", "2026-01-02"],
            "temperature_2m_max": [30.0, 31.0],
            "wind_speed_10m_max": [15.0, 22.0],
        }
        with patch("data_feeds.requests.get", return_value=self._mock_daily_response(fields)):
            result = fetch_offshore_forecast(days=2)
        assert result["wind_speed_10m_max_kn"] == [15.0, 22.0]

    def test_forecast_network_failure_raises_datafeederror(self):
        fetch_solar_forecast.clear()
        with patch("data_feeds.requests.get", side_effect=ConnectionError("network down")):
            with pytest.raises(DataFeedError):
                fetch_solar_forecast(days=2)

    def test_forecast_days_param_is_clamped_to_open_meteo_limits(self):
        fetch_solar_forecast.clear()
        fields = {"time": ["2026-01-01"], "temperature_2m_max": [40.0], "uv_index_max": [9.0], "shortwave_radiation_sum": [22.0]}
        with patch("data_feeds.requests.get", return_value=self._mock_daily_response(fields)) as mock_get:
            fetch_solar_forecast(days=999)  # way over the limit
            sent_params = mock_get.call_args.kwargs["params"]
            assert sent_params["forecast_days"] <= 16
