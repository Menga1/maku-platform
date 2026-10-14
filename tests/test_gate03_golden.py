"""Release Gate 03 - golden-reference suite (pre-launch audit mandate A3-A6).

What this file proves, and what it cannot
-----------------------------------------
Each of the 21 reference cases in tests/reference_cases/*.json is run
through the PRODUCTION entry point (maku_core.run_assessment - the function
every Streamlit page calls through app.assess) and checked against oracles
written in this file, independently of risk_engine.py / risk_matrix.py /
maku_core/residual.py:

  * physics fields with a hand-calculation basis (Lee arc flash, Humidex via
    dew point, power-law wind, OSHA noise dose, ISO 2631-1 A(8)) - exact
    within the documented tolerance;
  * matrix arithmetic: score = likelihood x severity, band from the
    documented thresholds (docs/METHODOLOGY.md section 2), worst hazard
    governs;
  * residual risk re-derived from the documented 2.0.0 rules (section 3);
  * determinism (two runs, byte-identical JSON);
  * band / safety-override REGRESSION BASELINES (labelled as such).

What it cannot prove: that MAKU's bands, likelihood margins and residual
conventions are the RIGHT ones. That needs expected values approved by an
independent, competent HSE reviewer from an approved reference standard
(mandate A1). Until a case's "approved_expected" block is filled in, its
test_approved_expected_value[...] is reported as SKIPPED - BLOCKED, and
scripts/audit_evidence.py marks the case BLOCKED in
docs/audit/reference_case_comparison.csv. The engine's own output is never
used as its own expected answer.
"""
from __future__ import annotations

import copy
import glob
import json
import math
import os
from unittest.mock import MagicMock, patch

import pytest

import maku_core
from maku_core import METHODOLOGY_VERSION, MODULES, run_assessment
from maku_core.service import InputError, residual_risk_for

HERE = os.path.dirname(__file__)
FILES = sorted(glob.glob(os.path.join(HERE, "reference_cases", "*.json")))
CASES = [(doc, case) for f in FILES for doc in [json.load(open(f, encoding="utf-8"))] for case in doc["cases"]]
CASE_IDS = [f"{doc['module']}:{case['id']}" for doc, case in CASES]
EXPECTED_CASE_COUNT = 21

# ---- independent oracles (from docs/METHODOLOGY.md, not imported) ---------
DOCUMENTED_BANDS = [(1, 4, "Low"), (5, 9, "Moderate"), (10, 15, "High"), (16, 25, "Extreme")]


def oracle_band(score: int) -> str:
    for low, high, label in DOCUMENTED_BANDS:
        if low <= score <= high:
            return label
    raise AssertionError(f"score {score} outside 1-25")


def oracle_residual(initial_matrix: dict, applied: list[dict]) -> dict:
    """Methodology 2.0.0 section 3, re-implemented from the text."""
    hazards = []
    for h in initial_matrix["hazards"]:
        relevant = [c for c in applied if h["name"] in c["hazards"] and c["level"] != "monitoring"]
        if any(c["level"] == "elimination" for c in relevant):
            likelihood = 1
        else:
            likelihood = max(1, h["likelihood"] - len(relevant))
        score = likelihood * h["severity"]                    # severity never reduced
        hazards.append({"name": h["name"], "likelihood": likelihood, "severity": h["severity"],
                        "score": score, "band": oracle_band(score)})
    worst = max(hazards, key=lambda x: x["score"])
    return {"hazards": hazards, "overall_score": worst["score"], "overall_band": worst["band"]}


def run_case(doc, case):
    return run_assessment(doc["module"], case["inputs"], country=doc.get("country"))


def applied_controls(case, assessment) -> list[dict]:
    scenario = case.get("residual_scenario") or {}
    wanted = scenario.get("applied_controls", "all_recommended")
    if wanted == "all_recommended":
        return assessment["controls"]
    return [c for c in assessment["controls"] if c["id"] in set(wanted)]


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


# =========================================================================
# A6: 21 individual golden-reference tests + aggregate
# =========================================================================
def test_reference_set_has_exactly_21_cases():
    assert len(CASES) == EXPECTED_CASE_COUNT, CASE_IDS
    assert len(set(CASE_IDS)) == EXPECTED_CASE_COUNT, "duplicate case ids"


