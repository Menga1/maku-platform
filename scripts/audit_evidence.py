#!/usr/bin/env python3
"""
Audit evidence generator (pre-launch audit mandate A7, C5, D1).

  python scripts/audit_evidence.py reference-cases  [--out docs/audit/reference_case_comparison.csv]
  python scripts/audit_evidence.py tenant-matrix --junit sqlite.xml [--junit postgres.xml]
                                                    [--out docs/audit/tenant_isolation_matrix.csv]
  python scripts/audit_evidence.py environment       [--out docs/audit/environment.json]

reference-cases runs all 21 cases through maku_core.run_assessment (the
production entry point) twice each and writes the A7 comparison table.
Expected values come ONLY from each case's "approved_expected" block, which
the independent HSE reviewer fills in. An empty block is reported as MISSING
and the case as BLOCKED - the engine's output is never copied into the
expected columns.

Exit code: 0 when every case is PASS, 1 if any FAIL, 2 if any BLOCKED (and none FAIL).
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import os
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

COLUMNS = ["Case ID", "Input Hash", "Expected Initial Score", "Actual Initial Score", "Expected Initial Band",
           "Actual Initial Band", "Expected Residual Score", "Actual Residual Score", "Expected Residual Band",
           "Actual Residual Band", "Deterministic", "Result", "Evidence",
           # additional context columns
           "Module", "Country", "Governing Hazard", "Actual Risk Band (module)", "Actual Safety Override",
           "Independent Field Checks", "Controls Applied (residual scenario)", "Methodology Version"]
MISSING = "MISSING - awaiting approved value"


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))


def load_cases():
    for path in sorted(glob.glob(os.path.join(ROOT, "tests", "reference_cases", "*.json"))):
        doc = json.load(open(path, encoding="utf-8"))
        for case in doc["cases"]:
            yield doc, case


def reference_cases(out: str) -> int:
    from maku_core import METHODOLOGY_VERSION, run_assessment
    from maku_core.service import residual_risk_for

    rows, outcomes = [], []
    for doc, case in load_cases():
        module, country = doc["module"], doc.get("country")
        input_hash = hashlib.sha256(_canonical({"module": module, "country": country,
                                                "inputs": case["inputs"]}).encode()).hexdigest()[:16]
        first = run_assessment(module, case["inputs"], country=country)
        second = run_assessment(module, case["inputs"], country=country)
        deterministic = _canonical(first) == _canonical(second)
        result, matrix = first["result"], first["result"]["risk_matrix"]
        scenario = (case.get("residual_scenario") or {}).get("applied_controls", "all_recommended")
        applied = [c["id"] for c in first["controls"]] if scenario == "all_recommended" else list(scenario)
        residual = residual_risk_for(first, applied)

        field_checks = []
        fields_ok = True
        for field, (value, tol) in case["expected"]["fields"].items():
            ok = abs(result[field] - value) <= tol
            fields_ok &= ok
            field_checks.append(f"{field}: expected {value}±{tol} (hand calc), actual {round(result[field], 4)} "
                                f"{'OK' if ok else 'MISMATCH'}")

        approved = case.get("approved_expected") or {}
        expected = {k: approved.get(k) for k in ("initial_score", "initial_band", "residual_score", "residual_band")}
        actual = {"initial_score": matrix["overall_score"], "initial_band": matrix["overall_band"],
                  "residual_score": residual["overall_score"], "residual_band": residual["overall_band"]}
        if not deterministic or not fields_ok:
            outcome = "FAIL"
        elif any(v is None for v in expected.values()):
            outcome = "BLOCKED"
        elif all(expected[k] == actual[k] for k in expected):
            outcome = "PASS"
        else:
            outcome = "FAIL"
        outcomes.append(outcome)
        case_id = f"{module}:{case['id']}"
        evidence = (f"tests/test_gate03_golden.py::test_golden_reference_case[{case_id}]; "
                    f"::test_approved_expected_value[{case_id}]"
                    + ("" if outcome != "BLOCKED" else " (skipped: no approved expected value)"))
        rows.append({
            "Case ID": case_id, "Input Hash": input_hash,
            "Expected Initial Score": expected["initial_score"] if expected["initial_score"] is not None else MISSING,
            "Actual Initial Score": actual["initial_score"],
            "Expected Initial Band": expected["initial_band"] or MISSING, "Actual Initial Band": actual["initial_band"],
            "Expected Residual Score": expected["residual_score"] if expected["residual_score"] is not None else MISSING,
            "Actual Residual Score": actual["residual_score"],
            "Expected Residual Band": expected["residual_band"] or MISSING,
            "Actual Residual Band": actual["residual_band"],
            "Deterministic": "YES" if deterministic else "NO", "Result": outcome, "Evidence": evidence,
            "Module": module, "Country": country or "GLOBAL", "Governing Hazard": matrix["governing_hazard"],
            "Actual Risk Band (module)": result["risk_band"], "Actual Safety Override": bool(result["safety_override"]),
            "Independent Field Checks": " | ".join(field_checks) or "none (no hand-calculation basis)",
            "Controls Applied (residual scenario)": ", ".join(applied) or "none",
            "Methodology Version": METHODOLOGY_VERSION,
        })
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    counts = {k: outcomes.count(k) for k in ("PASS", "FAIL", "BLOCKED")}
    print(f"{len(rows)} cases -> {out}: {counts}")
    return 1 if counts["FAIL"] else 2 if counts["BLOCKED"] else 0


# Mandate C5 rows -> test names in tests/test_tenant_isolation_matrix.py
MATRIX_ROWS = [
    ("Read own record", "test_read_own_record", "Allowed according to role"),
    ("Cross-tenant read", "test_cross_tenant_read", "No data disclosure"),
    ("Spoof tenant ID", "test_spoof_tenant_id", "Rejected or safely constrained"),
    ("Spoof author", "test_spoof_author", "Rejected"),
    ("Ownership update", "test_ownership_update", "Ownership cannot be transferred"),
    ("Cross-tenant delete", "test_cross_tenant_delete", "No unauthorized side effect"),
    ("Export/download", "test_export_across_tenants", "No unauthorized disclosure"),
    ("Membership revoked", "test_membership_revoked", "Denied according to session design"),
    ("Insufficient role", "test_insufficient_role", "Denied"),
    ("Unauthenticated / no identity", "test_unauthenticated_has_no_access|test_no_identity_sees_nothing", "No access"),
    ("Privilege escalation", "test_org_admin_cannot_escalate|test_application_role_cannot_bypass", "Denied"),
    ("Audit ledger tampering", "test_audit_log_is_append_only_for_the_application", "Denied"),
    ("Device token takeover", "test_release_token_requires_identity", "Denied"),
]


def tenant_matrix(junits: list[str], out: str) -> int:
    results = []
    for path in junits:
        backend = "postgresql" if "postgres" in os.path.basename(path) else "sqlite"
        for tc in ET.parse(path).getroot().iter("testcase"):
            if "test_tenant_isolation_matrix" not in tc.get("classname", ""):
                continue
            status = "PASS"
            if tc.find("failure") is not None or tc.find("error") is not None:
                status = "FAIL"
            elif tc.find("skipped") is not None:
                status = "SKIPPED"
            layer = "database (RLS, raw SQL as app role)" if "RowLevelSecurity" in tc.get("classname") \
                else "application"
            results.append((backend, layer, tc.get("name"), status))
    rows, failed = [], 0
    for label, pattern, required in MATRIX_ROWS:
        names = pattern.split("|")
        for backend, layer, name, status in results:
            if any(name.startswith(n) for n in names) and status != "SKIPPED":
                failed += status == "FAIL"
                rows.append({"Test": label, "Required result": required, "Layer": layer, "Backend": backend,
                             "Test identity": "alice (Org A supervisor) unless named in test",
                             "Test case": f"tests/test_tenant_isolation_matrix.py::{name}", "Actual": status})
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} matrix rows -> {out}: {failed} failed")
    return 1 if failed else 0


def environment(out: str) -> int:
    def run(cmd):
        try:
            return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=30).stdout.strip()
        except Exception as exc:  # noqa: BLE001
            return f"unavailable ({exc.__class__.__name__})"
    from analytics import SCHEMA_REVISION
    from maku_core import METHODOLOGY_VERSION
    record = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": run(["git", "rev-parse", "HEAD"]),
        "git_branch": run(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "git_dirty": bool(run(["git", "status", "--porcelain"])),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "postgresql_server": run(["psql", "--version"]),
        "schema_revision": SCHEMA_REVISION,
        "rls_policy_version": "migrations/versions/0003_row_level_security.py",
        "methodology_version": METHODOLOGY_VERSION,
        "requirements_sha256": hashlib.sha256(open(os.path.join(ROOT, "requirements.txt"), "rb").read()).hexdigest(),
        "installed_packages": run([sys.executable, "-m", "pip", "freeze"]).splitlines(),
    }
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)
    print(f"environment -> {out}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("reference-cases")
    p.add_argument("--out", default=os.path.join(ROOT, "docs", "audit", "reference_case_comparison.csv"))
    p = sub.add_parser("tenant-matrix")
    p.add_argument("--junit", action="append", required=True)
    p.add_argument("--out", default=os.path.join(ROOT, "docs", "audit", "tenant_isolation_matrix.csv"))
    p = sub.add_parser("environment")
    p.add_argument("--out", default=os.path.join(ROOT, "docs", "audit", "environment.json"))
    args = parser.parse_args(argv)
    if args.command == "reference-cases":
        return reference_cases(args.out)
    if args.command == "tenant-matrix":
        return tenant_matrix(args.junit, args.out)
    return environment(args.out)


if __name__ == "__main__":
    sys.exit(main())
