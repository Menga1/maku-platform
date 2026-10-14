# MAKU remediation roadmap

Response to the *Pre-Launch Technical & Product Review* (14 October 2026). Each finding in the review was checked against the code in this repository. This file records what was found, the fix, and the gate that must pass before release.

**Overall position:** MAKU is not released to the public stores until release gates 01–05 pass. Gate 06 is the controlled pilot.

Status legend: ✅ done and tested · 🔧 in progress (pull request open) · ⏳ planned · 🔍 needs an external party

---

## 1. Findings verified against the code

| # | Priority | Review finding | What the code actually does (verified 14 Oct 2026) | Fix | Status |
|---|---|---|---|---|---|
| F1 | P0 | Silent fallback from PostgreSQL to SQLite | If `DATABASE_URL` points to PostgreSQL and the database fails, writes freeze and a banner appears; no fallback. **But** if `DATABASE_URL` is missing or not PostgreSQL, the app silently uses a local SQLite file, and nothing marks a deployment as "production". After a failure, only the Dashboard shows the error; module pages still run assessments that are not saved. The failure is not written to the server log as an error. Schema changes are ad-hoc `ALTER`s. The Docker health check ignores the database. | `MAKU_ENV=production` requires a PostgreSQL URL and refuses to start without one. Every page stops with an explicit error when the database is down. `logger.critical` on failure. Health check pings the database. Versioned migrations. | 🔧 PR 2 |
| F2 | P0 | Tenant and project isolation | **Not enforced.** The organization picker lists every organization in the database and lets any signed-in user select one or create one. Site alerts are filtered by the organization *name* the user picked. No user↔organization link exists. CSV import takes the organization from the file. Phones register for push alerts under the picked organization. All deployment-configured accounts are global admins. | `organization_members` table; organization context resolved on the server from membership; one access check (`tenancy.py`) on every read and write; `organization_id` stored and filtered on every record; CSV import and push registration forced to the user's own organization; platform-admin and organization roles split; cross-tenant tests. | 🔧 PR 3 |
| F3 | P0 | SHA-256 passwords, sessions, secrets | Passwords are **bcrypt only**; SHA-256 and plain text are rejected at login. No SHA-256 hashes exist in the database. Lockout per user (5/15 min) and per IP (20) is stored in the database. Secrets (AI key, database URL) stay on the server. **Gaps:** passwords over 72 bytes crash account creation; deployment-configured accounts skip the 12-character rule and are always admin; sessions have an 8-hour absolute limit but no idle timeout. | Argon2id for new hashes; bcrypt still verified and upgraded automatically at next login; 72-byte bug fixed; idle timeout; deployment accounts checked against the password policy; `scripts/audit_credentials.py`. | 🔧 PR 4 |
| F4 | P0 | Risk engine credibility | `risk_engine.py`, `risk_matrix.py` and `regulatory_*.py` do not depend on Streamlit. **But** the safety-control rules live in `ai_advisor.py` (Streamlit-dependent), each of the 8 pages repeats the assessment pipeline, results carry no methodology version, and there is no reference-case set. **Methodology defect:** residual risk lowers the governing hazard's likelihood by 1 for *every* ticked control, whether or not that control addresses that hazard. | `maku_core/` service layer: typed inputs, a single `run_assessment()`, controls tagged with the hazard they address and their level in the hierarchy of controls, residual risk credited only for relevant controls, `METHODOLOGY_VERSION` stamped on every result, `tests/reference_cases/` for independent review. | 🔧 PR 5 |
| F5 | P1 | Mock data presented as live | Already fixed: simulators only run with `MAKU_DEMO_MODE=1`; every payload carries `is_live`; simulated values show a red **SIMULATED DATA** banner and are stamped on reports; AI failures are never cached or shown as content. | Keep; add a "cached / stale" label when a live feed is older than its update interval. | ✅ / ⏳ |
| F6 | P1 | Regulatory source traceability | `regulatory_references.py` lists sources with URLs; jurisdiction profiles carry an effective date. No per-reference verification status or reviewer record. | Add `verified_on`, `verified_by` and `status` to each reference; show them in reports. | ⏳ Phase 2 |
| F7 | P1 | Privacy and sensitive HSE records | Consent screen (GDPR / UAE PDPL), data export and in-app account deletion are implemented. Site photos are embedded in reports. No retention period is defined. | Define retention per record type; scheduled purge; access log for report downloads. | ⏳ Phase 1 / 5 |
| F8 | P1 | Mobile usability and packaging | Capacitor shell adds native GPS, camera, push, share and an offline view; CI builds both stores. Not yet tested on real devices. | Real-device test matrix (Phase 3). | ⏳ Phase 3 |
| F9 | P1 | Monitoring and recovery | Nightly database backups in Docker; Caddy and container health checks. No error monitoring, no tested restore, no rollback procedure. | Error monitoring; quarterly restore drill; documented rollback. | ⏳ Phase 4 / 5 |
| F10 | P1 | Store listing accuracy (found during this review) | The marketing illustrations mention capabilities MAKU does not have today: virtual GIS buoys, 3D BIM twins, satellite albedo data, rack-level IoT sensors, and "correlates electrical load" for arc flash (MAKU deliberately never uses load to estimate arc-flash energy). | Use these images in the app only; store screenshots and descriptions must describe what the app actually does. Edit the artwork text before using it in a store listing. | ⏳ Phase 5 |

---

