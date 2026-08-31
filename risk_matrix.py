"""
MAKU Risk Matrix Scoring Engine
================================
Implements the classic 5x5 Likelihood x Severity risk matrix (the ISO
31010 / HSE-style convention), which is the industry-standard instrument
behind the numeric risk-band thresholds this refactor requires:

    Score = Likelihood (1-5) x Severity (1-5)      range: 1-25
    Low: 1-4   Moderate: 5-9   High: 10-15   Extreme/Critical: 16-25

These band edges are not arbitrary round numbers picked to look official -
they are the textbook cut-points a 5x5 matrix naturally produces (the
lowest-likelihood/lowest-severity cell scores 1x1=1; the
almost-certain/catastrophic cell scores 5x5=25), which is exactly why a
5x5 matrix is the right instrument for the requested bands rather than
some other arbitrary scale.

ARCHITECTURE - PURELY ADDITIVE:
This module does not replace or recompute any hazard value in
risk_engine.py. Every calculate_*_kinetic_risk() function there hands its
ALREADY-COMPUTED driver values (WBGT margin above the ACGIH limit, dB over
the noise criterion, arc-flash incident energy, etc.) to score_hazard()
below, which converts each one into a documented (likelihood, severity)
pair. Nothing here invents a new environmental reading or threshold - it
re-expresses values and bands risk_engine.py already computed and already
tests, on the matrix's numeric axis, broken out per hazard as required
("individual hazards ... must be scored, rated, and displayed separately
before being aggregated").

LIKELIHOOD CONVENTION (explicit, not a fitted probability model):
This is a deterministic screening tool, not an actuarial risk model -
there is no historical incident-frequency dataset behind these numbers,
and pretending otherwise would be dishonest. The five likelihood levels
instead encode something a live screening tool CAN actually and
transparently compute: how close the CURRENT reading is to the
already-documented trigger/exceedance threshold for that hazard.
    5  Almost certain - the hazard is ACTIVE now (reading has already
       crossed its documented trigger/exceedance threshold)
    4  Likely          - within a narrow margin of the threshold
    3  Possible         - moderate margin, trending toward the threshold
    2  Unlikely         - comfortable margin below the threshold
    1  Rare              - well clear of the threshold
See likelihood_from_margin() below for the exact rule.

SEVERITY CONVENTION:
severity_from_band() maps risk_engine.py's OWN existing band label
(LOW/MODERATE/HIGH/CRITICAL, or Low/Moderate/High/Extreme - both
vocabularies appear across the 8 modules) directly onto the 1-5 severity
axis, in the same relative order those bands have always ranked. Severity
is therefore never a second, disconnected judgment call bolted on
separately from the existing, already-tested band logic - it is that same
band, just expressed on the matrix's numeric axis.
"""

from __future__ import annotations

RISK_MATRIX_BAND_THRESHOLDS = [
    (4, "Low"),
    (9, "Moderate"),
    (15, "High"),
    (25, "Extreme"),
]

# Existing risk_engine.py band vocabularies map onto the matrix's 1-5
# severity axis, preserving the same relative ranking those bands already
# carry throughout this codebase.
_SEVERITY_FROM_BAND = {
    "LOW": 1, "Low": 1,
    "MODERATE": 3, "Moderate": 3,
    "HIGH": 4, "High": 4,
    "CRITICAL": 5, "Extreme": 5, "EXTREME": 5,
}


def matrix_score(likelihood: int, severity: int) -> int:
    """Score = Likelihood x Severity, each clamped to the valid 1-5 range
    so a caller passing an out-of-range value degrades safely rather than
    producing a score outside the documented 1-25 scale."""
    likelihood = min(max(int(likelihood), 1), 5)
    severity = min(max(int(severity), 1), 5)
    return likelihood * severity


def matrix_band(score: int) -> str:
    """Maps a 1-25 matrix score onto Low/Moderate/High/Extreme using the
    exact hardcoded thresholds this refactor requires: Low 1-4,
    Moderate 5-9, High 10-15, Extreme 16-25."""
    for threshold, label in RISK_MATRIX_BAND_THRESHOLDS:
        if score <= threshold:
            return label
    return RISK_MATRIX_BAND_THRESHOLDS[-1][1]


def severity_from_band(band_label: str, default: int = 3) -> int:
    """Converts an existing risk_engine.py band label into the matrix's
    1-5 severity axis. An unrecognized label falls back to 3 (the middle
    of the scale) rather than silently understating or overstating
    severity for a band this function doesn't recognize."""
    return _SEVERITY_FROM_BAND.get(band_label, default)


