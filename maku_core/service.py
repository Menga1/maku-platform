"""
run_assessment(): the one entry point for a MAKU risk assessment.
=================================================================
Validates inputs against the module registry, runs the risk_engine.py
formula with the regulatory profile for the chosen country, attaches the
tagged controls, and stamps the methodology version. Pure Python: no
Streamlit, no database, no network - the same call serves the web app, a
future REST API (FastAPI etc.) for a Flutter / React Native app, and the
reference-case tests.

    from maku_core import run_assessment, residual_risk_for
    a = run_assessment("data_center", {"hot_aisle_temp": 41, "ceiling_void_confined": True,
                                       "gas_system_armed": True}, country="UAE")
    a["result"]["risk_band"], a["controls"][0]["id"]
    residual_risk_for(a, ["data_center.unknown_ie_no_live_work"])
"""
from __future__ import annotations

import math
import numbers

from regulatory_country_thresholds import FALLBACK_COUNTRY_CODE, REGULATORY_PROFILES, get_regulatory_profile

from .controls import controls_for_result, resolve_applied
from .modules import MODULES, ModuleSpec
from .residual import residual_risk
from .version import METHODOLOGY_VERSION


class InputError(ValueError):
    """Invalid assessment request. .problems lists every issue found."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


def get_module(module_key: str) -> ModuleSpec:
    try:
        return MODULES[module_key]
    except KeyError:
        raise InputError([f"unknown module '{module_key}' (known: {', '.join(MODULES)})"]) from None


def validate_inputs(module_key: str, inputs: dict) -> dict:
    """Returns clean keyword arguments for the engine function, or raises
    InputError listing every problem (unknown fields, missing required
    fields, wrong types, out-of-range or non-finite numbers, bad choices)."""
    spec = get_module(module_key)
    inputs = dict(inputs or {})
    problems: list[str] = []
    known = {f.name for f in spec.fields}
    for name in sorted(set(inputs) - known):
        problems.append(f"unknown field '{name}'")
    clean: dict = {}
    for f in spec.fields:
        value = inputs.get(f.name)
        if value is None:
            if f.required:
                problems.append(f"'{f.name}' is required")
            elif f.default is not None:
                clean[f.name] = f.default
            elif f.kind == "number":
                clean[f.name] = None
            continue
        if f.kind == "number":
            if isinstance(value, bool) or not isinstance(value, numbers.Real):   # numpy numbers included
                problems.append(f"'{f.name}' must be a number")
                continue
            value = float(value)
            if not math.isfinite(value):
                problems.append(f"'{f.name}' must be a finite number")
                continue
            if (f.minimum is not None and value < f.minimum) or (f.maximum is not None and value > f.maximum):
                problems.append(f"'{f.name}' = {value:g} is outside the plausible range "
                                f"{f.minimum:g}..{f.maximum:g} {f.unit}".rstrip())
                continue
        elif f.kind == "bool":
            if type(value).__name__ == "bool_":       # numpy.bool_
                value = bool(value)
            if not isinstance(value, bool):
                problems.append(f"'{f.name}' must be true or false")
                continue
        elif f.kind == "choice":
            if value not in f.choices:
                problems.append(f"'{f.name}' must be one of: {', '.join(f.choices)}")
                continue
        clean[f.name] = value
    if problems:
        raise InputError(problems)
    return clean


def run_assessment(module_key: str, inputs: dict, country: str | None = None,
                   regulatory_profile: dict | None = None) -> dict:
    """{
         "methodology_version", "module_key", "module", "country",
         "inputs":   validated inputs actually used,
         "result":   the risk_engine.py result (risk_band, safety_override,
                     risk_matrix, citations, ... + methodology_version),
         "controls": [{id, text, hazards, level}],
       }
    Pass either `country` (a code from regulatory_country_thresholds, e.g.
    "UAE"; omitted = the GLOBAL reference profile; unknown codes are
    rejected) or an already-resolved `regulatory_profile`."""
    spec = get_module(module_key)
    kwargs = validate_inputs(module_key, inputs)
    if country is not None and country not in REGULATORY_PROFILES:
        # Explicit, not a silent substitution of another country's limits.
        raise InputError([f"unknown country '{country}' (known: {', '.join(REGULATORY_PROFILES)})"])
    if regulatory_profile is None:
        regulatory_profile = get_regulatory_profile(country or FALLBACK_COUNTRY_CODE)
    result = spec.function(**kwargs, regulatory_profile=regulatory_profile)
    result["methodology_version"] = METHODOLOGY_VERSION
    return {
        "methodology_version": METHODOLOGY_VERSION,
        "module_key": module_key,
        "module": result.get("module", spec.name),
        "country": regulatory_profile.get("country_code") if isinstance(regulatory_profile, dict) else None,
        "inputs": kwargs,
        "result": result,
        "controls": [c.as_dict() for c in controls_for_result(result)],
    }


def residual_risk_for(assessment_or_result: dict, applied: list[str]) -> dict:
    """Residual risk for an assessment (from run_assessment) or a bare engine
    result, given the control ids or texts marked as applied on site."""
    result = assessment_or_result.get("result", assessment_or_result)
    return residual_risk(result.get("risk_matrix") or {}, resolve_applied(result, applied))


def input_schema(module_key: str) -> dict:
    """JSON Schema (draft 2020-12) of a module's inputs - for API docs and
    for generating mobile forms."""
    spec = get_module(module_key)
    props, required = {}, []
    for f in spec.fields:
        if f.kind == "number":
            p = {"type": "number", "minimum": f.minimum, "maximum": f.maximum}
        elif f.kind == "bool":
            p = {"type": "boolean"}
        else:
            p = {"type": "string", "enum": list(f.choices)}
        if f.unit:
            p["x-unit"] = f.unit
        if f.description:
            p["description"] = f.description
        if f.default is not None:
            p["default"] = f.default
        props[f.name] = p
        if f.required:
            required.append(f.name)
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": spec.name,
            "description": spec.description, "type": "object", "properties": props,
            "required": required, "additionalProperties": False}
