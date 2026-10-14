"""Command-line use, e.g. to check a case by hand or from another language:

    python -m maku_core modules
    python -m maku_core schema data_center
    python -m maku_core run solar '{"ghi": 950, "uv_index": 9, "ambient_temp": 42, "surface_type": "silicon_pv_panels"}' --country UAE
    python -m maku_core run high_rise @case.json --applied high_rise.override

Prints JSON. Exit code 2 on invalid input.
"""
import argparse
import json
import sys

from . import MODULES, InputError, input_schema, residual_risk_for, run_assessment


def _load(arg: str) -> dict:
    if arg.startswith("@"):
        with open(arg[1:], encoding="utf-8") as fh:
            return json.load(fh)
    return json.loads(arg)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m maku_core")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("modules")
    s = sub.add_parser("schema")
    s.add_argument("module")
    r = sub.add_parser("run")
    r.add_argument("module")
    r.add_argument("inputs", help="JSON object, or @file.json")
    r.add_argument("--country", default=None)
    r.add_argument("--applied", nargs="*", default=[], help="control ids applied on site")
    a = p.parse_args(argv)
    try:
        if a.cmd == "modules":
            out = {k: {"name": m.name, "description": m.description} for k, m in MODULES.items()}
        elif a.cmd == "schema":
            out = input_schema(a.module)
        else:
            out = run_assessment(a.module, _load(a.inputs), country=a.country)
            if a.applied:
                out["residual"] = residual_risk_for(out, a.applied)
    except InputError as exc:
        print(json.dumps({"error": "invalid_input", "problems": exc.problems}, indent=2))
        return 2
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
