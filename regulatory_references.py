"""
MAKU - Regulatory References & Bibliography
=============================================
This module names the real, applicable standards bodies and documents for
each MAKU risk module, and cites one general professional reference text.

WHAT THIS FILE IS: a curated citation list (title, issuing body, document
number, region, and - where the issuing body publishes it freely - a link
to the official source).

WHAT THIS FILE IS NOT: a copy of any regulation, code of practice, or
textbook. No legislative text, code clause, or book content is reproduced
here. Two reasons, not one:
  1. Copyright - most of the standards named below (and the Brauer text)
     are copyrighted works; reproducing them without license is
     infringement regardless of intent.
  2. Accuracy/safety - MAKU informs real construction-site safety
     decisions. A fabricated or slightly-wrong paraphrase of a legal
     threshold is more dangerous than no citation at all, because it
     looks authoritative. Every reference below points to where the user
     or their HSE team should go to read the actual current text - MAKU
     never claims to be that source itself.

Anyone using MAKU professionally should verify the current, jurisdiction-
correct version of every cited document before relying on it - regulations
are amended over time and MAKU does not track amendments.

GLOBAL EXPANSION NOTE: UK, Canada, and Australia citation entries were added
per-module below alongside the existing USA/UAE/France/international
entries. This file still holds CITATIONS ONLY (standards body, document
title, region, URL) - the actual numeric threshold values for these
countries (heat-stress method, wind-shear knots, noise dBA, silica ug/m3,
UV/bushfire-smoke bands, cold-stress Wind Chill, remote-communication
requirements) live in regulatory_country_thresholds.py, exactly per that
file's own naming-note rationale above. Keeping numeric thresholds out of
this file is deliberate, not an oversight.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Per-module regulatory references
# ---------------------------------------------------------------------------
# Keyed by the exact "module" string risk_engine.py puts in its result dict,
# so ai_advisor.get_references(result) can look this up directly.

REGULATORY_REFERENCES: dict[str, list[dict]] = {
    "Solar (Desert)": [
        {"region": "UAE - Dubai", "body": "Dubai Municipality", "doc": "Code of Construction Safety Practice in the Emirate of Dubai (DM COP) - heat stress / working in high temperature provisions", "url": "https://www.dm.gov.ae/wp-content/uploads/2022/04/code_of_safety_EN.pdf"},
        {"region": "UAE - Abu Dhabi", "body": "ADPHC (Abu Dhabi Public Health Centre; framework formerly administered as OSHAD)", "doc": "ADOSH-SF (Abu Dhabi Occupational Safety and Health System Framework) - Heat Stress Management Code of Practice", "url": "https://www.adphc.gov.ae"},
        {"region": "USA", "body": "OSHA", "doc": "29 CFR 1926 (Construction) - Subpart D general environmental controls; OSHA Heat Illness Prevention guidance", "url": "https://www.osha.gov/heat-exposure"},
        {"region": "USA / International", "body": "ACGIH", "doc": "Threshold Limit Values (TLVs) - Heat Stress and Strain", "url": "https://www.acgih.org"},
        {"region": "UK", "body": "HSE (Health and Safety Executive)", "doc": "Thermal comfort / working outdoors guidance", "url": "https://www.hse.gov.uk/temperature"},
        {"region": "Canada", "body": "CCOHS / CNESST", "doc": "Humidex Based Heat Response Plan guidance; provincial heat-stress prevention guidance (e.g. CNESST, Quebec)", "url": "https://www.ccohs.ca/oshanswers/phys_agents/humidex.html"},
        {"region": "Australia", "body": "Safe Work Australia", "doc": "Managing the risks of working in heat - Code of Practice; SunSmart UV Index workplace guidance", "url": "https://www.safeworkaustralia.gov.au"},
    ],
    "Offshore (Marine)": [
        {"region": "UAE - Abu Dhabi", "body": "ADPHC", "doc": "ADOSH-SF - Marine/offshore operations and heat stress elements", "url": "https://www.adphc.gov.ae"},
        {"region": "UK", "body": "HSE", "doc": "Offshore health and safety guidance (energy/marine sector)", "url": "https://www.hse.gov.uk/offshore"},
        {"region": "USA", "body": "OSHA / BSEE", "doc": "29 CFR 1917 (Marine Terminals); Bureau of Safety and Environmental Enforcement offshore standards", "url": "https://www.osha.gov"},
        {"region": "Canada", "body": "CCOHS / CSA Group", "doc": "CSA Z1015 and related marine/offshore OH&S guidance", "url": "https://www.ccohs.ca"},
        {"region": "Australia", "body": "NOPSEMA / Safe Work Australia", "doc": "Offshore petroleum and greenhouse gas storage safety regulations", "url": "https://www.nopsema.gov.au"},
    ],
    "Underground (Tunnel/Metro)": [
        {"region": "UAE - Dubai", "body": "Dubai Municipality", "doc": "Code of Construction Safety Practice in the Emirate of Dubai (DM COP) - confined space and excavation provisions", "url": "https://www.dm.gov.ae/wp-content/uploads/2022/04/code_of_safety_EN.pdf"},
        {"region": "UAE - Abu Dhabi", "body": "ADPHC", "doc": "ADOSH-SF - Confined Space Entry and Excavation Codes of Practice", "url": "https://www.adphc.gov.ae"},
        {"region": "USA", "body": "OSHA", "doc": "29 CFR 1926 Subpart AA (Confined Spaces in Construction); 29 CFR 1926.800 (Underground Construction)", "url": "https://www.osha.gov"},
        {"region": "USA / International", "body": "ACGIH", "doc": "TLVs for Chemical Substances (CO) and Particulates (Not Otherwise Specified, PM)", "url": "https://www.acgih.org"},
        {"region": "UK", "body": "HSE", "doc": "L101 - Safe work in confined spaces (Approved Code of Practice)", "url": "https://www.hse.gov.uk/pubns/priced/l101.pdf"},
        {"region": "Canada", "body": "CCOHS", "doc": "Confined Space Entry - OH&S guidance", "url": "https://www.ccohs.ca/oshanswers/hsprograms/confinedspace_entry.html"},
        {"region": "Australia", "body": "Safe Work Australia", "doc": "Confined Spaces - Code of Practice", "url": "https://www.safeworkaustralia.gov.au"},
    ],
    "High-Rise (Vertical Urban)": [
        {"region": "UAE - Dubai", "body": "Dubai Municipality", "doc": "Code of Construction Safety Practice in the Emirate of Dubai (DM COP) - crane operations and working at height provisions", "url": "https://www.dm.gov.ae/wp-content/uploads/2022/04/code_of_safety_EN.pdf"},
        {"region": "UAE - Abu Dhabi", "body": "ADPHC", "doc": "ADOSH-SF - Working at Height and Lifting Operations Codes of Practice", "url": "https://www.adphc.gov.ae"},
        {"region": "USA", "body": "OSHA", "doc": "29 CFR 1926 Subpart CC (Cranes and Derricks); Subpart M (Fall Protection)", "url": "https://www.osha.gov"},
        {"region": "UK", "body": "HSE", "doc": "Work at Height Regulations 2005; LOLER (Lifting Operations and Lifting Equipment Regulations)", "url": "https://www.hse.gov.uk/work-at-height"},
        {"region": "Canada", "body": "CSA Group", "doc": "CSA Z150 (Safety Code on Mobile Cranes); provincial OH&S working-at-height regulations", "url": "https://www.csagroup.org"},
        {"region": "Australia", "body": "Safe Work Australia", "doc": "Managing the Risk of Falls at Workplaces - Code of Practice; Mobile Crane Code of Practice", "url": "https://www.safeworkaustralia.gov.au"},
    ],
    "Data Center (Controlled Critical Environment)": [
        {"region": "UAE - Dubai", "body": "Dubai Municipality / DEWA", "doc": "Code of Construction Safety Practice in the Emirate of Dubai (DM COP) - electrical safety provisions", "url": "https://www.dm.gov.ae/wp-content/uploads/2022/04/code_of_safety_EN.pdf"},
        {"region": "UAE - Abu Dhabi", "body": "ADPHC", "doc": "ADOSH-SF - Electrical Safety Code of Practice", "url": "https://www.adphc.gov.ae"},
        {"region": "USA", "body": "NFPA", "doc": "NFPA 70E - Standard for Electrical Safety in the Workplace (arc-flash PPE categories)", "url": "https://www.nfpa.org/70E"},
        {"region": "USA", "body": "OSHA", "doc": "29 CFR 1926 Subpart K (Electrical)", "url": "https://www.osha.gov"},
        {"region": "UK", "body": "HSE", "doc": "Electricity at Work Regulations 1989", "url": "https://www.hse.gov.uk/electricity"},
        {"region": "Canada", "body": "CSA Group", "doc": "CSA Z462 - Workplace Electrical Safety", "url": "https://www.csagroup.org"},
        {"region": "Australia", "body": "Safe Work Australia", "doc": "Managing Electrical Risks in the Workplace - Code of Practice", "url": "https://www.safeworkaustralia.gov.au"},
    ],
    "Wind Energy (Onshore/Offshore)": [
        {"region": "International", "body": "GWO (Global Wind Organisation)", "doc": "Basic Safety Training (BST) standard - Working at Heights module", "url": "https://globalwindsafety.org"},
        {"region": "USA", "body": "NOAA / OSHA", "doc": "Lightning Safety - the 30-30 rule for outdoor work stoppage", "url": "https://www.weather.gov/safety/lightning"},
        {"region": "USA", "body": "OSHA", "doc": "29 CFR 1926 Subpart M (Fall Protection); 29 CFR 1910.269 (Electric Power Generation)", "url": "https://www.osha.gov"},
        {"region": "UK", "body": "HSE / RenewableUK", "doc": "Offshore wind health and safety guidance", "url": "https://www.hse.gov.uk"},
        {"region": "Canada", "body": "CCOHS / Provincial OHS regulators", "doc": "Working-at-height and electrical-safety OH&S guidance applicable to wind turbine operations and maintenance", "url": "https://www.ccohs.ca"},
        {"region": "Australia", "body": "Safe Work Australia / Clean Energy Council", "doc": "Managing the Risk of Falls at Workplaces - Code of Practice; Clean Energy Council wind farm safety guidance", "url": "https://www.safeworkaustralia.gov.au"},
        {"region": "UAE - Abu Dhabi", "body": "ADPHC", "doc": "ADOSH-SF - Working at Height and Lifting Operations Codes of Practice", "url": "https://www.adphc.gov.ae"},
    ],
    "Mining & Quarrying": [
        {"region": "USA", "body": "OSHA", "doc": "29 CFR 1926.1153 - Respirable Crystalline Silica (Construction)", "url": "https://www.osha.gov/silica"},
        {"region": "USA", "body": "MSHA", "doc": "Mine Safety and Health Administration standards (30 CFR)", "url": "https://www.msha.gov"},
        {"region": "USA / International", "body": "ACGIH", "doc": "TLVs - Respirable Crystalline Silica (Quartz) and Noise", "url": "https://www.acgih.org"},
        {"region": "EU / France", "body": "European Commission / Code du Travail", "doc": "Directive 2003/10/EC (Noise); Directive 2002/44/EC (Vibration); Code du Travail Art. R4431 et seq.", "url": "https://eur-lex.europa.eu"},
        {"region": "UK", "body": "HSE", "doc": "Control of Noise at Work Regulations 2005; Control of Vibration at Work Regulations 2005; EH40/2005 Workplace Exposure Limits (respirable crystalline silica)", "url": "https://www.hse.gov.uk/noise"},
        {"region": "Canada", "body": "CCOHS / CNESST / Provincial Mining Regulators", "doc": "Occupational exposure limits for respirable crystalline silica and noise under provincial OHS/mining regulations", "url": "https://www.ccohs.ca/oshanswers/chemicals/silica.html"},
        {"region": "Australia", "body": "Safe Work Australia", "doc": "Managing the Risks of Respirable Crystalline Silica - Code of Practice; Workplace Exposure Standard for RCS (2020)", "url": "https://www.safeworkaustralia.gov.au"},
    ],
    "Marine & Port Construction": [
        {"region": "USA", "body": "OSHA", "doc": "29 CFR 1926.56 (Illumination); 29 CFR 1917 (Marine Terminals)", "url": "https://www.osha.gov"},
        {"region": "International", "body": "ISO", "doc": "ISO 12944 - Corrosion Protection of Steel Structures by Protective Paint Systems (exposure/durability categories)", "url": "https://www.iso.org"},
        {"region": "International", "body": "API", "doc": "API RP 2A - Recommended Practice for Planning, Designing and Constructing Fixed Offshore Platforms", "url": "https://www.api.org"},
        {"region": "UK", "body": "HSE", "doc": "Health and safety in ports guidance", "url": "https://www.hse.gov.uk"},
        {"region": "Canada", "body": "Transport Canada / CCOHS", "doc": "Marine Occupational Safety and Health Regulations", "url": "https://tc.canada.ca"},
        {"region": "Australia", "body": "Safe Work Australia / AMSA", "doc": "Health and safety in the maritime industry guidance; National Standard for Commercial Vessels", "url": "https://www.safeworkaustralia.gov.au"},
        {"region": "UAE - Dubai", "body": "Dubai Municipality", "doc": "Code of Construction Safety Practice in the Emirate of Dubai (DM COP) - marine works provisions", "url": "https://www.dm.gov.ae/wp-content/uploads/2022/04/code_of_safety_EN.pdf"},
    ],
    "Occupational Heat Stress (ISO 7243 / ACGIH TLV)": [
        {"region": "International", "body": "ISO", "doc": "ISO 7243 - Ergonomics of the thermal environment - Assessment of heat stress using the WBGT (wet bulb globe temperature) index", "url": "https://www.iso.org/standard/61190.html"},
        {"region": "USA / International", "body": "ACGIH", "doc": "Threshold Limit Values (TLVs) for Heat Stress and Strain - workload category, clothing adjustment, and acclimatization guidance", "url": "https://www.acgih.org"},
        {"region": "USA", "body": "OSHA", "doc": "Heat Illness Prevention guidance; OSHA Technical Manual Section III Chapter 4 (Clothing Adjustment Factors)", "url": "https://www.osha.gov/heat-exposure"},
        {"region": "USA / International", "body": "NIOSH", "doc": "Criteria for a Recommended Standard: Occupational Exposure to Heat and Hot Environments", "url": "https://www.cdc.gov/niosh/docs/2016-106/"},
    ],
}

# ---------------------------------------------------------------------------
# General professional bibliography (not module-specific)
# ---------------------------------------------------------------------------
# Cited by title/author/publisher only. MAKU does not reproduce, summarize
# in detail, or quote from any of these - they are pointers for the user's
# HSE team to consult directly.

FURTHER_READING: list[dict] = [
    {
        "author": "Roger L. Brauer",
        "title": "Safety and Health for Engineers, 3rd Edition",
        "publisher": "Wiley-Blackwell, 2016. ISBN 978-1-118-95945-9 (print) / 978-1-119-21918-7 (digital).",
        "note": "Broad engineering-focused safety/HSE reference text; purchase directly from the publisher or an academic bookseller.",
        "url": "https://www.wiley.com/en-us/Safety+and+Health+for+Engineers%2C+3rd+Edition-p-9781118959459",
    },
    {
        "author": "Jeffrey W. Vincoli (ed.)",
        "title": "Lewis' Dictionary of Occupational and Environmental Safety and Health",
        "publisher": "CRC Press LLC (Boca Raton), 2000.",
        "note": "~25,000-term reference dictionary spanning OSH, industrial hygiene, environmental compliance, and related disciplines; consult a library copy or the publisher.",
        "url": "https://www.routledge.com/search?author=Jeffrey%20W.%20Vincoli",
    },
    {
        "author": "ACGIH",
        "title": "TLVs and BEIs - Threshold Limit Values for Chemical Substances and Physical Agents",
        "publisher": "ACGIH (published/updated annually)",
        "note": "Primary source for the heat-stress and air-quality action limits this app's formulas are modeled on.",
    },
    {
        "author": "NFPA",
        "title": "NFPA 70E - Standard for Electrical Safety in the Workplace",
        "publisher": "National Fire Protection Association",
        "note": "Governing standard for arc-flash PPE category selection referenced in the Data Center module.",
    },
]


def get_references(module: str) -> list[dict]:
    """Return the curated reference list for a given risk_engine module
    name. Falls back to an empty list for an unrecognized module rather
    than raising, since a missing citation list should never break the
    page that's displaying it."""
    return REGULATORY_REFERENCES.get(module, [])


