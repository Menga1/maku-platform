# MAKU — Multi-Environment AI for Kinetic Risk Assessment
### in Mega-Underground, Offshore, and Solar Construction & MEP — expanded to High-Rise and Data Center environments

A Streamlit MVP with **five** environment-specific risk modules, each driven by
its own formula rather than a single generic score:

| Module | Core formula(s) | Primary hazard modeled |
|---|---|---|
| ☀️ Solar (Desert) | Albedo-weighted GHI thermal amplification + UV index correction against ambient temp | Acute heat stroke / UV-driven heat exhaustion for MEP tracker/module crews |
| 🌊 Offshore (Marine) | Environment Canada Humidex (vapor-pressure driven) + offshore wind-gust kinetic thresholds | Heat retention / thermal stress + wind-driven crane/lifting risk for welding/pipe-fitting/scaffolding crews |
| 🚇 Underground (Tunnel/Metro) | Humidex-based trapped-heat/geothermal-humidity model + PM2.5/CO OEL screening | Heat stress + air-quality (CO/PM2.5) exposure for MEP electrical crews pulling high-voltage cabling |
| 🏙️ High-Rise (Vertical Urban) | Exponential wind-shear scaling by floor level + crane-load oscillation index | Wind-shear-driven crane load-swing and fall-from-height risk for MEP riser & external-wall crews |
| 🖥️ Data Center (Controlled Critical Environment) | Load-scaled arc-flash incident-energy screen + hot/cold-aisle thermal differential, confined-space/armed-suppression cross-check | Arc-flash energy + thermal stress + confined-space asphyxiant risk for MEP/electrical commissioning crews |

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501).

## How it works

- **risk_engine.py** — all the math. Transparent, formula-based (not a black-box
  ML model), so every number can be traced back to a recognized/adapted method:
  WBGT, Humidex, ACGIH TLV, OEL comparison, a wind power-law height profile for
  gust amplification, and the Ralph Lee open-air arc-flash incident-energy
  equation. This is deliberate: HSE professionals and assessors trust
  auditable logic over an opaque AI score.
- **ai_advisor.py** — turns the risk engine's structured output into (1) a
  rule-based hierarchy-of-controls list, always available with no dependencies,
  and (2) an optional plain-language briefing generated via the Anthropic API
  if you paste an API key into the sidebar. Without a key, a solid fallback
  narrative is generated automatically — the app never breaks without one.
- **app.py** — the Streamlit dashboard entry point (overview + language
  selector); each environment's assessment UI is a separate page under
  `pages/`, per the project's multipage structure.
- **i18n.py** — shared UI translation layer, defaulting to French with English
  as an alternate. Only display strings live here; math and control logic
  never do.

### Module math reference

**Module 1 — Solar (Desert):** `calculate_solar_albedo_heat_risk()` combines
a surface-specific albedo factor (pure desert sand 0.30, silicon PV panels
0.15, hybrid assembly zone 0.25) with GHI to get a thermal-amplification term
(`GHI × albedo / 100`), then adds a UV correction (`UV index × 0.5`) on top of
ambient temperature to produce a perceived thermal temperature. Bands: LOW
(<32°C), MODERATE (32–37.9°C), HIGH (38–44.9°C or UV ≥ 8), CRITICAL (≥45°C or
UV ≥ 11, triggers a safety override and a 15-min/hour shift cap).

**Module 2 — Offshore (Marine):** `calculate_marine_humidex_risk()` uses the
Environment Canada Humidex formula, `Humidex = Ta + 0.5555 × (e - 10)`, where
`e` is actual vapor pressure in hPa from the shared saturation-vapor-pressure
helper, `e = (RH/100) × 6.105 × exp(17.27 × Ta / (237.7 + Ta))`. Humidex bands:
Low (<29), Moderate (29–34.9), High (35–39.9), Extreme (≥40). This thermal
risk is cross-referenced against an independent offshore wind-gust gate:
Normal Operations (<18 knots), Restricted – Monitor Closely (18–24.9 knots),
Suspended – Crane/Lifting Danger (≥25 knots). A safety override fires if the
Humidex band is Extreme or the wind gate is Suspended.

**Module 3 — Underground (Tunnel/Metro):** `calculate_underground_kinetic_risk()`
reuses the shared Humidex helper to model trapped-heat + geothermal-humidity
as a perceived temperature (stagnant, near-saturated tunnel air behaves like a
Humidex problem, not a dry desert WBGT one). Heat bands: LOW (<32°C), MODERATE
(32–37.9°C), HIGH (38–41.9°C), CRITICAL (≥42°C). In parallel, PM2.5 and CO are
screened against independent OEL bands (PM2.5 critical >250 µg/m³; CO critical
>25 ppm). The overall risk band takes the worst of the three; a safety
override fires - halting high-voltage MEP cabling work - if either OEL is
breached or perceived temperature exceeds 42°C.

