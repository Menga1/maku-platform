# Risk engine contract (for a future mobile API)

`maku_core` is MAKU's risk methodology as a plain Python library with no Streamlit, no database and no network calls. A REST service for a Flutter or React Native app only needs to wrap four functions. This file is the contract that service should expose. The service itself is **not built yet**.

## Library calls

```python
from maku_core import MODULES, input_schema, run_assessment, residual_risk_for, InputError

MODULES                                   # {"solar": ModuleSpec, ...}  (9 modules)
input_schema("data_center")               # JSON Schema of the inputs (units in "x-unit")
a = run_assessment("data_center", {"hot_aisle_temp": 48, "ceiling_void_confined": True,
                                   "gas_system_armed": True}, country="UAE")
residual_risk_for(a, ["data_center.unknown_ie_no_live_work"])
```

Try it from a shell: `python -m maku_core modules | schema <module> | run <module> '<json>' [--country UAE] [--applied <control ids>]`.

## Proposed endpoints

| Method and path | Library call | Notes |
|---|---|---|
| `GET /v1/modules` | `MODULES` | key, name, description |
| `GET /v1/modules/{module}/schema` | `input_schema(module)` | Drives the mobile form |
| `POST /v1/assessments/{module}` | `run_assessment(module, body.inputs, country=body.country)` | 422 with `problems[]` on `InputError` |
| `POST /v1/assessments/{id}/residual` | `residual_risk_for(stored_assessment, body.applied)` | `applied` = control ids |

### Request: `POST /v1/assessments/data_center`

```json
{ "country": "UAE",
  "inputs": { "hot_aisle_temp": 48, "ceiling_void_confined": true, "gas_system_armed": true,
              "label_incident_energy_cal": null } }
```

### Response: 200

```json
{ "methodology_version": "2.0.0", "module_key": "data_center",
  "module": "Data Center (Controlled Critical Environment)", "country": "UAE",
  "inputs": { "...": "validated values actually used" },
  "result": { "risk_band": "CRITICAL", "safety_override": true, "arc_flash_energy_cal": null,
              "arc_flash_study_required": true,
              "risk_matrix": { "overall_score": 25, "governing_hazard": "Arc-flash incident energy",
                               "hazards": [ { "name": "...", "likelihood": 5, "severity": 5, "score": 25 } ] },
              "...": "all module fields" },
  "controls": [ { "id": "data_center.unknown_ie_no_live_work", "level": "elimination",
                  "hazards": ["Arc-flash incident energy"], "text": "Arc-flash incident energy is UNKNOWN: ..." } ] }
```

### Response: 422

```json
{ "error": "invalid_input", "problems": ["'hot_aisle_temp' is required", "unknown country 'AE' (known: USA, ...)"] }
```

## Requirements the service must keep

The library deliberately leaves these to the service layer:

1. **Authentication** with the same accounts and Argon2id hashes (`accounts.py`). Use short-lived tokens, never the password, on each call.
2. **Tenant isolation:** every stored assessment belongs to an organization. Call `tenancy.require_access(principal, organization_id, "write" | "read")` before storing or returning anything (see `tenancy.py` and release gate 01).
3. **Strict persistence:** `MAKU_ENV=production` rules (PostgreSQL only, explicit failure) apply to the API process too.
4. **Methodology version:** store `methodology_version` with every assessment, and never recompute an old assessment with a newer version without saying so.
5. **Human approval:** a `safety_override: true` result must be acknowledged by a named, competent person in the client. The API must not let a client dismiss it silently.
