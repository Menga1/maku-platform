# MAKU — Response to the Pre-Launch Independent Audit Mandate

**Mandate:** *Pre-Launch Independent Audit Mandate — HSE Risk Engine Validation · API Security · Tenant Isolation* (review date 14 October 2026, status HOLD).
**Prepared by:** Claude, acting as software engineer for MAKU. This is an internal engineering response. It is not an independent review, an external penetration test or a certification.
**Date:** 14 October 2026.

**Decision (detail in item 11):**
- **Release Gate 03 — BLOCKED.** No independently approved expected values exist for the 21 reference cases.
- **Security gate — BLOCKED.** No external penetration test has been performed.

No blocker below has been relabelled as closed.

---

## Evidence package at a glance

| Mandate artifact (D2) | Where |
|---|---|
| 1. HSE reference validation report | Item 4 below; `docs/audit/reference_case_comparison.csv` (the A7 columns) |
| 2. Risk engine technical note | `docs/METHODOLOGY.md`, `docs/RISK_ENGINE_API.md`, and item 3 below |
| 3. Automated test results | `docs/audit/test_run_sqlite.log`, `docs/audit/test_run_postgres.log`, `docs/audit/junit_*.xml`; commands in item 1 |
| 4. Tenant isolation matrix | Item 6 below; `docs/audit/tenant_isolation_matrix.csv` |
| 5. Database security review (RLS, grants, functions, privileged paths) | Item 8 below; `migrations/versions/0003_row_level_security.py` |
| 6. Authentication review | Item 7 below |
| 7. External penetration-test report | **Not available.** Item 9 |
| 8. Remediation register | Item 5 below |
| 9. Release gate sign-off | Item 11 below |
| D1 environment record | Item 1 below; `docs/audit/environment.json` |
| Static analysis (internal, supporting only) | `docs/audit/bandit.txt`, `docs/audit/pip_audit.txt` |

---

## 1. Source commit and application architecture

### Environment record (D1)

| | |
|---|---|
| Repository | `Menga1/maku-platform`, branch `audit/pre-launch-evidence` |
| Base commit at the start of the audit | `5e689aa` (main) |
| **Code commit the evidence was produced on** | **`f4b7675`**. Code changes are in `4863c7a` and `f4b7675`. Evidence files were generated on `f4b7675` before they were committed, which is why `environment.json` reports `git_dirty: true`: the only untracked files were the `docs/audit/` outputs themselves. |
| Runtime | Python 3.13.16 on Linux x86_64; PostgreSQL 16.15 for the database-layer tests |
| Locked dependencies | `requirements.txt` (exact pins, sha256 `0a51d4a5…f1`); full `pip freeze` in `docs/audit/environment.json` |
| Database schema / migration version | Alembic head `0003_row_level_security` (`analytics.SCHEMA_REVISION`) |
| RLS policy version | `migrations/versions/0003_row_level_security.py` |
| Risk methodology version | `2.0.0` (`maku_core/version.py`), stamped on every result and report |
| Test accounts and roles (synthetic) | `platform.admin` (platform administrator)<br>**Org A:** `alice` (supervisor), `ada` (viewer), `amy` (org_admin)<br>**Org B:** `bob` (supervisor)<br>Throw-away local roles `maku_owner` (table owner) and `maku_app` (application role). No real users, organizations or customer data were used. |

**Commands and exit codes:**

```bash
# 1. Full suite, SQLite (development backend)
python -m pytest -p no:cacheprovider -q -rs --junitxml=docs/audit/junit_sqlite.xml
#    -> 685 passed, 54 skipped                                    exit code 0

# 2. Database-backed suites against PostgreSQL 16, connected as the APPLICATION role (RLS active)
MAKU_TEST_BACKEND=postgres \
MAKU_TEST_PG_URL=postgresql://maku_app:<redacted>@127.0.0.1:5432/maku_test \
MAKU_TEST_PG_OWNER_URL=postgresql://maku_owner:<redacted>@127.0.0.1:5432/maku_test \
python -m pytest -p no:cacheprovider -q -rs tests/ --junitxml=docs/audit/junit_postgres.xml
#    -> 423 passed, 25 skipped                                    exit code 0

# 3. Evidence tables
python scripts/audit_evidence.py reference-cases     # 21 cases: 0 PASS, 0 FAIL, 21 BLOCKED   exit code 2 (= BLOCKED)
python scripts/audit_evidence.py tenant-matrix --junit docs/audit/junit_sqlite.xml --junit docs/audit/junit_postgres.xml
#    -> 54 matrix rows, 0 failed                                  exit code 0
python scripts/audit_evidence.py environment         #                                         exit code 0

# 4. Production start-up, as the Docker entrypoint runs it
MAKU_ENV=production MIGRATION_DATABASE_URL=<owner> DATABASE_URL=<maku_app> python scripts/init_db.py
#    -> application role created, migrations 0001→0003 applied, "Database ready - schema revision 0003_row_level_security"   exit code 0

# 5. Supporting static checks (internal only, not a penetration test)
bandit -r . -x ./tests,./test_app.py,./mobile,./migrations --severity-level medium   # 15 medium, 0 high (reviewed: item 8)
pip-audit -r requirements.txt                                                        # "No known vulnerabilities found", exit code 0
```

**What the skipped tests are:**
- 21 are `test_approved_expected_value[…]`, each "BLOCKED: no independently approved expected value" (item 4).
- 30 are database-layer RLS tests, which only exist on PostgreSQL and run in command 2.
- The rest test SQLite-only or PostgreSQL-only paths.