@pytest.mark.parametrize("doc,case", CASES, ids=CASE_IDS)
def test_golden_reference_case(doc, case):
    first, second = run_case(doc, case), run_case(doc, case)
    assert canonical(first) == canonical(second), "non-deterministic result"
    result = first["result"]
    assert result["methodology_version"] == METHODOLOGY_VERSION

    # Independent hand calculations (documented tolerance, never a wider one).
    for field, (value, tolerance) in case["expected"]["fields"].items():
        assert result[field] == pytest.approx(value, abs=tolerance), field

    # Initial risk: matrix arithmetic against the documented methodology.
    matrix = result["risk_matrix"]
    assert matrix["hazards"], "a result without scored hazards is missing data"
    for h in matrix["hazards"]:
        assert isinstance(h["likelihood"], int) and 1 <= h["likelihood"] <= 5, h
        assert isinstance(h["severity"], int) and 1 <= h["severity"] <= 5, h
        assert h["score"] == h["likelihood"] * h["severity"], h
        assert h["band"] == oracle_band(h["score"]), h
    worst = max(h["score"] for h in matrix["hazards"])
    assert matrix["overall_score"] == worst
    assert matrix["overall_band"] == oracle_band(worst)

    # Residual risk: re-derived from the documented 2.0.0 rules.
    applied = applied_controls(case, first)
    residual = residual_risk_for(first, [c["id"] for c in applied])
    expected_residual = oracle_residual(matrix, applied)
    assert residual["overall_score"] == expected_residual["overall_score"]
    assert residual["overall_band"] == expected_residual["overall_band"]
    for got, want, initial in zip(residual["hazards"], expected_residual["hazards"], matrix["hazards"]):
        assert (got["likelihood"], got["severity"], got["score"], got["band"]) == \
               (want["likelihood"], want["severity"], want["score"], want["band"]), got["name"]
        assert got["severity"] == initial["severity"], "severity must never be reduced"
        assert got["score"] <= initial["score"]
    # Initial and residual are distinct objects; computing residual never
    # changes the initial result.
    assert canonical(first["result"]["risk_matrix"]) == canonical(run_case(doc, case)["result"]["risk_matrix"])

    # Regression baselines (MAKU's own thresholds, NOT approved values).
    assert result["risk_band"] == case["expected"]["risk_band"]
    assert bool(result["safety_override"]) is case["expected"]["safety_override"]


@pytest.mark.parametrize("doc,case", CASES, ids=CASE_IDS)
def test_approved_expected_value(doc, case):
    """Exact comparison with the INDEPENDENTLY APPROVED expected values.
    BLOCKED (skipped) until the reviewer fills in approved_expected."""
    approved = case.get("approved_expected")
    if not approved:
        pytest.skip("BLOCKED: no independently approved expected value for this case (mandate A1)")
    assessment = run_case(doc, case)
    result = assessment["result"]
    residual = residual_risk_for(assessment, [c["id"] for c in applied_controls(case, assessment)])
    assert result["risk_matrix"]["overall_score"] == approved["initial_score"]
    assert result["risk_matrix"]["overall_band"] == approved["initial_band"]
    assert residual["overall_score"] == approved["residual_score"]
    assert residual["overall_band"] == approved["residual_band"]
    if "safety_override" in approved:
        assert bool(result["safety_override"]) is approved["safety_override"]


def test_all_cases_aggregate():
    """Aggregate: every case runs, is deterministic, and the set's outcome
    summary is reproducible."""
    summary = []
    for doc, case in CASES:
        a, b = run_case(doc, case), run_case(doc, case)
        assert canonical(a) == canonical(b)
        summary.append((doc["module"], case["id"], a["result"]["risk_matrix"]["overall_score"],
                        a["result"]["risk_band"], case.get("approved_expected") is not None))
    assert len(summary) == EXPECTED_CASE_COUNT
    approved = sum(1 for s in summary if s[4])
    print(f"\n[gate 03] {len(summary)} cases executed, {approved}/{len(summary)} with approved expected values")


# =========================================================================
# A4: severity and risk-band boundaries
# =========================================================================
from risk_matrix import (aggregate_risk_matrix, likelihood_from_margin, matrix_band,  # noqa: E402
                         matrix_score, score_hazard, severity_from_band)


