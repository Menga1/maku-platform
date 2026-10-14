"""maku_core: the risk methodology as a library (review finding F4)."""
import itertools
import json
import math
import os
import subprocess
import sys

import numpy as np
import pytest

import risk_engine as engine
from maku_core import (MODULES, METHODOLOGY_VERSION, InputError, controls_for_result, input_schema,
                       residual_risk_for, run_assessment, validate_inputs)
from maku_core.controls import LEVELS, H_ARC_FLASH, H_AISLE
from regulatory_country_thresholds import get_regulatory_profile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

SAMPLE = {
    "solar": dict(ghi=950, uv_index=9, ambient_temp=42, surface_type="silicon_pv_panels"),
    "offshore": dict(ambient_temp=34, relative_humidity=75, wind_speed=40),
    "underground": dict(ambient_temp=38, geothermal_humidity=85, particulate_matter_pm25=80, gas_co_ppm=60),
    "high_rise": dict(ground_wind_speed_knots=22, floor_level=60, crane_load_mass_tons=3),
    "data_center": dict(hot_aisle_temp=48, ceiling_void_confined=True, gas_system_armed=True),
    "wind_energy": dict(hub_height_wind_speed_ms=22, is_offshore=True, significant_wave_height_m=2.5,
                        flash_to_bang_sec=10),
    "mining_quarrying": dict(respirable_silica_ugm3=80, measured_noise_dba=95, noise_exposure_hours=8,
                             measured_vibration_aw_ms2=1.3, vibration_exposure_hours=8),
    "marine_port": dict(current_tide_level_m=0.2, required_min_clearance_m=1.0, is_night_operation=True,
                        measured_illuminance_lux=20, hardware_years_in_service=20),
    "heat_stress": dict(workload_category="heavy", clothing_type="work_clothes", acclimatized=False,
                        wbgt_measured_c=31),
}


# ------------------------------------------------------------ independence
def test_library_does_not_import_streamlit_or_the_database():
    code = ("import sys, maku_core; "
            "maku_core.run_assessment('solar', %r); "
            "bad = [m for m in ('streamlit', 'analytics', 'auth', 'tenancy', 'sqlalchemy') if m in sys.modules]; "
            "print(bad); sys.exit(1 if bad else 0)") % (SAMPLE["solar"],)
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr


# ------------------------------------------------------------ parity
@pytest.mark.parametrize("key", list(MODULES))
def test_run_assessment_matches_the_engine(key):
    profile = get_regulatory_profile("UAE")
    spec = MODULES[key]
    direct = spec.function(**validate_inputs(key, SAMPLE[key]), regulatory_profile=profile)
    via = run_assessment(key, SAMPLE[key], country="UAE")
    assert via["result"]["risk_band"] == direct["risk_band"]
    assert via["result"]["safety_override"] == direct["safety_override"]
    assert via["result"]["risk_matrix"] == direct["risk_matrix"]
    assert via["methodology_version"] == via["result"]["methodology_version"] == METHODOLOGY_VERSION
    assert via["module"] == spec.name
    assert json.dumps(via, default=str)   # serialisable for an API