**End-to-end check in a browser.** I started the app with `MAKU_ENV=production`, connected as `maku_app` (RLS active). A user signed in, ran a Solar assessment, and the row was stored with `organization_id=1` and `username=e2e.admin`. I then stopped PostgreSQL while the page was open and ran another assessment. The page showed **CRITICAL DATABASE ERROR**, "Aucune évaluation ne peut être enregistrée, et rien n'est enregistré ailleurs" ("No assessment can be saved, and nothing is being saved anywhere else"), and the row count stayed at 1. Screenshot: `docs/audit/evidence_db_outage_page.png`.

### Architecture

**MAKU does not use Supabase.** There is no Supabase Auth, PostgREST endpoint, RPC, Edge Function or storage bucket. The mandate's Supabase-specific items are answered for the architecture MAKU actually has:

| Component | What it is |
|---|---|
| Web application | One Python process: Streamlit 1.65 (`app.py`, 8 module pages plus Dashboard, My account and Users (admin)). The browser talks only to Streamlit over HTTP and WebSocket. **All authorization runs server-side in Python.** The browser can only send widget values. |
| Risk engine | `maku_core.run_assessment()`, which validates inputs and calls the `risk_engine.py` formulas. It then scores the matrix (`risk_matrix.py`), builds controls (`maku_core/controls.py`) and computes residual risk (`maku_core/residual.py`). The pages call it through `app.assess()` and contain no risk logic. |
| Database | PostgreSQL 16 in production, accessed with psycopg2 through a pooled SQLAlchemy engine (`db.py`). SQLite is used for local development only. Schema comes from Alembic migrations `0001_baseline`, `0002_tenancy` and `0003_row_level_security`. |
| Authentication | MAKU's own code (`auth.py`, `accounts.py`), with Argon2id password hashes (item 7). |
| Reverse proxy | Caddy 2: TLS, security headers, static legal pages, store verification files and `/healthz` (`deploy/Caddyfile`). |
| Mobile apps | Capacitor shells (`mobile/`) that load the same hosted web app with `?shell=ios` or `?shell=android`. There is no separate mobile backend. |
| Push notifications | Firebase Cloud Messaging (FCM) HTTP v1, sent from the server (`push.py`) with a service account that is never sent to clients. |

**Entry points and exposed surface (B1)**

| Surface | Where | Authorization |
|---|---|---|
| Streamlit HTTP + WebSocket (`/`, `/_stcore/stream`, `/_stcore/health`, `/_stcore/host-config`, `/media/*`, `/_stcore/upload_file/*`) | Caddy → `app:8501`. The app container publishes no port; it is reachable only through Caddy. | Every page calls `auth.require_login()` and `ui_helpers.render_database_gate()` first. Data functions re-check tenancy on every call. |
| CSV upload (merge a previous log) | `ui_helpers.py:1118` → `analytics.merge_uploaded_csv` | `write` permission in the session's organization. At most 20,000 rows. Organization and project columns are overwritten with the session's validated context. Files are parsed in memory and **never stored**. |
| URL parameter `?shell=` | `mobile_bridge.py:46` | Only selects the web or mobile behaviour. Grants nothing. |
| Static pages `/legal/*`, `/.well-known/*`, `/healthz` | Caddy | Public by design. Contain no data. |
| Operator CLI tools (`manage_users.py`, `scripts/*.py`) | Run on the server only (`docker compose exec`) | Run under `analytics.system_context()`, a platform-administrator identity. They are not reachable from the network. |
| Outbound calls | `data_feeds.py` (Open-Meteo, OpenWeatherMap, ipapi.co), `ai_advisor.py` (Anthropic API, opt-in), `push.py` (FCM) | Fixed hosts. The only client-derived value used in a URL is the client IP, which is now validated (AUD-14). |

**Database connection strings**

| Variable | Used by | Role |
|---|---|---|
| `DATABASE_URL` | The application at runtime (`analytics._resolve_backend`) | **`maku_app`**: no table ownership, no `SUPERUSER`, no `BYPASSRLS`. Row-level security applies. |
| `MIGRATION_DATABASE_URL` | `scripts/init_db.py` (migrations and grants), `scripts/migrate_sqlite_to_postgres.py` | Table owner |
| `MAKU_DB_PATH` | Development only (SQLite file) | Refused when `MAKU_ENV` is production or staging |

Both URLs are set in `.env`, which is never committed. Logs show URLs only through `db.redact_url()`, which hides the password. Git history check: across every commit, `secrets/` has only ever contained `.gitkeep`, and no `.env`, `.db`, `secrets.toml`, keystore or `.p8` file has ever been committed.

---

## 2. Files and functions inspected

