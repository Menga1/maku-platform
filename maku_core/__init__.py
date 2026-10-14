"""
maku_core - MAKU's risk methodology as a plain Python library.
==============================================================
Everything needed to run an assessment without the Streamlit interface:

    from maku_core import run_assessment, residual_risk_for, input_schema, MODULES
    a = run_assessment("solar", {"ghi": 950, "uv_index": 9, "ambient_temp": 42,
                                 "surface_type": "silicon_pv_panels"}, country="UAE")
    a["result"]["risk_band"]                  # 'High'
    residual_risk_for(a, ["solar.cooling"])   # matrix after that control

Layers (inner layers never import outer ones):
    risk_engine.py, risk_matrix.py, regulatory_*.py   formulas, bands, thresholds
    maku_core.controls / .residual                    tagged controls, residual rule
    maku_core.service                                 validation + run_assessment
    app.py (Streamlit) / a future REST API            presentation only

See docs/METHODOLOGY.md for the rules and docs/RISK_ENGINE_API.md for the
request/response contract.
"""
from .controls import Control, controls_for_result, resolve_applied
from .modules import MODULE_KEY_BY_NAME, MODULES
from .residual import residual_risk
from .service import InputError, input_schema, residual_risk_for, run_assessment, validate_inputs
from .version import METHODOLOGY_DATE, METHODOLOGY_VERSION

__all__ = [
    "Control", "InputError", "METHODOLOGY_DATE", "METHODOLOGY_VERSION", "MODULES", "MODULE_KEY_BY_NAME",
    "controls_for_result", "input_schema", "resolve_applied", "residual_risk", "residual_risk_for",
    "run_assessment", "validate_inputs",
]