def get_further_reading() -> list[dict]:
    return FURTHER_READING


# ---------------------------------------------------------------------------
# Free/open-access HSE virtual library
# ---------------------------------------------------------------------------
# General (not module-specific) directory of genuinely free, legally
# accessible HSE publications from major standards/health bodies. These are
# organizations that publish substantial guidance free of charge - unlike
# the paid standards (OSHA CFRs excepted - those are public domain) and
# textbooks cited above. Still citations/links only, never reproduced text.

FREE_HSE_LIBRARY: list[dict] = [
    {
        "body": "ILO (International Labour Organization)",
        "description": "UN agency; publishes International Labour Standards on OSH and extensive free guidance covering nearly every hazard category.",
        "url": "https://www.ilo.org/topics-and-sectors/safety-and-health-work",
    },
    {
        "body": "WHO (World Health Organization)",
        "description": "Occupational health guidance, including heat stress, health-worker safety, and hazard-specific technical publications, free to read/download.",
        "url": "https://www.who.int/health-topics/occupational-health",
    },
    {
        "body": "NIOSH (US National Institute for Occupational Safety and Health)",
        "description": "Research-backed guidance documents, hazard alerts, and numbered publications; the technical research arm behind many OSHA/ACGIH limits.",
        "url": "https://www.cdc.gov/niosh/pubs/default.html",
    },
    {
        "body": "OSHA (US Occupational Safety and Health Administration)",
        "description": "Free fact sheets, hazard alerts, and guidance documents (the regulations themselves, 29 CFR, are also public domain).",
        "url": "https://www.osha.gov/publications/",
    },
    {
        "body": "HSE (UK Health and Safety Executive)",
        "description": "Extensive free guidance library, including Approved Codes of Practice summaries and sector-specific publications.",
        "url": "https://www.hse.gov.uk/pubns/",
    },
    {
        "body": "CCOHS (Canadian Centre for Occupational Health and Safety)",
        "description": "Free OSH Answers fact sheets covering most workplace hazard categories in the app.",
        "url": "https://www.ccohs.ca/oshanswers/",
    },
    {
        "body": "Safe Work Australia",
        "description": "Free model Codes of Practice and guidance material (heat, UV, silica, noise, isolated/remote work) underpinning Australia's model WHS Regulations.",
        "url": "https://www.safeworkaustralia.gov.au/collection/model-codes-practice",
    },
]