class TestBandBoundaries:
    @pytest.mark.parametrize("score", range(1, 26))
    def test_every_score_maps_to_exactly_one_documented_band(self, score):
        assert matrix_band(score) == oracle_band(score)

    @pytest.mark.parametrize("below,above,band_below,band_above", [
        (4, 5, "Low", "Moderate"), (9, 10, "Moderate", "High"), (15, 16, "High", "Extreme")])
    def test_each_boundary_and_its_neighbours(self, below, above, band_below, band_above):
        assert matrix_band(below) == band_below and matrix_band(above) == band_above

    def test_no_gaps_or_overlaps_in_the_documented_table(self):
        covered = [s for low, high, _ in DOCUMENTED_BANDS for s in range(low, high + 1)]
        assert covered == list(range(1, 26))

    @pytest.mark.parametrize("bad", [0, 26, -1, 4.5, "5", None, True, float("nan")])
    def test_invalid_scores_are_rejected(self, bad):
        with pytest.raises(ValueError):
            matrix_band(bad)

    def test_only_achievable_scores(self):
        achievable = {l * s for l in range(1, 6) for s in range(1, 6)}
        assert {matrix_score(l, s) for l in range(1, 6) for s in range(1, 6)} == achievable

    @pytest.mark.parametrize("likelihood,severity", [(0, 3), (6, 3), (3, 0), (3, 6), (-1, -1), (2.5, 3),
                                                     (None, 3), ("3", 3), (True, 3)])
    def test_invalid_axis_values_are_rejected(self, likelihood, severity):
        with pytest.raises(ValueError):
            score_hazard("x", likelihood, severity)

    @pytest.mark.parametrize("label,severity", [("LOW", 1), ("Low", 1), ("MODERATE", 3), ("Moderate", 3),
                                                ("HIGH", 4), ("High", 4), ("CRITICAL", 5), ("Extreme", 5)])
    def test_band_vocabulary_to_severity(self, label, severity):
        assert severity_from_band(label) == severity

    @pytest.mark.parametrize("label", ["", "Critical-ish", None, "low "])
    def test_unknown_band_label_is_rejected_not_guessed(self, label):
        with pytest.raises(ValueError):
            severity_from_band(label)

    def test_no_hazard_is_not_low_risk(self):
        with pytest.raises(ValueError):
            aggregate_risk_matrix([])


class TestLikelihoodBoundaries:
    """likelihood_from_margin: threshold 100, comfortable margin 20 ->
    bands at margin 0 / 5 / 12 / 20 (documented 0, 25 %, 60 %, 100 %)."""

    @pytest.mark.parametrize("value,likelihood", [
        (120, 5), (100, 5), (99.999, 4), (95, 4), (94.999, 3), (88, 3), (87.999, 2), (80, 2), (79.999, 1), (0, 1)])
    def test_boundaries(self, value, likelihood):
        assert likelihood_from_margin(value, 100, 20) == likelihood

    @pytest.mark.parametrize("args", [(float("nan"), 100, 20), (50, float("inf"), 20), (50, 100, 0),
                                      (50, 100, -5), (None, 100, 20), ("50", 100, 20)])
    def test_invalid_inputs_are_rejected(self, args):
        with pytest.raises(ValueError):
            likelihood_from_margin(*args)


# =========================================================================
# A4 / A6: input validation and missing data, every module and field
# =========================================================================
def _valid_inputs(module_key):
    for doc, case in CASES:
        if doc["module"] == module_key:
            return dict(case["inputs"]), doc.get("country")
    raise AssertionError(module_key)


NUMBER_FIELDS = [(m.key, f) for m in MODULES.values() for f in m.fields
                 if f.kind == "number" and any(doc["module"] == m.key for doc, _ in CASES)]


class TestInputValidation:
    @pytest.mark.parametrize("module_key,field", NUMBER_FIELDS, ids=[f"{m}.{f.name}" for m, f in NUMBER_FIELDS])
    def test_range_edges(self, module_key, field):
        inputs, country = _valid_inputs(module_key)
        for ok in (field.minimum, field.maximum):
            run_assessment(module_key, {**inputs, field.name: ok}, country=country)
        span = (field.maximum - field.minimum) or 1
        for bad in (field.minimum - span * 1e-6 - 1e-9, field.maximum + span * 1e-6 + 1e-9):
            with pytest.raises(InputError):
                run_assessment(module_key, {**inputs, field.name: bad}, country=country)

    @pytest.mark.parametrize("module_key,field", NUMBER_FIELDS, ids=[f"{m}.{f.name}" for m, f in NUMBER_FIELDS])
    def test_non_numbers_are_rejected(self, module_key, field):
        inputs, country = _valid_inputs(module_key)
        for bad in (float("nan"), float("inf"), "42", True, [42]):
            with pytest.raises(InputError):
                run_assessment(module_key, {**inputs, field.name: bad}, country=country)

    @pytest.mark.parametrize("module_key", sorted({doc["module"] for doc, _ in CASES}))
    def test_missing_required_fields_are_rejected(self, module_key):
        inputs, country = _valid_inputs(module_key)
        for field in MODULES[module_key].fields:
            if field.required and field.name in inputs:
                partial = {k: v for k, v in inputs.items() if k != field.name}
                with pytest.raises(InputError):
                    run_assessment(module_key, partial, country=country)
                with pytest.raises(InputError):
                    run_assessment(module_key, {**inputs, field.name: None}, country=country)

    def test_unknown_country_is_rejected_not_substituted(self):
        inputs, _ = _valid_inputs("offshore")
        with pytest.raises(InputError):
            run_assessment("offshore", inputs, country="AE")

    def test_unknown_input_field_is_rejected(self):
        inputs, country = _valid_inputs("offshore")
        with pytest.raises(InputError):
            run_assessment("offshore", {**inputs, "risk_band": "Low"}, country=country)


