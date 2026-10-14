# MAKU — Multi-Environment AI for Kinetic Risk Assessment

Occupational health & safety (HSE) decision support for construction and MEP crews in eight environments:
Solar (desert), Offshore, Underground/tunnels, High-rise, Data centres, Wind energy, Mining & quarrying, and
Marine & port construction. Every risk number comes from a transparent, cited formula (`risk_engine.py`); the
optional AI layer only writes the briefing around those numbers.

> MAKU is decision support. It does not replace a competent person, a permit-to-work system, an IEEE 1584
> arc-flash study, or a certified engineering assessment.

## Run it

**Production** (Docker, PostgreSQL, automatic HTTPS): follow [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

**Developer laptop**

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python manage_users.py create dev.admin --role admin     # local SQLite account
streamlit run app.py
python -m pytest -q test_app.py tests/                    # full suite
MAKU_TEST_PG_URL=postgresql://... python -m pytest -q tests/   # + PostgreSQL integration tests
```

`MAKU_DEMO_MODE=1 streamlit run app.py` enables the sensor simulators (every simulated value carries a red
**SIMULATED DATA** banner).

## Repository map

| Path | Purpose |
|---|---|
| `app.py` | Streamlit entry point: login gate, privacy gate, navigation, the eight module pages |
| `risk_engine.py` | All risk maths - pure functions, no Streamlit |
| `ai_advisor.py` | Rule-based controls + optional Claude briefing (successes cached per API key; failures never cached) |
| `data_feeds.py` | Live feeds (Open-Meteo, Nominatim, ipapi.co); every payload tagged `is_live`; mocks only in demo mode |
| `auth.py`, `accounts.py` | bcrypt-only login, database-backed lockout, roles, consent, data export, account deletion |
| `tenancy.py` | Tenant isolation: organization membership and the server-side access check on every read and write |
| `analytics.py`, `db.py` | Assessment/alert/audit logs on pooled SQLAlchemy engines; `MAKU_ENV=production` makes PostgreSQL mandatory |
| `alembic.ini`, `migrations/` | Versioned database migrations, applied by `scripts/init_db.py` at start-up |
| `mobile_bridge.py`, `push.py` | Bridge to the native shell (GPS, camera, share, offline cache) and FCM stop-work alerts |
| `ui_helpers.py`, `i18n.py` | Shared widgets, PDF/HTML reports, 14-language UI strings |
| `regulatory_*.py` | Country threshold profiles and the verified citation list |
| `manage_users.py` | Account administration CLI |
| `scripts/migrate_sqlite_to_postgres.py` | One-time data migration with audit-chain verification |
| `Dockerfile`, `docker-compose.yml`, `deploy/` | Production stack: app, PostgreSQL, Caddy (TLS), nightly backups, legal pages, store verification files |
| `mobile/` | Capacitor 8 shell for iOS and Android |
| `mobile/fastlane/`, `.github/workflows/deploy.yml` | Automatic uploads to Google Play internal testing and TestFlight ([`docs/MOBILE_CI.md`](docs/MOBILE_CI.md)) |

## Engineering basis of the core formulas

| Module | Formula | Status |
|---|---|---|
| High-rise wind | `V(z) = V10 × (z / 10 m)^α`, α by terrain (ASCE 7 Exposure D/C/B: 0.11/0.15/0.25; dense city 0.33); a measured working-height reading overrides the model | Adapted (atmospheric power law) |
| Data-centre arc flash | Equipment label value → Lee `IE = 5.12×10⁵ · V · I · t / D²` cal/cm² → otherwise **unknown, study required** (load in kW is never used) | Label / Lee screening (not IEEE 1584) |
| Offshore / underground heat | Environment Canada Humidex | Direct implementation |
| Heat stress | WBGT approximation + ACGIH TLV work/rest tables | Adapted |
| Solar | Perceived temperature `Ta + GHI·albedo/100 + 0.5·UV` | MAKU screening index, cross-checked against WBGT |

The full table, with caveats, is `regulatory_references.FORMULA_STANDARDS_MAP` and is shown in the app.

## Production hardening in this release

- Corrected the Lee arc-flash constant (the previous value under-reported incident energy ~239×), removed the
  load-based arc-flash estimate, and replaced the exponential wind curve with the power law.
- No silent mock data: failed feeds fall back to manual entry; simulated values are bannered, logged and
  stamped on reports as SIMULATED.
- AI failures (429/timeout/network) are never cached and never shown as raw exceptions.
- bcrypt-only credentials, server-side lockout per user and per IP, roles, GDPR/UAE PDPL consent, data export
  and in-app account deletion.
- PostgreSQL support fixed (the previous code aborted every Postgres transaction), connection pooling,
  one-time schema migration, CORS and WebSocket origins locked to the MAKU domain.
- Logos converted to WebP (12 MB → 0.2 MB).