**Module 4 — High-Rise (Vertical Urban):** `calculate_high_rise_kinetic_risk()`
scales ground wind speed exponentially with floor level,
`V(h) = V_ground × e^(0.008 × floor_level)`, approximating urban boundary-layer
shear/turbulence amplification with height. A load-oscillation index,
`(scaled_wind_speed² / crane_load_mass_tons)`, captures why lighter,
high-surface-area facade/curtain-wall loads swing far worse than dense
structural loads under the same wind loading. The risk band takes the worse of
independent wind-speed and oscillation-index bands (LOW/MODERATE/HIGH/
CRITICAL); a safety override forces an immediate suspension of crane lifts and
external-wall work whenever scaled wind exceeds 30 knots.

**Module 5 — Data Center (Controlled Critical Environment):**
`calculate_datacenter_kinetic_risk()` uses a simplified load-driven arc-flash
incident-energy screen, `IE = 2.5 × (load_kW / 100)²` cal/cm², reflecting how
available fault energy compounds with switchgear capacity (an illustrative
MVP coefficient - see `lee_arc_flash_incident_energy()` in `risk_engine.py`
for the full Ralph Lee voltage/fault-current/clearing-time/working-distance
form, kept as a reference for when those individual parameters are known).
In parallel, a hot/cold-aisle thermal differential is computed against an
assumed 22°C cold-aisle target. The risk band takes the worse of independent
arc-flash and thermal bands. A safety override fires - halting all
commissioning work in the zone - if incident energy exceeds 40 cal/cm² (no
PPE category permits live work above this), if the thermal differential or
hot-aisle temperature crosses its critical threshold, or if a gaseous
clean-agent suppression system is armed while crews are inside a confined
ceiling-void space (asphyxiation/accidental-discharge risk).

## Official HSE Report: PDF export & regulatory references

Every module page (and the dashboard, showing the last-viewed assessment)
renders an **Official HSE Report** section with two real downloads - an
actual `.pdf` (built with `fpdf2`, not a browser print-to-PDF of the HTML
view) and an `.html` version - plus a printable in-page preview. Both
include:

- The current assessment's metrics, drivers, AI narrative, and mitigation
  action plan (unchanged from before).
- A **Regulatory References** section (`regulatory_references.py`) citing
  the real, applicable standards body and document for that module across
  UAE (Dubai Municipality Code of Construction Safety Practice; ADOSH-SF,
  the Abu Dhabi Occupational Safety and Health System Framework -
  administered by ADPHC, formerly OSHAD), USA (OSHA, ACGIH, NFPA), UK
  (HSE), Canada (CCOHS/CSA), and Australia (Safe Work Australia).
- A **Further Reading** bibliography citing one general professional
  reference text (Roger L. Brauer, *Safety and Health for Engineers*,
  Wiley) by title/author/publisher.

**Important boundary, stated explicitly because it matters here:**
`regulatory_references.py` and the report it feeds are a *citation list*,
not a copy of any regulation or book. No legislative text or copyrighted
book content is reproduced anywhere in this app - for two reasons, not
one. First, copyright: most cited standards (and the Brauer text) are
copyrighted works. Second, and more important for a tool that informs
real site-safety decisions: a fabricated or slightly-wrong paraphrase of
a legal threshold is more dangerous than no citation at all, because it
looks authoritative. Every reference points to where the user's HSE team
should go to read the actual current text; MAKU never claims to be that
source itself, and the AI narrative's "regulatory basis" line is
generated from this same verified list rather than a separate hardcoded
one, so the two can't drift out of sync or reference something
unverified.

Anyone using MAKU professionally should verify the current,
jurisdiction-correct version of every cited document - regulations are
amended over time and MAKU does not track amendments.

## What each new module adds

- **High-Rise**: projects ground-level wind speed to the working floor with an
  exponential boundary-layer scaling curve (steeper amplification the higher
  the floor, simulating the shear a real multi-level anemometer network + BIM
  digital twin would report), then derives a load-oscillation index from that
  scaled wind and the crane load's mass - light, high-surface-area
  facade/curtain-wall loads swing far worse than dense structural loads. A
  hard safety override suspends crane lifts and external-wall work above the
  30-knot scaled-wind threshold.
- **Data Center**: combines a hot/cold-aisle thermal differential with a
  load-scaled arc-flash incident-energy screen, plus confined-space +
  armed-clean-agent cross-referencing - crews inside a confined ceiling-void
  space while a gaseous suppression system is armed is an automatic safety
  override, independent of the thermal/arc-flash reading.

## HSE Virtual Library & Live Legislation Search

Every module page now also shows an **HSE Virtual Library** section
(`regulatory_references.py` / `render_virtual_library()`) linking to
genuinely free, legally accessible publications from ILO, WHO, NIOSH,
OSHA, UK HSE, and CCOHS, plus a constructed Google Books search link for
that module's topic (Google's own book-preview/search system - MAKU never
fetches or reproduces book content). Copyrighted texts like Brauer's
*Safety and Health for Engineers* are pointed to for purchase/institutional
access, never reproduced.