# =========================================================================
# A5: residual-risk rules
# =========================================================================
class TestResidualRules:
    def test_no_controls_means_residual_equals_initial(self):
        for doc, case in CASES:
            a = run_case(doc, case)
            r = residual_risk_for(a, [])
            assert r["overall_score"] == a["result"]["risk_matrix"]["overall_score"], case["id"]

    def test_controls_not_recommended_are_never_credited(self):
        doc, case = CASES[0]
        a = run_case(doc, case)
        r = residual_risk_for(a, ["made-up-control", "Wear a lucky charm"])
        assert r["overall_score"] == a["result"]["risk_matrix"]["overall_score"]

    def test_the_same_control_twice_counts_once(self):
        for doc, case in CASES:
            a = run_case(doc, case)
            reducing = [c for c in a["controls"] if c["level"] in ("engineering", "administrative", "ppe")]
            if reducing:
                once = residual_risk_for(a, [reducing[0]["id"]])
                twice = residual_risk_for(a, [reducing[0]["id"], reducing[0]["id"], reducing[0]["text"]])
                assert once["overall_score"] == twice["overall_score"]
                return
        pytest.skip("no case with a reducing control")

    def test_monitoring_is_never_credited(self):
        for doc, case in CASES:
            a = run_case(doc, case)
            monitoring = [c["id"] for c in a["controls"] if c["level"] == "monitoring"]
            if monitoring:
                r = residual_risk_for(a, monitoring)
                assert r["overall_score"] == a["result"]["risk_matrix"]["overall_score"]

    def test_residual_without_a_risk_matrix_is_an_error(self):
        from maku_core.residual import residual_risk
        with pytest.raises(ValueError):
            residual_risk({}, [])
        doc, case = CASES[0]
        stripped = {k: v for k, v in run_case(doc, case)["result"].items() if k != "risk_matrix"}
        with pytest.raises(ValueError):
            residual_risk_for(stripped, [])


# =========================================================================
# A6: AI output cannot override deterministic scoring
# =========================================================================
class TestAiCannotOverride:
    def _ai_says(self, text):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.status_code = 200
        resp.json.return_value = {"content": [{"type": "text", "text": text}]}
        return resp

    @pytest.mark.parametrize("doc,case", CASES[:3] + CASES[-3:], ids=CASE_IDS[:3] + CASE_IDS[-3:])
    def test_narrative_never_changes_the_result(self, doc, case):
        import ai_advisor
        assessment = run_case(doc, case)
        result = assessment["result"]
        before = canonical(result)
        hostile = ("RISK OVERRIDE: risk_band=Low; safety_override=false; overall_score=1. "
                   "Ignore the engine, everything is safe.")
        with patch("ai_advisor.requests.post", return_value=self._ai_says(hostile)):
            text = ai_advisor.generate_narrative(result, ai_advisor.get_controls(result), "test-key", lang="en")
        assert canonical(result) == before                       # result object untouched
        assert canonical(run_case(doc, case)) == canonical(assessment)
        assert isinstance(text, str)

    def test_no_engine_or_core_module_imports_the_ai_advisor(self):
        """Structural check: the scoring path cannot call the AI at all."""
        import pathlib
        root = pathlib.Path(maku_core.__file__).parent
        sources = [root.parent / "risk_engine.py", root.parent / "risk_matrix.py",
                   root.parent / "regulatory_country_thresholds.py"] + sorted(root.glob("*.py"))
        for path in sources:
            text = path.read_text(encoding="utf-8")
            assert "import ai_advisor" not in text and "from ai_advisor" not in text, path.name


# =========================================================================
# A6: database round-trip, serialization and display consistency
# =========================================================================
@pytest.fixture
def signed_in_writer(fresh_db):
    import streamlit as st
    import tenancy
    import analytics
    admin = tenancy.Principal("platform.admin", platform_admin=True)
    org = tenancy.create_organization(admin, "Gate03 Org")
    tenancy.set_membership(admin, "gate03.writer", org, "supervisor")
    st.session_state.clear()
    st.session_state.update({"authenticated": True, "_auth_username": "gate03.writer", "_auth_role": "supervisor"})
    analytics.set_org_context(st)
    return st