# ------------------------------------------------------------ validation
class TestValidation:
    def test_collects_every_problem(self):
        with pytest.raises(InputError) as err:
            validate_inputs("solar", {"ghi": -5, "uv_index": "high", "surface_type": "lava", "colour": "red"})
        text = " | ".join(err.value.problems)
        for expected in ("'ghi'", "'uv_index' must be a number", "'ambient_temp' is required",
                         "'surface_type' must be one of", "unknown field 'colour'"):
            assert expected in text

    @pytest.mark.parametrize("bad", [math.nan, math.inf, True])
    def test_rejects_non_finite_and_bool_numbers(self, bad):
        with pytest.raises(InputError):
            validate_inputs("offshore", {"ambient_temp": bad, "relative_humidity": 50, "wind_speed": 5})

    def test_fahrenheit_typo_is_caught(self):
        with pytest.raises(InputError):
            validate_inputs("offshore", {"ambient_temp": 104, "relative_humidity": 50, "wind_speed": 5})

    def test_numpy_values_accepted(self):
        kw = validate_inputs("offshore", {"ambient_temp": np.float64(30), "relative_humidity": np.int64(50),
                                          "wind_speed": np.float32(5)})
        assert kw["relative_humidity"] == 50.0

    def test_defaults_filled(self):
        kw = validate_inputs("high_rise", {"ground_wind_speed_knots": 10, "floor_level": 5, "crane_load_mass_tons": 1})
        assert kw["terrain"] == engine.DEFAULT_WIND_TERRAIN and kw["floor_height_m"] == 3.5
        assert kw["measured_hook_wind_knots"] is None

    def test_unknown_module_and_country(self):
        with pytest.raises(InputError):
            run_assessment("volcano", {})
        with pytest.raises(InputError):
            run_assessment("solar", SAMPLE["solar"], country="AE")   # codes are e.g. "UAE"

    @pytest.mark.parametrize("key", list(MODULES))
    def test_schema_describes_every_field(self, key):
        schema = input_schema(key)
        assert set(schema["properties"]) == {f.name for f in MODULES[key].fields}
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) <= set(schema["properties"])


# ------------------------------------------------------------ controls
def _scenario_results():
    yield from (engine.calculate_solar_albedo_heat_risk(g, u, t, "silicon_pv_panels")
                for t, u, g in itertools.product([25, 38, 46], [2, 11], [300, 1000]))
    yield from (engine.calculate_marine_humidex_risk(t, h, w) for t, h, w in itertools.product([28, 36], [40, 90], [10, 45]))
    yield from (engine.calculate_underground_kinetic_risk(t, h, pm, co)
                for t, h, pm, co in itertools.product([30, 42], [50, 95], [10, 80], [5, 60]))
    yield from (engine.calculate_high_rise_kinetic_risk(w, f, m) for w, f, m in itertools.product([5, 15, 30], [2, 40, 90], [2, 25]))
    yield from (engine.calculate_datacenter_kinetic_risk(None, hot, conf, arm, label_incident_energy_cal=lab)
                for lab, conf, arm, hot in itertools.product([None, 3.0, 12.0, 45.0], [True, False], [True, False], [30, 48]))
    yield from (engine.calculate_wind_energy_kinetic_risk(w, off, wave, ftb)
                for w, off, wave, ftb in itertools.product([8, 14, 22], [True, False], [0.5, 2.0], [None, 10, 60]))
    yield from (engine.calculate_mining_quarrying_kinetic_risk(si, n, 8, v, 8)
                for si, n, v in itertools.product([20, 80], [80, 95], [0.3, 0.7, 1.3]))
    yield from (engine.calculate_marine_port_kinetic_risk(tide, 1.0, night, lux, yrs)
                for tide, night, lux, yrs in itertools.product([0.2, 0.7, 2.0], [True, False], [20, 100], [2, 20]))
    yield from (engine.calculate_iso7243_heat_stress(wl, cl, acc, "100/0", wbgt_measured_c=wb)
                for wl, cl, acc, wb in itertools.product(["light", "heavy"], ["work_clothes", "vapor_barrier_coveralls"],
                                                         [True, False], [24, 31]))


def test_every_control_targets_hazards_the_engine_actually_scores():
    """Guards against a hazard being renamed in risk_engine.py but not here
    (which would silently stop crediting that control)."""
    seen = 0
    for result in _scenario_results():
        scored = {h["name"] for h in result["risk_matrix"]["hazards"]}
        for c in controls_for_result(result):
            assert c.level in LEVELS
            if c.level != "monitoring":
                assert c.hazards, c.id
            assert set(c.hazards) <= scored, (c.id, set(c.hazards) - scored)
            seen += 1
    assert seen > 100


def test_control_ids_are_unique_and_stable_per_text():
    by_id = {}
    for result in _scenario_results():
        ids = [c.id for c in controls_for_result(result)]
        assert len(ids) == len(set(ids))
        for c in controls_for_result(result):
            by_id.setdefault(c.id, set()).add(c.level)
    assert all(len(levels) == 1 for levels in by_id.values())


