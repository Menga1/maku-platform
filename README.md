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

## Scope note for your capstone report

The solar and offshore modules can read live Open-Meteo forecast and marine
data when their automatic feeds are armed. The underground, high-rise, and data
center modules use bounded simulated telemetry because their specialist sensor
feeds are not publicly available here; every module also supports manual
inputs. Each input layer is thin and swappable, so connecting production
telemetry later does not require changing the risk logic. This remains an MVP:
validate every feed, threshold, and operational response with the responsible
HSE and engineering teams before using it on a real site.

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