## 2. Phases and release gates

### Phase 1 — Secure the foundation · **Release blocker**

| Work item | Finding | Exit criterion |
|---|---|---|
| Production mode refuses SQLite and refuses to start without PostgreSQL | F1 | Starting with `MAKU_ENV=production` and no PostgreSQL URL exits with a logged error |
| Every page stops with an explicit error when the database is unavailable | F1 | Test: simulated outage → no page accepts an assessment |
| Versioned migrations (Alembic) with a baseline of the current schema | F1 | `alembic upgrade head` on an empty and on a pre-existing database gives the same schema |
| Backup **restore** tested | F1 | Restore of last night's backup into a scratch database, checked row counts and audit-chain integrity |
| Organization membership and server-side access checks on every read/write | F2 | Cross-tenant test suite passes (see Gate 01) |
| Argon2id, automatic upgrade of bcrypt hashes, 72-byte fix, idle timeout | F3 | Unit tests; no deployment account fails the password audit |
| Review of uploads, downloads, injection, secrets and error messages | — | Checklist in §4 completed; no raw exception text shown to users |

### Phase 2 — Validate HSE intelligence · **Release blocker**

| Work item | Finding | Exit criterion |
|---|---|---|
| Service layer `maku_core.run_assessment()` used by every page | F4 | The 8 pages contain no assessment logic of their own |
| Residual risk credited only for controls that address the governing hazard | F4 | Test: an unrelated control does not change residual risk |
| Reference cases for each module, reviewed by a competent HSE professional | F4 | ≥ 5 cases per module signed off; all pass in CI |
| `METHODOLOGY_VERSION` on every result and report | F4 | Reports show the version; changing a formula requires bumping it |
| Units, timestamps, coverage, stale and missing data for every live feed | F5 | Each feed has a test for missing and stale data |
| Regulatory references verified against official sources, with date and status | F6 | Every reference has `verified_on` and `status` |
| AI briefings separate facts, assumptions and recommendations; critical decisions need human approval | — | Stop-work results cannot be dismissed without a named approver |

### Phase 3 — Prepare the mobile experience · Product readiness

Real-device testing (at least two Android and two iOS sizes) of forms, maps, tables, charts and PDF reports. Clear loading, empty, error, session-expired and offline states. Decision on the long-term frontend (current Capacitor shell versus Flutter / React Native on top of the `maku_core` API).

### Phase 4 — Test the whole system · Quality assurance

Unit, integration, security and end-to-end tests in a staging environment that mirrors production. Concurrent users, unavailable APIs, database failure, expired sessions and recovery. Penetration test by an external party (🔍). User acceptance testing with practising HSE professionals.

### Phase 5 — Controlled release · Launch readiness

Privacy policy published; store data-safety and privacy answers match actual collection (location, photos, push token, AI processing by Anthropic). Account deletion (done) and retention workflow. Store assets that match the real feature set (F10). Reviewer test accounts. Error monitoring, release signing (done in CI), versioning (automatic in CI), backups and rollback procedure.

### Release gates

| Gate | Passes when | Evidence |
|---|---|---|
| **01 Security** | No known critical or high vulnerability open; authentication and tenant isolation verified | Cross-tenant test suite green; credential audit clean; external penetration test report (🔍) |
| **02 Data integrity** | No silent production database substitution; migrations, persistence, backup restore and recovery tested | Production-mode start-up test; migration test; restore drill log |
| **03 HSE validation** | Risk logic independently validated; safety-critical outputs traceable and reviewed | Signed-off reference cases; methodology version on reports; reviewer's statement (🔍) |
| **04 Mobile QA** | Core workflows pass on representative Android and iOS devices | Device test matrix with results |
| **05 Store compliance** | Privacy, deletion, metadata, permissions and store-specific requirements checked | Completed store checklists; data-safety form matches §1 F7; listing matches F10 |
| **06 Controlled launch** | Pilot users complete real workflows; material feedback resolved; monitoring operational | Pilot report; monitoring dashboard live |

---

## 3. Decisions taken (14 October 2026)

| Decision | Choice | Reason |
|---|---|---|
| Users per organization | A user can belong to several organizations; each membership has its own role | Consultants and contractors work for several clients |
| Records saved before isolation existed | Attached to the organization with the same name; "Default organization" records go to the owner's organization | Keeps history without guessing |
| Password hashing | Argon2id for new passwords; bcrypt still accepted and upgraded at next login | Review recommends Argon2id; no forced resets |
| Streamlit Community Cloud copy | Kept as a labelled **demo** (`MAKU_ENV=demo`, local storage, "data not kept" banner) | Useful for demos; the production server runs in strict mode |
| Delivery | One pull request per area, merged by the owner | Each change reviewable on its own |

## 4. Phase 1 security checklist (beyond F1–F3)

- [ ] File uploads: CSV import size and type limits; photos limited to 6 per report and re-encoded
- [ ] Report downloads scoped to the user's organization
- [ ] All SQL parameterized (no string formatting with user input)
- [ ] No raw exception text shown to users (`showErrorDetails = "none"` is set; check custom messages)
- [ ] Dependency audit (`pip-audit`, `npm audit`) clean or each finding justified
- [ ] Secrets only in server environment / secret stores; none in the repository or the mobile app

## 5. Not covered here

External penetration testing, independent engineering validation of the formulas, and legal review of the privacy policy require outside specialists. Budget them separately, as the review notes.