| Area | Files and functions |
|---|---|
| Entry point and pages | `app.py`: page routing (`st.navigation` / `pg.run`), `assess`, `save_assessment`, `can_save_assessments`, `render_org_context_selector`, `on_assessment_logged`, push opt-in, site alert logging and display |
| Persistence | `analytics.py`: `_resolve_backend`, `_get_connection`, `_handle_db_failure`, `_disable_db_fatal`, `probe_database`, `verify_schema_revision`, `set_org_context`, `get_org_context`, `require_scope`, `log_assessment`, `get_log_dataframe`, `get_all_time_log_dataframe`, `merge_uploaded_csv`, `log_site_alert`, `get_site_alert_log_dataframe`, `log_audit_event`, `get_audit_log_dataframe`, `verify_audit_log_integrity`, `_get_or_create_id`, `_find_id`<br>`db.py`: `maku_env`, `strict_persistence`, `require_production_database`, `redact_url`, `get_engine` |
| Tenancy | `tenancy.py`: `principal_from_session`, `accessible_organizations`, `membership_role`, `can`, `require_access`, `create_organization`, `set_membership`, `remove_membership`<br>`push.py`: `register_device`, `_tokens_for_organization`, `_forget_token`, `notify_stop_work` |
| Authentication | `auth.py`: `require_login`, `_verify_credentials`, `_session_expired`, `_session_idle`, `_clear_session_identity`, `get_client_ip`<br>`accounts.py`: `hash_password`, `verify_password`, `needs_rehash`, `upgrade_stored_hash`, `create_user`, `change_password`, `record_login_attempt`, `lockout_status`, `export_user_data`, `erase_account_data`<br>`manage_users.py`, `scripts/audit_credentials.py`, `data_feeds.client_ip_from_headers` |
| Risk engine | `maku_core/service.py` (`validate_inputs`, `run_assessment`, `residual_risk_for`), `maku_core/residual.py`, `maku_core/controls.py` (`controls_for_result`, `resolve_applied`), `maku_core/modules.py`<br>`risk_matrix.py` (`matrix_score`, `matrix_band`, `severity_from_band`, `likelihood_from_margin`, `score_hazard`, `aggregate_risk_matrix`)<br>`risk_engine.py` (module functions, via the reference cases), `ai_advisor.generate_narrative`, `ui_helpers._build_report_pdf` |
| Schema and deployment | `migrations/env.py`, `migrations/versions/0001_baseline.py`, `0002_tenancy.py`, `0003_row_level_security.py` (new)<br>`scripts/init_db.py`, `scripts/migrate_sqlite_to_postgres.py`, `docker-compose.yml`, `docker-entrypoint.sh`, `Dockerfile`, `deploy/Caddyfile`, `.env.example`, `.gitignore`, `requirements*.txt` |
| UI rendering | `ui_helpers.render_database_gate`, `render_analytics_section`, HTML report rendering (`escape()` use at every `unsafe_allow_html` site, re-checked by listing all 12 sites) |
| Tests | `tests/reference_cases/*.json`, `tests/test_reference_cases.py`, `tests/test_maku_core.py`, `tests/test_tenancy.py`, `tests/test_database_guard.py`, `tests/test_passwords.py`, `test_app.py`<br>New: `tests/test_gate03_golden.py`, `tests/test_tenant_isolation_matrix.py` |

---

## 3. Authoritative source and version of the 21 reference cases

**There is no authoritative, independently approved reference set yet.** This blocks Gate 03.

What exists (`tests/reference_cases/*.json`, 8 files, 21 cases):

