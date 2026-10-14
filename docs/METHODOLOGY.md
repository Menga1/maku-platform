# MAKU risk methodology

**Current version: 2.0.0 (14 October 2026)**, defined in `maku_core/version.py`. Every result, residual calculation and PDF/HTML report records the version that produced it.

MAKU is a screening and decision-support tool. It does not replace a competent person, a permit-to-work system, an IEEE 1584 arc-flash study, or a certified engineering assessment.

## 1. Where each rule lives

| Layer | File | What it decides |
|---|---|---|
| Formulas and bands | `risk_engine.py` | The physical calculation per module (Humidex, power-law wind, Lee arc flash, OSHA noise dose, A(8)...) and its band |
| Country thresholds | `regulatory_country_thresholds.py` | Limits that differ by jurisdiction (heat, wind, noise criterion, silica) |
| Risk matrix | `risk_matrix.py` | 5×5 likelihood × severity per hazard; "worst hazard governs" aggregation |
| Controls | `maku_core/controls.py` | Recommended controls, each tagged with the hazards it reduces and its level in the hierarchy of controls |
| Residual risk | `maku_core/residual.py` | How applied controls change likelihood (see §3) |
| Entry point | `maku_core/service.py` | Input validation and `run_assessment()`, used by the web app and any future API |

The Streamlit pages only collect inputs and display results. They contain no risk logic.

## 2. Initial risk (unchanged from 1.x)

Each module scores each hazard separately:

- **Severity (1–5)** is the module's own band (LOW / MODERATE / HIGH / CRITICAL, or Low / Moderate / High / Extreme), mapped in order.
- **Likelihood (1–5)** reflects how close the current reading is to the documented trigger threshold: 5 means it is already crossed, 1 means it is well clear.
- **Score** = likelihood × severity (1–25). Bands: Low 1–4 · Moderate 5–9 · High 10–15 · Extreme 16–25.
- The module result is the worst-scoring hazard.

## 3. Residual risk: changed in 2.0.0

| | 1.x (withdrawn) | 2.0.0 |
|---|---|---|
| Which hazard a control reduces | Always the governing hazard, whatever the control | Only the hazards the control is tagged with |
| Effect of one applied control | Likelihood −1 | Elimination (stop work, de-energize, evacuate, remove the operator): likelihood → 1 · Engineering, administrative, PPE: −1 each |
| Monitoring advice ("keep monitoring") | Counted as a control | Never credited |
| Controls not recommended for this result | Counted | Ignored |
| Severity | Never reduced | Never reduced |
| Floor | Likelihood 1 | Likelihood 1 |

**Why it changed.** Under 1.x, ticking "rotate crews and hydrate" lowered a data centre's arc-flash risk, which no independent reviewer would accept (pre-launch review, finding F4). Each control now carries a `hazards` tag, and a test checks that every tag matches a hazard name the engine actually scores.

**What it is not.** These are screening conventions, not measured control effectiveness. The output lists, for each hazard, which controls were credited, so a reviewer can see exactly why the score moved.

## 4. Inputs

Each module's inputs, units and plausibility ranges are defined in `maku_core/modules.py`. Ranges reject typos and unit mistakes (for example 104 entered for °C); they are not safety thresholds. Invalid inputs are refused with the full list of problems; MAKU never guesses a value. Unknown country codes are refused rather than replaced by another country's limits.

## 5. Reference cases and independent review

`tests/reference_cases/*.json` holds worked cases for every module, run on every test pass.

- Fields marked *hand calculation* were computed from the published formula independently of `risk_engine.py`:
  - Lee (1982) arc-flash energy
  - Power-law wind profile
  - Environment Canada Humidex, via dew point
  - OSHA 29 CFR 1910.95 noise dose
  - ISO 2631-1 A(8) vibration exposure
- Bands and safety overrides are MAKU's own thresholds. They are regression baselines until a competent HSE professional reviews each case and fills in `reviewed_by`, `reviewed_on` and `review_status`.
- The test run prints `[reference cases] N/M independently reviewed`. **Release gate 03 requires M/M.**

To add a case, append it to the module's JSON file with its inputs, the expected band, override and fields (with tolerance), and the basis for each expected value.

## 6. Changing the methodology

1. Change the rule, add or adjust reference cases, and run the tests.
2. Bump `METHODOLOGY_VERSION`: major if any existing result can change band or residual score, minor for additions, patch for wording.
3. Add a line to the history below.

## History

| Version | Date | Change |
|---|---|---|
| 2.0.0 | 2026-10-14 | Residual risk credits only controls that address the hazard; elimination → rare; monitoring never credited. Methodology version stamped on results and reports. Unknown country codes rejected by the library. |
| 1.x | before 2026-10-14 | Lee constant corrected to 5.12×10⁵; power-law wind; load never used for arc flash (see README "Production hardening"). |