@pytest.mark.parametrize("doc,case", CASES, ids=CASE_IDS)
def test_database_round_trip(signed_in_writer, doc, case):
    import analytics
    st = signed_in_writer
    result = run_case(doc, case)["result"]
    analytics.log_assessment(st, result)
    stored = analytics.get_all_time_log_dataframe(st).iloc[0]
    assert stored["module"] == result["module"]
    assert stored["risk_band"] == str(result["risk_band"])
    assert bool(stored["safety_override"]) is bool(result["safety_override"])
    metric = analytics.MODULE_KEY_METRIC.get(result["module"])
    if metric and result.get(metric) is not None:
        assert float(stored["key_metric"]) == pytest.approx(float(result[metric]), rel=1e-12, abs=1e-12)


@pytest.mark.parametrize("doc,case", CASES[::4], ids=CASE_IDS[::4])
def test_report_displays_the_computed_result(doc, case):
    pypdf = pytest.importorskip("pypdf")
    import io
    from ui_helpers import _build_report_pdf
    result = run_case(doc, case)["result"]
    pdf = _build_report_pdf(result, "", [], [], [], "2026-10-14 00:00 UTC", "en")
    text = " ".join(page.extract_text() for page in pypdf.PdfReader(io.BytesIO(pdf)).pages)
    assert str(result["risk_band"]) in text
    assert METHODOLOGY_VERSION in text


def test_serialization_round_trip_is_lossless():
    for doc, case in CASES:
        a = run_case(doc, case)
        assert json.loads(canonical(a)) == json.loads(canonical(json.loads(canonical(a))))
        for value in json.loads(canonical(a["result"]["risk_matrix"]))["hazards"]:
            assert not (isinstance(value.get("score"), float) and math.isnan(value["score"]))


# =========================================================================
# Regression tests for defects found during this audit
# =========================================================================
class TestAuditRegressions:
    def test_R1_get_or_create_never_returns_a_made_up_id(self, fresh_db, monkeypatch):
        import analytics
        conn = analytics._get_connection()
        with conn:
            def refuse(*a, **k):
                raise RuntimeError("insert refused")
            real_execute = conn.execute

            def execute(sql, params=()):
                if sql.startswith("INSERT INTO organizations"):
                    refuse()
                return real_execute(sql, params)
            monkeypatch.setattr(conn, "execute", execute)
            with pytest.raises(RuntimeError):
                analytics._get_or_create_id(conn, "organizations", {}, "name", "Never Created")

    def test_R2_unreadable_audit_ledger_is_not_reported_intact(self, fresh_db, monkeypatch):
        import analytics
        monkeypatch.setattr("analytics.DATABASE_URL", "postgresql://u:p@127.0.0.1:1/none")
        report = analytics.verify_audit_log_integrity()
        assert report["ok"] is False and report.get("error")

    def test_R3_no_access_decision_without_the_database(self, fresh_db, monkeypatch):
        import analytics
        import streamlit as st
        st.session_state.update({"authenticated": True, "_auth_username": "x", "_auth_role": "supervisor"})
        monkeypatch.setattr("analytics.DATABASE_URL", "postgresql://u:p@127.0.0.1:1/none")
        analytics.probe_database(force=True)
        with pytest.raises(analytics.PersistenceError):
            analytics.require_scope(st, "read")
        with pytest.raises(analytics.PersistenceError):
            analytics.set_org_context(st)

    def test_R4_failed_safety_alert_write_is_reported(self, fresh_db, monkeypatch):
        import analytics
        monkeypatch.setattr("analytics.DATABASE_URL", "postgresql://u:p@127.0.0.1:1/none")
        assert analytics.log_site_alert("w", "physiological_strain", "CRITICAL", "Heat") is False

    @pytest.mark.skipif(os.environ.get("MAKU_TEST_BACKEND") == "postgres", reason="SQLite development path")
    def test_R5_development_sqlite_failure_has_no_in_memory_substitute(self, fresh_db, monkeypatch, tmp_path):
        import analytics
        import streamlit as st
        st.session_state.update({"authenticated": True, "_auth_username": "x", "_auth_role": "admin"})
        monkeypatch.setattr("analytics.DB_PATH", str(tmp_path / "missing-dir" / "x.db"))
        with pytest.raises(analytics.PersistenceError):
            analytics.log_assessment(st, run_case(*CASES[0])["result"])
        assert analytics.LOG_SESSION_KEY not in st.session_state
        assert analytics.is_db_fatal()