def get_free_library() -> list[dict]:
    return FREE_HSE_LIBRARY


def google_books_search_url(topic: str) -> str:
    """
    Builds a link to Google's own book-search results page for a topic.
    This is Google Books' own legitimate search/preview system (it handles
    publisher licensing for previews itself) - MAKU just constructs the
    query URL, it never fetches, caches, or reproduces any book content.
    """
    from urllib.parse import quote_plus
    return f"https://www.google.com/search?tbm=bks&q={quote_plus(topic)}"


# Per-module search topic used to build the Google Books link above.
MODULE_LIBRARY_TOPICS: dict[str, str] = {
    "Solar (Desert)": "heat stress construction safety engineering",
    "Offshore (Marine)": "offshore marine construction safety engineering",
    "Underground (Tunnel/Metro)": "tunnel underground construction safety engineering",
    "High-Rise (Vertical Urban)": "crane wind load high-rise construction safety engineering",
    "Data Center (Controlled Critical Environment)": "arc flash electrical safety engineering",
    "Wind Energy (Onshore/Offshore)": "wind turbine working at height lightning safety engineering",
    "Mining & Quarrying": "mining quarry silica noise vibration occupational health engineering",
    "Marine & Port Construction": "marine port construction corrosion safety engineering",
    "Occupational Heat Stress (ISO 7243 / ACGIH TLV)": "occupational heat stress WBGT ACGIH ISO 7243 engineering",
}