def likelihood_from_margin(current_value: float, threshold: float, comfortable_margin: float) -> int:
    """Derives a 1-5 likelihood from how close `current_value` is to
    `threshold`, for a hazard where EXCEEDING the threshold is the unsafe
    direction (current_value > threshold means the hazard has triggered).
    `comfortable_margin` is in the same units as current_value/threshold -
    the distance below the threshold this hazard's own domain treats as
    "clearly fine" (e.g. 3 degC of WBGT headroom, 10 dB of noise
    headroom); each call site documents its own choice of margin inline,
    the same way this codebase already documents every illustrative
    screening constant elsewhere.

    This is a deterministic, reproducible rule - not a fitted/calibrated
    probability - consistent with this module's LIKELIHOOD CONVENTION
    note above."""
    margin = threshold - current_value
    if margin <= 0:
        return 5  # already at/past the threshold - almost certain
    if margin <= comfortable_margin * 0.25:
        return 4
    if margin <= comfortable_margin * 0.6:
        return 3
    if margin <= comfortable_margin:
        return 2
    return 1


def score_hazard(name: str, likelihood: int, severity: int, note: str = "") -> dict:
    """Builds one hazard's matrix entry - the atomic unit every module's
    risk_matrix breakdown list is built from. Returns {"name",
    "likelihood", "severity", "score", "band", "note"}."""
    score = matrix_score(likelihood, severity)
    return {
        "name": name,
        "likelihood": likelihood,
        "severity": severity,
        "score": score,
        "band": matrix_band(score),
        "note": note,
    }


def aggregate_risk_matrix(hazards: list[dict]) -> dict:
    """Combines a list of score_hazard() entries into the module-level
    matrix result: {"hazards", "overall_score", "overall_band",
    "governing_hazard"}. overall = the worst (max-score) individual
    hazard - the same "worst hazard governs" aggregation rule
    risk_engine.py's existing risk_band()-based modules already apply,
    just expressed numerically here."""
    if not hazards:
        return {"hazards": [], "overall_score": 0, "overall_band": "Low", "governing_hazard": None}
    worst = max(hazards, key=lambda h: h["score"])
    return {
        "hazards": hazards,
        "overall_score": worst["score"],
        "overall_band": worst["band"],
        "governing_hazard": worst["name"],
    }


def apply_controls_residual_risk(risk_matrix: dict, num_controls_applied: int) -> dict:
    """
    HSE audit corrective action - 2-stage risk workflow: Initial Risk ->
    Applied Controls -> Calculated Residual Risk. Given an already-computed
    initial risk_matrix (an aggregate_risk_matrix() result), models the
    RESIDUAL risk after num_controls_applied documented controls have been
    marked as implemented on site.

    METHODOLOGY (explicit, conservative, and deliberately NOT a fabricated
    quantitative "% risk reduction per control" - this tool has no
    empirical effectiveness data for any specific control, and asserting
    one would be exactly the kind of unjustified number this audit exists
    to eliminate):
      - Each applied control reduces the GOVERNING hazard's LIKELIHOOD by
        exactly 1 point on the already-established 1-5 scale, floored at 1
        ("rare") - it can never go below that floor no matter how many
        controls are marked applied.
      - SEVERITY IS NEVER REDUCED by this function. This follows the
        standard hierarchy-of-controls principle: administrative and PPE-
        level controls (the kind get_controls() in ai_advisor.py
        recommends) reduce the LIKELIHOOD of harm occurring, not the
        inherent severity of the hazard if it does occur. A genuine
        severity reduction would require an engineering/elimination/
        substitution control, which is a site-engineering judgment this
        screening tool does not claim to certify - so it is conservatively
        left untouched.
      - After the governing hazard's likelihood is reduced, the FULL
        hazard list is re-aggregated via aggregate_risk_matrix() (not just
        the one hazard recomputed in isolation) - if a different hazard
        now dominates because the previously-worst one was brought down,
        that hazard correctly becomes the new governing one, exactly as
        the initial assessment's own "worst hazard governs" rule works.

    Returns an aggregate_risk_matrix()-shaped dict plus two extra keys so
    a caller/UI can show exactly how much reduction was modeled - never
    silently: "controls_applied_count" (the input, echoed back) and
    "likelihood_reduction_applied" (the actual reduction after the floor-
    at-1 cap, which may be less than num_controls_applied).
    """
    hazards = risk_matrix.get("hazards", [])
    if not hazards:
        return {
            "hazards": [], "overall_score": 0, "overall_band": "Low", "governing_hazard": None,
            "controls_applied_count": num_controls_applied, "likelihood_reduction_applied": 0,
        }

    governing_name = risk_matrix.get("governing_hazard")
    governing = next((h for h in hazards if h["name"] == governing_name), max(hazards, key=lambda h: h["score"]))

    num_controls_applied = max(int(num_controls_applied), 0)
    reduction = min(num_controls_applied, governing["likelihood"] - 1)
    new_likelihood = governing["likelihood"] - reduction

    reduced_hazard = score_hazard(
        governing["name"],
        new_likelihood,
        governing["severity"],
        note=governing.get("note", "")
        + f" | Residual after {num_controls_applied} applied control(s): likelihood "
          f"{governing['likelihood']} -> {new_likelihood} (severity unchanged - see "
          f"apply_controls_residual_risk() methodology).",
    )
    residual_hazards = [reduced_hazard if h["name"] == governing["name"] else h for h in hazards]
    result = aggregate_risk_matrix(residual_hazards)
    result["controls_applied_count"] = num_controls_applied
    result["likelihood_reduction_applied"] = reduction
    return result
