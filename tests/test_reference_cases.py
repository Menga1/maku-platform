"""Reference cases (review finding F4 / release gate 03).

Every JSON file in tests/reference_cases/ is run through maku_core. Values
with a hand-calculation basis were computed from the published formula,
independently of the engine. Bands and safety overrides are MAKU's own
thresholds: regression baselines until a competent HSE reviewer fills in
review_status / reviewed_by / reviewed_on. test_review_status_report prints
how many cases are still unreviewed - release gate 03 requires zero.
"""
import glob
import json
import os

import pytest

from maku_core import METHODOLOGY_VERSION, run_assessment

HERE = os.path.dirname(__file__)
FILES = sorted(glob.glob(os.path.join(HERE, "reference_cases", "*.json")))
CASES = [(os.path.basename(f), json.load(open(f, encoding="utf-8"))) for f in FILES]
PARAMS = [pytest.param(doc["module"], doc.get("country"), case, id=f"{doc['module']}:{case['id']}")
          for _, doc in CASES for case in doc["cases"]]


def test_every_module_has_reference_cases():
    from maku_core import MODULES
    covered = {doc["module"] for _, doc in CASES}
    assert covered >= set(MODULES) - {"heat_stress"}, set(MODULES) - covered


@pytest.mark.parametrize("module,country,case", PARAMS)
def test_reference_case(module, country, case):
    assessment = run_assessment(module, case["inputs"], country=country)
    result = assessment["result"]
    expected = case["expected"]
    assert result["risk_band"] == expected["risk_band"]
    assert bool(result["safety_override"]) is expected["safety_override"]
    for field, (value, tolerance) in expected["fields"].items():
        assert result[field] == pytest.approx(value, abs=tolerance), field
    assert result["methodology_version"] == METHODOLOGY_VERSION


def test_review_status_report(capsys):
    pending = [f"{doc['module']}:{c['id']}" for _, doc in CASES for c in doc["cases"]
               if not c.get("reviewed_by")]
    total = sum(len(doc["cases"]) for _, doc in CASES)
    with capsys.disabled():
        print(f"\n[reference cases] {total - len(pending)}/{total} independently reviewed "
              f"(release gate 03 requires all)")