# ------------------------------------------------------------ residual rule (methodology 2.0.0)
class TestResidualRisk:
    def _dc(self):
        """Arc flash unknown (governing, CRITICAL) + hot aisle + armed confined void."""
        return run_assessment("data_center", SAMPLE["data_center"])

    def test_unrelated_control_gives_no_credit(self):
        """The 1.x defect: a heat control lowered the arc-flash risk."""
        a = self._dc()
        before = a["result"]["risk_matrix"]
        after = residual_risk_for(a, ["data_center.aisle_rotation"])
        arc_before = next(h for h in before["hazards"] if h["name"] == H_ARC_FLASH)
        arc_after = next(h for h in after["hazards"] if h["name"] == H_ARC_FLASH)
        assert arc_after["likelihood"] == arc_before["likelihood"]
        assert after["overall_score"] == before["overall_score"]
        assert after["credited"] == {H_AISLE: ["data_center.aisle_rotation"]}

    def test_elimination_makes_the_hazard_rare_and_another_can_govern(self):
        a = self._dc()
        after = residual_risk_for(a, ["data_center.unknown_ie_no_live_work"])
        arc = next(h for h in after["hazards"] if h["name"] == H_ARC_FLASH)
        assert arc["likelihood"] == 1
        assert after["governing_hazard"] != H_ARC_FLASH

    def test_severity_is_never_reduced(self):
        a = self._dc()
        all_ids = [c["id"] for c in a["controls"]]
        after = residual_risk_for(a, all_ids)
        before = {h["name"]: h["severity"] for h in a["result"]["risk_matrix"]["hazards"]}
        assert {h["name"]: h["severity"] for h in after["hazards"]} == before

    def test_administrative_controls_reduce_by_one_each_floor_one(self):
        a = run_assessment("high_rise", dict(ground_wind_speed_knots=14, floor_level=50, crane_load_mass_tons=2))
        ids = [c["id"] for c in a["controls"] if c["level"] == "administrative"]
        assert ids, a["controls"]
        after = residual_risk_for(a, ids)
        for h_before in a["result"]["risk_matrix"]["hazards"]:
            n = sum(1 for c in a["controls"] if c["id"] in ids and h_before["name"] in c["hazards"])
            h_after = next(h for h in after["hazards"] if h["name"] == h_before["name"])
            assert h_after["likelihood"] == max(1, h_before["likelihood"] - n)

    def test_controls_not_recommended_for_this_result_are_ignored(self):
        a = self._dc()
        after = residual_risk_for(a, ["solar.cooling", "made.up.control", "data_center.de_energize"])
        assert after["controls_applied_count"] == 0   # de_energize is only recommended above 40 cal/cm2
        assert after["overall_score"] == a["result"]["risk_matrix"]["overall_score"]

    def test_texts_and_ids_are_equivalent(self):
        a = self._dc()
        first = a["controls"][0]
        assert residual_risk_for(a, [first["id"]]) == residual_risk_for(a, [first["text"]])

    def test_monitoring_advice_is_never_credited(self):
        a = run_assessment("solar", dict(ghi=200, uv_index=1, ambient_temp=20, surface_type="pure_desert_sand"))
        assert [c["level"] for c in a["controls"]] == ["monitoring"]
        after = residual_risk_for(a, [a["controls"][0]["id"]])
        assert after["credited"] == {} and after["overall_score"] == a["result"]["risk_matrix"]["overall_score"]

    def test_records_methodology_version(self):
        assert residual_risk_for(self._dc(), [])["methodology_version"] == METHODOLOGY_VERSION


# ------------------------------------------------------------ command line
def test_command_line():
    out = subprocess.run([sys.executable, "-m", "maku_core", "run", "data_center",
                          json.dumps(SAMPLE["data_center"]), "--country", "UAE",
                          "--applied", "data_center.unknown_ie_no_live_work"],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    doc = json.loads(out.stdout)
    assert doc["country"] == "UAE" and "residual" in doc
    bad = subprocess.run([sys.executable, "-m", "maku_core", "run", "solar", "{}"], cwd=ROOT,
                         capture_output=True, text=True)
    assert bad.returncode == 2 and "invalid_input" in bad.stdout