| Element | Source | Status |
|---|---|---|
| Physical quantities: Lee (1982) arc-flash energy, power-law wind profile, Environment Canada Humidex via dew point, OSHA 29 CFR 1910.95 noise dose, ISO 2631-1 A(8) vibration | Hand calculations from the published formulas, made independently of `risk_engine.py` (`basis` field per case) | Independent of the engine, but **not reviewed by a qualified person** |
| Module bands (`risk_band`) and `safety_override` | MAKU's own thresholds | **Regression baselines only**, never presented as approved |
| Initial matrix score and band, residual score and band | Not in any approved standard; MAKU's methodology 2.0.0 (`docs/METHODOLOGY.md`) | **No approved expected value** |
| Reviewer, approval date, reference standard | `approved_expected` block per case (schema in each JSON file's `approval_schema`) | **Empty for all 21 cases** |

**Requested from the HSE reviewer:** for each case, the approved reference standard or matrix and its version, initial score and band, residual scenario (which controls), residual score and band, safety override, reviewer name and qualification, approval date, and case notes. They should be entered in `approved_expected`. `test_approved_expected_value[…]` then compares them exactly with no code change, and `scripts/audit_evidence.py reference-cases` reports PASS or FAIL per case.

**The approved formula is not assumed (A3).** MAKU's documented method is a 5×5 likelihood × severity product with bands Low 1–4, Moderate 5–9, High 10–15, Extreme 16–25. If the approved standard uses a lookup matrix or a different band table, the reviewer's values will expose the difference in exactly those tests.

---

## 4. Case-by-case actual scores and comparison results

All 21 cases were run twice each through the production entry point `maku_core.run_assessment` and produced identical output both times (deterministic).

- **Residual scenario:** every control MAKU recommends for that result is marked as applied, as written in each case's `residual_scenario`. The reviewer may replace this.
- **"Expected" columns:** MISSING for every case, because no approved values exist. Engine output was never copied into them.

| Case ID | Input hash | Actual initial (score, band) | Actual residual (score, band) | Module band | Override | Governing hazard | Determ. | Result |
|---|---|---|---|---|---|---|---|---|
| data_center:lee-480V-20kA-6cyc | 83c773b6af878b55 | 3 Low | 3 Low | MODERATE | no | Hot/cold-aisle thermal differential | YES | **BLOCKED** |
| data_center:lee-480V-50kA-30cyc | 5bb8fbb00db50b1e | 10 High | 5 Moderate | CRITICAL | no | Arc-flash incident energy | YES | **BLOCKED** |
| data_center:label-45cal-danger | 95fd3319527948bb | 25 Extreme | 5 Moderate | CRITICAL | yes | Arc-flash incident energy | YES | **BLOCKED** |
| data_center:unknown-ie | 32ca76c7ed409f59 | 25 Extreme | 5 Moderate | CRITICAL | yes | Confined ceiling-void + armed clean-agent suppression | YES | **BLOCKED** |
| high_rise:floor40-suburban | cd6b7e042b1d6f05 | 25 Extreme | 20 Extreme | CRITICAL | no | Crane-load oscillation index | YES | **BLOCKED** |
| high_rise:floor60-urban | 0914699f2e1e36b5 | 25 Extreme | 5 Moderate | CRITICAL | yes | Wind shear (crane gate) | YES | **BLOCKED** |
| high_rise:measured-overrides-model | 4c485800881a81d0 | 25 Extreme | 5 Moderate | CRITICAL | yes | Wind shear (crane gate) | YES | **BLOCKED** |
| marine_port:night-low-tide | 26dc7b31f36f18ff | 25 Extreme | 5 Moderate | CRITICAL | yes | Tide clearance margin | YES | **BLOCKED** |
| marine_port:day-safe | 62fd780159360589 | 2 Low | 2 Low | LOW | no | Splash-zone hardware corrosion capacity loss | YES | **BLOCKED** |
| mining_quarrying:noise-95dBA-8h | 4932abb03ba2499c | 25 Extreme | 5 Moderate | CRITICAL | yes | Noise dose | YES | **BLOCKED** |
| mining_quarrying:wbv-1.0-4h | 0d6a79ccae0ed1a2 | 8 Moderate | 4 Low | HIGH | no | Whole-body vibration A(8) | YES | **BLOCKED** |
| mining_quarrying:silica-over-oel | abc382aea92869ae | 25 Extreme | 5 Moderate | CRITICAL | yes | Respirable crystalline silica (RCS) | YES | **BLOCKED** |
| offshore:humidex-30C-70pct | d1e3a74decc0c589 | 25 Extreme | 5 Moderate | Extreme | yes | Humidex heat stress | YES | **BLOCKED** |
| offshore:humidex-35C-50pct | 4d776788fb2baec0 | 25 Extreme | 5 Moderate | Extreme | yes | Humidex heat stress | YES | **BLOCKED** |
| offshore:humidex-25C-80pct-gale | 33ac7ef1b4c274e2 | 25 Extreme | 5 Moderate | Moderate | yes | Wind (crane/lifting) | YES | **BLOCKED** |
| solar:hot-panels | 8f6b820cc13490f1 | 25 Extreme | 5 Moderate | Extreme | yes | Perceived thermal temperature (heat/UV amplification) | YES | **BLOCKED** |
| solar:mild-sand | 00610dd60e992004 | 1 Low | 1 Low | Low | no | Perceived thermal temperature (heat/UV amplification) | YES | **BLOCKED** |
| underground:co-over-oel | 49beee937a9cf36a | 25 Extreme | 5 Moderate | CRITICAL | yes | Trapped-heat / geothermal humidity (perceived temp) | YES | **BLOCKED** |
| underground:clean-cool | b9757ad20be3bc40 | 1 Low | 1 Low | LOW | no | Trapped-heat / geothermal humidity (perceived temp) | YES | **BLOCKED** |
| wind_energy:lightning-close | cd0dca7b60dcc58e | 25 Extreme | 5 Moderate | CRITICAL | yes | Lightning (30-30 rule) | YES | **BLOCKED** |
| wind_energy:calm-onshore | 7de038129fd27867 | 1 Low | 1 Low | LOW | no | Hub-height wind speed (fall-from-height access gate) | YES | **BLOCKED** |

**Summary: 0 PASS · 0 FAIL · 21 BLOCKED.** The full A7 table, including the independent field checks and the controls credited, is in `docs/audit/reference_case_comparison.csv`.

**What did verify** (`tests/test_gate03_golden.py`, all passing on SQLite and PostgreSQL):
- **Independent field values:** all 12 independently specified field values are inside their documented tolerance. Three of them are exact pass-throughs: the 45.0 cal/cm² label value, the 33.0 kn measured wind and the 140 m working height.
  - Lee: 2.37 vs 2.374 ±0.01; 29.68 vs 29.678 ±0.05.
  - Wind: 29.0 vs 29.02 ±0.05; 54.6 vs 54.62 ±0.05.
  - Noise dose: 200.0 vs 200.0 ±0.5. A(8): 0.707 vs 0.707 ±0.005.
  - Humidex: 40.9 vs 41.2, 45.0 vs 45.3 and 33.5 vs 33.7, each ±0.6 (see OPEN-04).
- **Matrix arithmetic:** for every hazard of every case, score = L × S. Each band matches the documented table, re-implemented independently in the test. The overall result equals the worst hazard.
- **Residual:** for every case, re-derived from the documented 2.0.0 rules by an independent oracle in the test. Severity is never reduced, residual ≤ initial, and computing residual leaves the initial result unchanged.
- **Boundaries (A4):** all 25 scores, each boundary ±1, no gaps or overlaps, invalid scores and axis values rejected, likelihood margin boundaries at 0 / 25 % / 60 % / 100 %.
- **Validation (A4):** every numeric input of every module at its minimum, its maximum and just outside both. NaN, infinity, strings, booleans and missing or `None` values are all rejected. Unknown country codes and unknown fields are rejected.
- **AI cannot override (A6):** a hostile AI reply ("risk_band=Low; safety_override=false") leaves the result byte-identical. A structural test shows no scoring module imports `ai_advisor`.
- **Database round trip (A6):** all 21 cases are stored and read back with the same band, override and key metric. The PDF report displays the computed band and the methodology version.

**Observations the reviewer must rule on.** These are not changed by me, because changing them would mean inventing thresholds:

| Ref | Case(s) | Observation |
|---|---|---|
| OPEN-02a | data_center:lee-480V-20kA-6cyc | The module band (MODERATE) and the matrix band (Low, 3) disagree. Two classifications are shown for one result. |
| OPEN-02b | data_center:lee-480V-50kA-30cyc | Module CRITICAL, matrix High (10), **no safety override** at 29.7 cal/cm². |
| OPEN-02c | mining_quarrying:wbv-1.0-4h | Module HIGH, matrix Moderate (8). |
| OPEN-02d | offshore:humidex-25C-80pct-gale | Module band Moderate (the Humidex band only), but override = yes and matrix Extreme (wind governs). The headline band understates the governing hazard. |
| OPEN-02e | high_rise:floor40-suburban | Module CRITICAL, matrix Extreme 25, **no safety override**. Residual stays Extreme (20) because no recommended control addresses the oscillation hazard. |
| OPEN-02f | underground:co-over-oel | CO is over the occupational exposure limit, but ties are broken by list order, so the governing hazard shown is "trapped heat". The tie-break rule needs approval. |
| OPEN-03 | All severity-5 cases | The "all recommended" residual scenario includes elimination controls (stop work), which set likelihood to 1, so residual shows Moderate (5). The reviewer must confirm whether this residual scenario and convention are acceptable. |
| OPEN-04 | offshore humidex cases | The engine's relative-humidity form differs from the dew-point hand calculation by up to 0.3 Humidex units, inside the ±0.6 tolerance. The reviewer must approve the formula and the tolerance, so the tolerance cannot hide a formula difference. |

---

## 5. Defects found and code changes made — remediation register

Each defect is closed only with a regression test that reproduced the original failure condition. Severity reflects actual impact.

| ID | Severity | Component | Root cause | Fix | Regression test | Status |
|---|---|---|---|---|---|---|
| AUD-01 | High | `analytics.py` (C3) | Outside production, a database failure silently switched to an **in-memory session log** (`session_state`) | Every environment now fails closed. The in-memory store is removed and `_handle_db_failure` always freezes the database layer. | `test_gate03_golden.py::TestAuditRegressions::test_R5…`, `test_app.py::TestDatabaseFailSafe` | Fixed |
| AUD-02 | High | `analytics.log_assessment`, `app.save_assessment` (C3) | In the fatal state the write silently returned, and the page carried on as though it had been saved | `PersistenceError` on every failed write and read. The page shows "Assessment NOT saved" or the CRITICAL banner. CSV import is a single transaction. | `test_database_guard.py::…writes_nothing`, `test_app.py::…no_silent_redirect…`, browser outage check | Fixed |
| AUD-03 | High | `analytics.require_scope`, `set_org_context`, `app.can_save_assessments` (B3) | **Fail-open:** with the database disabled, tenant checks were skipped and an unchecked context was returned | No access decision without the database (`PersistenceError`). Saving is refused. | `TestAuditRegressions::test_R3…` | Fixed |
| AUD-04 | High | Database layer (B3) | No database-level tenant isolation: one role owned the tables and every query relied on Python filters | Migration 0003: RLS on 7 organization-owned tables, identity from the server-side session, a separate `maku_app` role, and start-up refusal when connected as owner, superuser or BYPASSRLS. | `test_tenant_isolation_matrix.py::TestDatabaseRowLevelSecurity` (30 tests), `test_database_guard.py::TestPostgresProduction` | Fixed |
| AUD-05 | Medium | `audit_log` (B6/C4) | The application role could `UPDATE`, `DELETE` and `TRUNCATE` the hash-chained ledger | Those privileges are revoked from `maku_app` (append-only). The owner keeps them. | `…::test_audit_log_is_append_only_for_the_application` | Fixed |
| AUD-06 | Medium | Sessions (B4/B5) | Password change, account deletion, deactivation or role change did not end other live sessions until the idle or absolute timeout | Every request re-checks the account and a fingerprint of the stored hash. Revoked sessions are signed out and audited (`SESSION_REVOKED`). | `test_passwords.py::TestSessionRevocation` (6 tests) | Fixed |
| AUD-07 | Medium | `risk_matrix.py` (A4) | Invalid likelihood or severity was silently **clamped or truncated** (0→1, 7→5, 2.9→2) | Values outside 1–5, non-integers and booleans are rejected. Scores outside 1–25 are rejected. | `TestBandBoundaries`, `test_app.py::…rejects_out_of_range_inputs` | Fixed |
| AUD-08 | Medium | `risk_matrix.py` (A5) | An unknown band label became severity 3. An empty hazard list reported **"Low", score 0**. | Both now raise `ValueError`. Residual with no matrix raises. | `TestBandBoundaries::test_unknown_band_label…`, `::test_no_hazard_is_not_low_risk`, `TestResidualRules::test_residual_without_a_risk_matrix…` | Fixed |
| AUD-09 | Medium | `analytics._get_or_create_id` | A failed insert returned a **made-up id 0**. On PostgreSQL it also aborted the transaction. | Savepoint. The real error is re-raised. | `TestAuditRegressions::test_R1…` | Fixed |
| AUD-10 | Medium | `analytics.verify_audit_log_integrity` | An unreadable ledger was reported as `ok: True` | Now returns `ok: False` with an `error` key | `TestAuditRegressions::test_R2…` | Fixed |
| AUD-11 | Medium | `analytics.log_site_alert` (C3) | A failed safety-alert write was silent | Returns `False` and logs CRITICAL. The page says "Alert shown but NOT recorded". | `TestAuditRegressions::test_R4…` | Fixed |
| AUD-12 | Low | `risk_matrix.likelihood_from_margin` | NaN read as "rare" (1). Inputs were already validated upstream, so this was not reachable from the pages. | Non-finite or invalid values are rejected | `TestLikelihoodBoundaries::test_invalid_inputs…` | Fixed |
| AUD-13 | Low | Database layer | The organization of a stored row could be changed by `UPDATE` | Trigger `keep_organization` on 5 tables, which applies to the platform admin too | `…::test_ownership_update` | Fixed |
| AUD-14 | Medium | `data_feeds.client_ip_from_headers` (C1) | Header text went **unvalidated** into the ipapi.co URL path and the per-IP login-lockout key | Only valid IP addresses are accepted. In the Docker stack, Caddy overwrites `X-Forwarded-For`. | `TestClientIpValidation` (7 cases) | Fixed |
| AUD-15 | Low | `analytics.get_log_dataframe` | Returned an empty result before the access check when the session had no log yet. Nothing was disclosed, but the order was wrong. | Access is checked first | `…::test_cross_tenant_read_with_tampered_session_context` | Fixed |
| AUD-16 | Low | `push.py` | The worker thread had no identity, so RLS would hide tokens and alerts would silently not be sent | The thread runs as the user who raised the alert (`acting_as`). Token release goes through `maku_release_device_token`. | `test_tenancy.py::TestPushIsolation`, `…::test_release_token_requires_identity` | Fixed |
| OPEN-01 | **High (gate)** | Gate 03 | No independently approved expected values (A1) | **Needs a qualified HSE reviewer** | `test_approved_expected_value[*]` (21 BLOCKED) | **Open** |
| OPEN-02 | **High (gate)** | Methodology (A4) | Module band vs matrix band contradictions, overrides and tie-break (table in item 4) | **Needs a methodology decision by the reviewer**; then code and tests follow | — | **Open** |
| OPEN-03, OPEN-04 | Medium | Methodology (A5, A3) | Residual scenario and convention; Humidex formula and tolerance | Reviewer approval | — | **Open** |
| OPEN-05 | **High (gate)** | Security gate | No external penetration test | Commission an independent tester | — | **Open** |
| OPEN-06 | Low | Accounts | There is **no password recovery or reset flow** (no reset tokens). An administrator must delete and recreate the account. Reset-token criteria in B4 are therefore not applicable. | Product decision | — | Open (accepted risk pending decision) |
| OPEN-07 | Low | RLS scope | `users`, `login_attempts`, `user_consents` and `account_deletions` are not tenant-owned and not RLS-protected. They are protected by application admin checks. The platform-admin flag is asserted by the application server, so RLS protects against query mistakes and IDOR, **not against a compromised application server**. | Documented; pen-test scope | — | Open (by design) |
| OPEN-08 | Low | GDPR access | After their membership is removed, a user cannot export their own past assessments for that organization (RLS); an administrator must do it | Product decision | — | Open |
| OPEN-09 | Info | Rate limiting | Brute-force lockout exists for sign-in (per user and per IP). There is no general request rate limit at the proxy. | Pen-test scope, then Caddy rate limiting if required | — | Open |

**Supporting files changed:**
- `migrations/versions/0003_row_level_security.py` (new)
- `scripts/init_db.py`: owner and application roles, grants
- `docker-compose.yml`, `.env.example`, `docs/DEPLOYMENT.md`: `MAKU_APP_DB_PASSWORD` and `MIGRATION_DATABASE_URL`
- `tenancy.py`: admin actions run as the acting principal
- `manage_users.py`, `scripts/audit_credentials.py`, `scripts/migrate_sqlite_to_postgres.py`: run under `system_context()`
- `scripts/audit_evidence.py` (new)
- `requirements-dev.txt`: adds `pypdf==5.9.0` for report-display tests

---

## 6. Tenant-isolation test results (C5, B2, B3)

**Method.** Two synthetic organizations, each with one assessment, one project and site, one site alert and one registered device:
- **Org A:** `alice` (supervisor), `ada` (viewer), `amy` (org_admin).
- **Org B:** `bob` (supervisor).

Each matrix row is run at two layers:
- **Application layer:** the functions the pages call, with a real signed-in session, on SQLite and on PostgreSQL.
- **Database layer:** raw SQL sent as the `maku_app` role with alice's identity, which **bypasses every Python check**, on PostgreSQL. This shows RLS holds on its own.

| Test | Required result | Application layer (SQLite / PostgreSQL) | Database layer, RLS (PostgreSQL) |
|---|---|---|---|
| Read own record | Allowed according to role | PASS / PASS (supervisor and viewer read A's rows) | PASS: all 7 tenant tables return A's rows |
| Cross-tenant read | No data disclosure | PASS / PASS: selecting B by id or by name is denied and audited; a tampered session context is re-checked on every read | PASS: `WHERE organization_id = <B>` returns 0 rows on all 7 tables, though the owner sees B's rows |
| Spoof tenant ID on create | Rejected or safely constrained | PASS / PASS: an organization override raises; CSV import is forced into A; device registration for B is denied | PASS: inserts with B's id are rejected (`42501`) on assessments, projects, alerts, device tokens and memberships; creating an organization is rejected |
| Spoof author | Rejected | — | PASS: an assessment with `username='bob'` is rejected |
| Ownership update | Ownership cannot be transferred | PASS / PASS: no function moves records; membership changes move nothing | PASS: members' `UPDATE` affects 0 rows (records are immutable); the platform admin's change of `organization_id` is rejected by the trigger |
| Cross-tenant delete | No unauthorized side effect | PASS / PASS: CSV merge deletes only the session's own rows in A | PASS: `DELETE … WHERE organization_id = <B>` affects 0 rows on 5 tables; B's row still exists (owner check) |
| Export / download | No unauthorized disclosure | PASS / PASS: the Excel export contains no B data; the all-organizations alert view is denied; push tokens are org-scoped | (covered by cross-tenant read) |
| Membership revoked | Denied according to session design | PASS / PASS: the **next request** of the same session is denied | PASS: 0 rows visible immediately |
| Insufficient role | Denied | PASS / PASS: a viewer cannot write | PASS: a viewer cannot insert; an org_admin cannot appoint an org_admin |
| Unauthenticated / no identity | No access | PASS / PASS | PASS: 0 rows on all 7 tables |
| Privilege escalation | Denied | PASS / PASS: an org_admin cannot manage B, appoint an org_admin or create an organization | PASS: the app role is not superuser or BYPASSRLS; `row_security=off` and `DISABLE ROW LEVEL SECURITY` are refused |
| Audit ledger tampering | Denied | — | PASS: `UPDATE`, `DELETE` and `TRUNCATE audit_log` are refused (`42501`) |
| Device-token takeover | Denied | — | PASS: anonymous `maku_release_device_token` is refused |

**54 matrix rows, 0 failures** (`docs/audit/tenant_isolation_matrix.csv`). The existing suite `tests/test_tenancy.py` (24 tests) also passes on both backends.

**Tenant ownership is derived from trusted records, never from client input.**
- The organization comes from `organization_members`, keyed by the server-side session username set by `auth.require_login()` after verifying credentials.
- The browser can only choose among organizations it is a member of. `require_scope` re-checks membership in the database on every call.
- On PostgreSQL, the identity reaches the database as transaction-local settings, and the policies look up the role through `maku_org_role()`. No policy reads an organization id supplied by a request.

**Elevated paths, reviewed separately (B3).**
- The four `SECURITY DEFINER` functions (`maku_org_role`, `maku_can`, `maku_project_org`, `maku_release_device_token`) have a fixed `search_path`. Each reads or deletes only rows keyed to the caller's own identity or the given token.
- `maku_release_device_token` requires a signed-in caller and has `EXECUTE` revoked from `PUBLIC`.
- Operator CLIs run as `system` (platform admin) and only from a shell on the server.
- Migrations run as the owner.

**Not covered** (no such feature exists in MAKU): stored attachments or files, signed URLs, storage buckets, background jobs that read tenant data other than push, views, and RPCs exposed to clients.

---

## 7. Password storage and authentication findings (B4, B5, B6)

Passwords are stored by **MAKU's own code**, not Supabase Auth.

| Check | Finding | Evidence |
|---|---|---|
| Algorithm | **Argon2id**, RFC 9106 low-memory profile (t=3, m=64 MiB, p=4), unique salt per hash, stored as `argon2:$argon2id$v=19$m=65536,t=3,p=4$…` | `test_passwords.py::TestHashing` |
| Every write path | `create_user`, `change_password` and `upgrade_stored_hash` all call `hash_password` (Argon2id). These are the only three `password_hash` writes in the codebase. | `TestNoFastHashes::test_every_write_path_stores_argon2id` |
| Legacy hashes | bcrypt is still accepted and upgraded to Argon2id at the next successful sign-in. A failed sign-in does not upgrade. | `TestUpgradeOnSignIn` |
| Plaintext, SHA-256, MD5, base64 | **Never verify**; rejected through `verify_password` itself. Deployment accounts in those formats are refused and audited. | `TestNoFastHashes::test_weak_formats_never_verify`, `TestHashing::test_anything_else_fails_closed`, `scripts/audit_credentials.py` |
| Length | Maximum 256 characters. Passwords over 72 bytes work and are not silently truncated. | `TestHashing` |
| Policy | At least 12 characters and 3 of 4 character classes. In production, a deployment account below policy is refused at sign-in. | `TestDeploymentAccounts` |
| Brute force | Server-side lockout: 5 failures per user, 20 per IP, within a rolling window. Equal timing for unknown users (decoy Argon2 hash). | Existing `test_app.py` lockout tests |
| Sessions | Idle timeout 30 min, absolute timeout 8 h. **New:** revoked on the next request after a password change, deletion, deactivation, role change or deployment credential rotation (AUD-06). | `TestSessions`, `TestSessionRevocation` |
| Tokens and JWTs | **Not applicable.** MAKU issues no JWTs and no bearer tokens. The session is server-side Streamlit state tied to the WebSocket connection. Forged, expired or tampered-token tests do not apply. The pen test should still try session fixation and WebSocket hijacking. | — |
| Recovery and reset | **No reset flow exists** (OPEN-06) | — |
| Secrets in the repository and history | None. `.gitignore` covers `.env`, `secrets.toml`, keys and keystores; all history checked (item 1). The FCM service account and AI key are server-side only. **No Supabase service-role key exists.** | `git log --all -- 'secrets/*' '*.db' '.streamlit/secrets.toml'` |
| Redaction | Database URLs are redacted in logs. Init and migration errors never print URLs. Tests assert no password appears in output. | `test_database_guard.py::…without_leaking_password`, `…never_contains_the_password` |

**Operational note, outside the code.** Several plaintext passwords for the owner's personal accounts were typed into the development chat. They should be rotated before launch, and the production `MAKU_AUTH_USERS` hash should be generated from a new password.

---

## 8. Database RLS, fallback and mock-data findings (B3, B6, C3)

**Supabase RLS.** Not applicable, because MAKU does not use Supabase. The equivalent controls are in PostgreSQL itself.

**PostgreSQL row-level security** (`migrations/versions/0003_row_level_security.py`):

| Table | SELECT | INSERT | UPDATE | DELETE |
|---|---|---|---|---|
| organizations | member (read) | platform admin | platform admin | platform admin |
| organization_members | own rows, org_admin of that org, platform admin | org_admin (not as org_admin), platform admin | same | org_admin, own row (erasure), platform admin |
| projects | read | write | manage | manage |
| sites | read (through the project's organization) | write | manage | manage |
| assessment_log | read | write **and** `username` = caller | platform admin only (records immutable) | manage, own rows, platform admin |
| site_alert_log | read (NULL organization: platform admin only) | signed-in caller with read, or NULL organization | platform admin | platform admin |
| device_tokens | own, read in that org, platform admin | own token in an org the caller can read | own | own, platform admin |
| audit_log | no RLS: app role may `SELECT` and `INSERT` only | — | revoked | revoked (also `TRUNCATE`) |

- **Grants:** least privilege for `maku_app` (`grant_statements`); `TRUNCATE` is revoked on all tables. No views and no client-callable RPCs exist.
- **Trigger:** `keep_organization` makes ownership immutable.
- **Owner and RLS bypass:** the start-up check `verify_rls_enforced` refuses a role that is superuser, BYPASSRLS, the table owner, or connected to a database where RLS is off. The tests cover this (`test_runtime_refuses_the_owner_role_too`, `test_production_refuses_to_connect_as_the_table_owner`).
- **SQLite (development only):** has no RLS; application-layer checks only.

**Database fallback (C3): fixed, every environment fails closed.**
- No silent switch to SQLite: production and staging refuse a missing or non-PostgreSQL `DATABASE_URL` at start-up (exit code 2) and at runtime.
- No in-memory store anywhere (AUD-01).
- Failed writes raise and are shown as **NOT saved** (AUD-02). Failed reads raise; they are never shown as an empty history.
- CSV import is one transaction, so the delete and insert are rolled back together.
- An unreadable audit ledger is reported as not verified (AUD-10).
- Recovery happens only when the **same** configured database answers again (`probe_database`).

**Mock and demo data (C3).**
- Simulators and mock fallbacks run only with `MAKU_DEMO_MODE=1`, which is off in `.env.example` and in production.
- Simulated inputs carry `data_provenance = "SIMULATED"`, show red **SIMULATED DATA** banners, and are never pushed as stop-work alerts.
- The mock IP geolocation is labelled "Mock fallback data".
- AI text is labelled as a narrative and never changes a result (item 4).

**Injection (C1).**
- All values are bound parameters.
- Bandit's 12 "string-built SQL" (B608) hits were reviewed one by one. Every interpolated part is a table or column name from code constants; no request value is interpolated. These are false positives.
- The other Bandit items were also reviewed:
  - B113: a timeout is present (20 or 40 s).
  - B310: healthcheck to a fixed localhost URL.
  - B314: the evidence script parses its own JUnit file.
- 0 high-severity findings. `pip-audit`: no known vulnerable dependency.

---

## 9. External penetration-test status

**Not performed. No report exists.** I have not carried out, and do not claim, an external penetration test. The automated and internal reviews above do not substitute for it (D3).

**Suggested scope for the independent tester:**
- The deployed Docker stack (Caddy, Streamlit, PostgreSQL) in an isolated staging environment with `MAKU_ENV=staging` and synthetic data, under written authorization.
- Streamlit WebSocket session handling: fixation, hijacking, cross-site WebSocket.
- Authentication and lockout bypass.
- BOLA and IDOR across Org A and B through the real UI and WebSocket messages.
- File upload: CSV parsing, size limits, formula injection in exported CSV and Excel.
- XSS in report and HTML rendering.
- Header and CSP configuration.
- Rate limiting and resource exhaustion (OPEN-09).
- The mobile shells (`capacitor://localhost` framing, deep links).
- OWASP API Top 10 mapping.

---

## 10. Outstanding blockers and evidence still required

1. **Approved reference set (Gate 03).** A qualified, independent HSE reviewer must:
   - provide the approved reference standard and version;
   - fill `approved_expected` for all 21 cases, including the residual scenario;
   - sign off reviewer, qualification and date.
   Then re-run `python -m pytest tests/test_gate03_golden.py` and `python scripts/audit_evidence.py reference-cases`, which exits 0 only when all 21 PASS.
2. **Methodology rulings (Gate 03):** OPEN-02 (band contradictions, overrides, tie-break), OPEN-03 (residual convention) and OPEN-04 (Humidex formula and tolerance). Any change to thresholds is then a methodology version bump, with new tests.
3. **External penetration test (Security gate):** authorization letter, tester report, remediation of every critical or high finding, and independent retest evidence.
4. **Product decisions:** OPEN-06 (password recovery), OPEN-08 (removed member's data access), OPEN-09 (rate limiting).
5. **Credential rotation:** rotate the passwords shared during development (item 7) before production.
6. **Production rehearsal:** the Docker image build and full `docker compose up` on the target server were not run in this environment. The Oracle Cloud server is not provisioned yet because of capacity in the Dubai region. Re-run commands 2–4 of item 1 against the staging stack.

---

## 11. Final gate decision

| Gate | Requirement | Status | Evidence, defects, reviewer |
|---|---|---|---|
| **Gate 03** — HSE reference cases | All 21 approved cases plus boundary and regression tests pass with no unexplained discrepancy | **BLOCKED** | Determinism, independent physics fields, matrix and residual arithmetic, boundaries, validation, AI-override and round-trip tests: **all pass** (`tests/test_gate03_golden.py`, 235 passed on SQLite, 234 on PostgreSQL).<br>**But 0 of 21 cases have approved expected values** (OPEN-01), and classification contradictions await a ruling (OPEN-02). Reviewer: *none yet*. |
| **Security** — external penetration test | External test complete; critical and high findings fixed and independently retested; tenant isolation and authentication pass | **BLOCKED** | Internal: tenant-isolation matrix 54/54 PASS at the application and database (RLS) layers; authentication review in item 7; 16 internal defects fixed with regression tests (item 5).<br>**No external test has been performed** (OPEN-05). Tester: *none yet*. |

*Neither gate may be marked PASS on the basis of this document. Both need the independent evidence listed in item 10.*