def get_library_topic(module: str) -> str:
    return MODULE_LIBRARY_TOPICS.get(module, "occupational safety and health engineering")


# ---------------------------------------------------------------------------
# Formula-Level Regulatory Algorithm Validation
# ---------------------------------------------------------------------------
# HSE audit corrective action: "inline documentation/metadata mapping every
# scoring formula against recognized standards (ISO 7243, ACGIH, OSHA,
# IEEE 1584)." REGULATORY_REFERENCES above cites standards bodies PER
# MODULE (a reading list); this table is finer-grained - one row PER
# NAMED FORMULA/FUNCTION in risk_engine.py, so an auditor can check each
# individual calculation against its claimed standard rather than a whole
# module's general reading list.
#
# "validation_status" is deliberately a 3-way honest classification, not a
# blanket "compliant" stamp:
#   - "Direct implementation"     - a published, named formula/table is
#                                    implemented as documented (e.g. the
#                                    Humidex formula, ISO 2631-1 WBV A(8)).
#   - "Adapted / approximated"    - based on a real named standard, but not
#                                    a verbatim reproduction (e.g. ACGIH TLV
#                                    figures reconstructed from the table's
#                                    published shape, not the copyrighted
#                                    booklet itself; the BoM WBGT
#                                    approximation formula in place of a
#                                    real globe/wet-bulb sensor reading).
#   - "Illustrative (not standards-derived)" - a physics-motivated or
#                                    project-specific screening heuristic
#                                    this app invented for MVP purposes -
#                                    explicitly NOT claimed to come from any
#                                    named standard, and never labeled as
#                                    such elsewhere in this app.
# This table was built by reading every formula's own existing docstring/
# inline comment in risk_engine.py and risk_matrix.py - it does not
# introduce any new claim risk_engine.py doesn't already make about
# itself; it centralizes those claims into one auditable table and
# corrects one pre-existing imprecision along the way (the High-Rise
# module's wind-with-height model is an exponential curve, not a literal
# power-law, despite this file's own module docstring loosely calling it
# a "power-law profile" - see that row's caveat below).
FORMULA_STANDARDS_MAP: list[dict] = [
    {
        "function": "wbgt_outdoor_approx()",
        "module": "Shared helper (Solar, Offshore heat-stress inputs)",
        "formula_summary": "WBGT = 0.567*Ta + 0.393*e + 3.94 (outdoor WBGT approximation from dry-bulb temp + RH)",
        "cited_standards": ["ISO 7243 (WBGT concept/index)", "Australian Bureau of Meteorology (approximation formula)"],
        "validation_status": "Adapted / approximated",
        "caveat": "A published meteorological approximation used when no direct globe/wet-bulb WBGT sensor "
                  "reading is available - not equivalent to a real ISO 7243 instrument measurement.",
    },
    {
        "function": "humidex() / classify_humidex()",
        "module": "Shared helper (Offshore; Canada heat-stress method)",
        "formula_summary": "Humidex = Ta + 0.5555*(e - 10.0)",
        "cited_standards": ["Environment Canada - Humidex"],
        "validation_status": "Direct implementation",
        "caveat": "Formula and published comfort/danger category bands both match Environment Canada's "
                  "documented Humidex method.",
    },
    {
        "function": "wind_chill_c() / classify_wind_chill()",
        "module": "Shared helper (Canada cold-stress method)",
        "formula_summary": "WCI = 13.12 + 0.6215*T - 11.37*V^0.16 + 0.3965*T*V^0.16 (valid T<=10C, wind>4.8 km/h)",
        "cited_standards": ["Environment and Climate Change Canada - Wind Chill Index"],
        "validation_status": "Direct implementation",
        "caveat": "Outside its documented validity domain the function intentionally returns the unmodified "
                  "temperature rather than extrapolating the formula.",
    },
    {
        "function": "ACGIH_WBGT_LIMITS / acgih_action_level() / _acgih_table() / calculate_iso7243_heat_stress()",
        "module": "Occupational Heat Stress (ISO 7243 / ACGIH TLV)",
        "formula_summary": "WBGT action-limit table lookup by workload category and work/rest ratio, plus "
                            "Clothing Adjustment Factor and acclimatization shift",
        "cited_standards": ["ACGIH TLVs for Heat Stress and Strain", "ISO 7243 (WBGT screening methodology)",
                             "OSHA Technical Manual Section III Chapter 4 (Clothing Adjustment Factors)"],
        "validation_status": "Adapted / approximated",
        "caveat": "light/moderate/heavy figures follow the published ACGIH TLV table shape; the very_heavy row "
                  "and the acclimatized-worker shift are commonly-cited reconstructions, not a verbatim "
                  "transcription of the current copyrighted booklet - verify against the current edition "
                  "before a real compliance decision (flagged in-app at the point of use).",
    },
    {
        "function": "noise_dose_percent()",
        "module": "Mining & Quarrying; Acoustic Noise Exposure",
        "formula_summary": "allowed_hours = 8 / 2^((L - criterion)/exchange_rate); dose = 100 * actual/allowed",
        "cited_standards": ["OSHA 29 CFR 1910.95 (exchange-rate dose methodology)", "NIOSH"],
        "validation_status": "Direct implementation",
        "caveat": "Standard occupational noise-dose exchange-rate formula; criterion/exchange-rate default to "
                  "OSHA's 90 dBA/5 dB and switch to the stricter EU 85 dBA/3 dB variant via the regulatory "
                  "profile, not a second formula.",
    },
    {
        "function": "whole_body_vibration_a8()",
        "module": "Mining & Quarrying",
        "formula_summary": "A(8) = a_w * sqrt(T / 8h)",
        "cited_standards": ["ISO 2631-1", "EU Physical Agents (Vibration) Directive 2002/44/EC"],
        "validation_status": "Direct implementation",
        "caveat": "Standard daily-exposure normalization formula; action/limit values (0.5 / 1.15 m/s2) match "
                  "the EU Directive's published A(8) figures.",
    },
    {
        "function": "Silica / CO / PM2.5 OEL exceedance checks",
        "module": "Mining & Quarrying; Underground (Tunnel/Metro)",
        "formula_summary": "Direct comparison of a measured concentration against a published occupational "
                            "exposure limit",
        "cited_standards": ["OSHA 29 CFR 1926.1153 (respirable crystalline silica)", "ACGIH TLVs"],
        "validation_status": "Direct implementation",
        "caveat": "The limit values themselves are resolved per-jurisdiction via regulatory_country_thresholds "
                  "profiles, not hardcoded to one country's figure alone.",
    },
    {
        "function": "lee_arc_flash_incident_energy()",
        "module": "Data Center (reference implementation; not the one actually called by the module below)",
        "formula_summary": "IE = 2.142e3 * V(kV) * Isc(kA) * t(s) / D(mm)^2  [cal/cm2]",
        "cited_standards": ["Ralph Lee open-air arc-flash incident-energy approximation"],
        "validation_status": "Adapted / approximated",
        "caveat": "A widely-published order-of-magnitude screening method - explicitly NOT a substitute for a "
                  "full IEEE 1584 arc-flash study before authorizing live electrical work.",
    },
    {
        "function": "calculate_datacenter_kinetic_risk() arc_flash_energy_cal",
        "module": "Data Center (Controlled Critical Environment)",
        "formula_summary": "arc_flash_energy_cal = 2.5 * (electrical_load_kw / 100.0)^2 - a simplified, "
                            "load-only proxy, NOT the Lee formula above",
        "cited_standards": ["None - does not implement IEEE 1584 or the Ralph Lee formula"],
        "validation_status": "Illustrative (not standards-derived)",
        "caveat": "Uses a tuned illustrative coefficient because only electrical_load_kw is collected in this "
                  "MVP (not voltage/fault-current/clearing-time/working-distance). A genuine IEEE 1584 arc-flash "
                  "study - or lee_arc_flash_incident_energy() above, once those parameters are wired in - is "
                  "required before authorizing live work near this equipment. Do not cite this figure as an "
                  "IEEE 1584 or Ralph Lee result.",
    },
    {
        "function": "calculate_high_rise_kinetic_risk() scaled_wind_speed",
        "module": "High-Rise (Vertical Urban)",
        "formula_summary": "scaled_wind_speed = ground_wind_speed_knots * exp(0.008 * floor_level)",
        "cited_standards": ["None - not a certified structural wind-loading calculation"],
        "validation_status": "Illustrative (not standards-derived)",
        "caveat": "This file's own module-level docstring loosely describes this as a 'wind power-law profile', "
                  "but the implementation is an EXPONENTIAL growth curve, not the power-law form ASCE 7 / "
                  "Eurocode 1 atmospheric boundary-layer wind profiles actually use (v(z) = v_ref*(z/z_ref)^alpha). "
                  "This entry corrects that imprecision for auditors relying on this table: treat the wind-with-"
                  "height scaling as an illustrative screening heuristic, not a cited standard calculation.",
    },
    {
        "function": "corroded_capacity_pct()",
        "module": "Marine & Port Construction",
        "formula_summary": "remaining_capacity_pct = 100 - annual_derate_rate * years_in_service (linear)",
        "cited_standards": ["Loosely modeled on ISO 12944 exposure-category severity ordering (C3/C4/C5-M)"],
        "validation_status": "Illustrative (not standards-derived)",
        "caveat": "A simplified linear screening model for MVP purposes, not a substitute for a certified "
                  "structural/corrosion-engineering inspection - already documented as such at the point of use.",
    },
    {
        "function": "calculate_physiological_strain() max heart rate",
        "module": "Worker Physiology (Wearables)",
        "formula_summary": "HRmax = 208 - 0.7 * age",
        "cited_standards": ["Tanaka, Monahan & Seals (2001) age-predicted maximal heart rate formula"],
        "validation_status": "Direct implementation",
        "caveat": "A widely-cited, published epidemiological formula; individual max HR varies and this remains "
                  "a screening estimate, not a clinical stress-test result.",
    },
    {
        "function": "calculate_acoustic_noise_exposure() distance attenuation",
        "module": "Extended Air Quality / Noise",
        "formula_summary": "Inverse-square-law sound attenuation with distance, feeding into noise_dose_percent()",
        "cited_standards": ["Inverse-square law (acoustics physics)", "OSHA/NIOSH (via noise_dose_percent())"],
        "validation_status": "Direct implementation",
        "caveat": "Standard free-field point-source attenuation model; real sites with reflective surfaces or "
                  "barriers will deviate from the free-field assumption.",
    },
    {
        "function": "matrix_score() / matrix_band() / aggregate_risk_matrix() (risk_matrix.py)",
        "module": "All 9 modules - Risk Matrix Scoring Engine",
        "formula_summary": "Score = Likelihood (1-5) x Severity (1-5), range 1-25; Low 1-4/Moderate 5-9/"
                            "High 10-15/Extreme 16-25",
        "cited_standards": ["ISO 31010 (risk assessment techniques)", "Classic HSE-style 5x5 Likelihood x "
                             "Severity risk matrix convention"],
        "validation_status": "Direct implementation",
        "caveat": "The requested 1-4/5-9/10-15/16-25 bands are exactly the textbook cut-points a 5x5 matrix "
                  "produces, not a coincidentally-matching invented scale. Likelihood is derived deterministically "
                  "from margin-to-threshold (see risk_matrix.likelihood_from_margin()'s own docstring) since this "
                  "is a screening tool with no incident-frequency dataset - not a fitted probability model.",
    },
    {
        "function": "apply_controls_residual_risk() (risk_matrix.py)",
        "module": "All 9 modules - 2-stage residual risk workflow",
        "formula_summary": "Governing hazard's likelihood reduced by 1 point per applied control, floored at 1; "
                            "severity never reduced",
        "cited_standards": ["Hierarchy of controls (general HSE principle: administrative/PPE controls reduce "
                             "likelihood of harm, not inherent hazard severity)"],
        "validation_status": "Illustrative (not standards-derived)",
        "caveat": "The hierarchy-of-controls PRINCIPLE behind never reducing severity is standard HSE doctrine; "
                  "the specific '1 likelihood point per applied control' rule is this app's own conservative, "
                  "transparent screening choice, not a number drawn from any named standard - deliberately so, "
                  "since no empirical per-control effectiveness dataset exists here.",
    },
]


def get_formula_standard(function_name: str) -> dict | None:
    """Looks up one FORMULA_STANDARDS_MAP entry by (a substring of) its
    "function" field - case-insensitive, so a caller can pass either the
    bare function name (e.g. "humidex") or the fuller signature string
    stored above. Returns None (never raises) when nothing matches, so a
    caller can handle "no validation entry found" explicitly rather than
    getting a confusing empty dict."""
    needle = function_name.strip().lower()
    for entry in FORMULA_STANDARDS_MAP:
        if needle in entry["function"].lower():
            return entry
    return None


def get_all_formula_standards() -> list[dict]:
    """Returns the full FORMULA_STANDARDS_MAP - the no-argument counterpart
    to get_formula_standard(), matching risk_engine.get_stop_work_triggers()'s
    own "call with no filter to get everything" convention."""
    return list(FORMULA_STANDARDS_MAP)
    return None