A sidebar checkbox, off by default, lets the user opt into **live
legislation search**: when enabled (and an Anthropic API key is supplied),
`generate_narrative()` gives Claude access to its built-in `web_search`
tool so it can check current, jurisdiction-specific guidance and cite real
URLs it finds - on top of, never instead of, the verified reference list.
This reuses the same API key already required for the AI briefing; no
separate search API key is needed. It's opt-in because live search adds
API cost and latency.

**A second fabrication bug found and fixed while building this:** the
*live* prompt sent to the Anthropic API (not just the offline fallback
fixed earlier) was instructing the model to "use Roger Bauer's
deep-excavation and tunnel-boring-machine risk-analysis principles" and to
"name the framework and protocol" - i.e., actively telling a live LLM call
to invent specifics for an unverified named methodology, on every
API-backed briefing. This has been removed. The prompt now supplies the
model with the exact verified references for that module and explicitly
forbids inventing named methodologies, principles, or clause numbers - see
`TestGenerateNarrativeRequest` in `test_app.py`, which inspects the actual
request payload sent to the API (via mocking, no real network call) to
keep this from silently regressing.

## Meteorology Forecast, Assessment Log & Monthly Excel Export

**7-day meteorology forecast** (Solar and Offshore pages only): a real,
free, keyless call to Open-Meteo's daily forecast API
(`fetch_solar_forecast()` / `fetch_offshore_forecast()` in
`data_feeds.py`) - max temperature, max UV, and radiation for Solar; max
temperature and max wind for Offshore. Shown as a small line chart in an
expander on each page. The other 3 modules (Underground, High-Rise, Data
Center) don't get a forecast section, because there is no real public
forecast API for tunnel/crane/data-center sensors - MAKU doesn't fabricate
one just to have a chart there.

**Assessment log & trend analytics** (dashboard, `analytics.py`): every
assessment run on any of the 5 pages is logged (timestamp, module, risk
band, safety override, a per-module headline metric) to
`st.session_state`. The dashboard shows a live count/chart, a "Download
log (CSV)" button, and a "Monthly Excel Report" button producing a real
`.xlsx` (openpyxl) with three sheets: raw log, a month+module summary
table, and a genuinely embedded line chart (not just a description of
one - verified in `test_app.py` by reopening the generated file and
checking `wb["Trend Chart"]._charts`).

**Persistence caveat - stated plainly because it matters:** Streamlit
Cloud gives an app ephemeral local storage only. Anything written to disk
is wiped on redeploy, reboot, or extended inactivity - there is no
database here. So the log above is session-scoped: it remembers what ran
during the current browser session, nothing from before it and nothing
that survives a restart. To build a genuine multi-week/monthly history,
the user carries it forward manually: download the CSV periodically, and
re-upload it in a later session via the "Upload a previous log (CSV) to
merge" field, which de-duplicates on merge. This is an honest low-tech
substitute for a real backend, not a claim that persistent storage
exists. If true persistence is needed later, the fix is swapping in a
real datastore behind `analytics.py`'s three functions
(`log_assessment`/`get_log_dataframe`/`merge_uploaded_csv`) - that
change is isolated to this one file and doesn't touch `risk_engine.py`
or any page.

## Scope note for your capstone report

This MVP **simulates** the real-time data feeds described in the architecture
(satellite GHI/albedo, offshore buoy telemetry, subsurface GIS/OEL sensors,
multi-level building anemometers/BIM, rack-level IoT thermal mapping) via
manual inputs and sliders, rather than integrating live APIs — that level of
systems integration is beyond a capstone timeline. The architecture is built so
each module's inputs are a thin, swappable layer: replacing sliders with a live
data source later is a data-plumbing change, not a change to the risk logic
itself. It's worth stating this explicitly in your report as "MVP with
simulated inputs, designed for live-data extension" — assessors will read that
as engineering maturity, not a shortcut.

The Lee arc-flash equation and the wind power-law profile are recognized,
published methods used here for early-stage/illustrative hazard screening —
call this out explicitly as not a substitute for a full IEEE 1584 arc-flash
study or a certified structural/wind engineering assessment before any live
work is authorized on a real site.

## Ideas for extending it further (if you have time before submission)

- Add a data-logging layer (CSV/SQLite) so repeated assessments build a site
  risk history over a shift/project, across all five modules.
- Add a PDF/Word export of each assessment for a real HSE audit trail (there
  are docx/pdf generation tools that could plug in here).
- Add a simple map view (e.g. per-site markers) if you want the "GIS" framing
  to show visually rather than just in text.
- Wire the High-Rise module to a real per-floor anemometer array and the Data
  Center module to a rack-level IoT feed, replacing the simulated inputs.
