"""
Residual risk after applied controls - methodology 2.0.0
=========================================================
Replaces the 1.x rule (risk_matrix.apply_controls_residual_risk), which
lowered the governing hazard's likelihood by 1 for EVERY ticked control,
whether or not that control addressed it: ticking "hydration breaks" lowered
an arc-flash risk. That cannot be defended in an independent review
(pre-launch review finding F4).

Rules (per hazard, on the 5x5 matrix of risk_matrix.py):
  1. A control is credited only against the hazards it is tagged with
     (maku_core.controls). Controls MAKU did not recommend for this result,
     and "monitoring" advice, are never credited.
  2. elimination (stop work, de-energize, evacuate, remove the operator):
     likelihood becomes 1 ("rare") while the control is in place.
  3. engineering, administrative, ppe: likelihood -1 per applied control.
  4. Likelihood never goes below 1. SEVERITY IS NEVER REDUCED - the
     consequence if the hazard does occur is unchanged by these controls;
     a genuine severity reduction needs an engineering redesign judged by a
     competent person, which this screening tool does not certify.
  5. The module result is re-aggregated with the same "worst hazard governs"
     rule as the initial assessment, so another hazard can become governing.

These are screening conventions, not measured control effectiveness. The
output records, per hazard, exactly which controls were credited.
"""
from __future__ import annotations

from risk_matrix import aggregate_risk_matrix, score_hazard

from .controls import Control
from .version import METHODOLOGY_VERSION


def residual_risk(risk_matrix: dict, applied: list[Control]) -> dict:
    """aggregate_risk_matrix()-shaped result plus:
         methodology_version
         credited: {hazard name: [control ids]}
         uncredited_controls: ids of applied controls that address no scored hazard
    """
    hazards = (risk_matrix or {}).get("hazards", [])
    credited: dict[str, list[str]] = {}
    residual_hazards = []
    for hazard in hazards:
        relevant = [c for c in applied if hazard["name"] in c.hazards and c.level != "monitoring"]
        likelihood = hazard["likelihood"]
        if any(c.level == "elimination" for c in relevant):
            new_likelihood = 1
        else:
            new_likelihood = max(1, likelihood - len(relevant))
        if relevant:
            credited[hazard["name"]] = [c.id for c in relevant]
        if new_likelihood != likelihood:
            note = (hazard.get("note", "") + f" | Residual: likelihood {likelihood} -> {new_likelihood} "
                    f"({', '.join(c.id for c in relevant)}); severity unchanged.")
            residual_hazards.append(score_hazard(hazard["name"], new_likelihood, hazard["severity"], note=note))
        else:
            residual_hazards.append(hazard)
    result = aggregate_risk_matrix(residual_hazards)
    scored = {h["name"] for h in hazards}
    result["methodology_version"] = METHODOLOGY_VERSION
    result["credited"] = credited
    result["controls_applied_count"] = len(applied)
    result["uncredited_controls"] = [c.id for c in applied if not (set(c.hazards) & scored)]
    return result
