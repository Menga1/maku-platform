"""
MAKU - Global Regulatory Profile Database
===========================================
A country-keyed database of HSE numeric thresholds, designed to be passed
into risk_engine.py's calculation functions as a `regulatory_profile` dict
so the SAME physics/engineering formula (WBGT, Humidex, wind-shear
amplification, arc-flash energy...) gets classified against the correct
jurisdiction's limits, instead of one hardcoded global table.

NAMING NOTE: this file is intentionally NOT named regulatory_references.py.
That name is already used by a different, still-critical module in this
codebase - a copyright-safe CITATION list (standards body names, document
titles, URLs) that ai_advisor.py's narrative and the official PDF report
both depend on for their "Regulatory References" section. Overwriting it
would have silently broken the PDF report and the AI briefing's regulatory-
basis line. This file covers NUMERIC THRESHOLDS; regulatory_references.py
covers CITATIONS. They're deliberately separate concerns.

HONESTY PRINCIPLE - READ BEFORE EXTENDING THIS FILE:
Most HSE numeric limits are internationally harmonized or near-universal.
ACGIH TLVs in particular are referenced almost worldwide, including by
UAE's OSHAD-SF and (via ISO 7243) France's INRS guidance. Faking country-
specific variation on an already-harmonized figure would be worse than not
having the feature, because it would look precise while being wrong. Every
category below either (a) cites a genuine, documented divergence, or
(b) explicitly says "defers to the harmonized default" rather than
inventing a plausible-looking national number that doesn't actually exist
in that country's published guidance.

GLOBAL EXPANSION NOTE (UK / Canada / Australia / fallback):
This file was extended to cover 3 additional baseline jurisdictions plus an
explicit "no profile registered yet" fallback path. The same honesty
principle above governs every number added:
  - UK: HSE does not publish a distinct statutory WBGT heat-stress table
    (it assesses thermal comfort qualitatively under the general duty in
    the Management of Health and Safety at Work Regulations 1999), so UK
    heat_stress uses the harmonized ACGIH profile as its numeric cross-
    check - same treatment as USA/UAE. What UK genuinely and distinctly
    publishes are COSHH Workplace Exposure Limits (HSE EH40/2005, 2020
    update) - respirable crystalline silica WEL of 0.1 mg/m3 (100 ug/m3)
    8-hr TWA, and the Control of Noise at Work Regulations 2005 action
    values (80/85 dBA lower/upper exposure action values, 3 dB exchange
    rate) - both real, citable, and genuinely different from the harmonized
    default. Crane wind speed has no UK statutory figure either (same
    OEM/load-chart deferral as OSHA) - shown in both knots and mph since UK
    site anemometry commonly reports in mph.
  - Canada: OHS is provincially regulated: CNESST (Quebec) is used here as
    the representative baseline, not a claim that all provinces share
    identical figures. Canada's genuine, well-documented divergence is
    Environment and Climate Change Canada's HUMIDEX heat-stress index
    (a fundamentally different formula/method than WBGT, not just a
    different number) with a published "Danger" threshold at Humidex >= 45,
    used here as the critical safety cutoff - plus ECCC's Wind Chill Index
    for cold-stress screening, genuinely absent from every other profile in
    this file since it's the only baseline jurisdiction where sub-zero
    working conditions are a routine site reality.
  - Australia: Safe Work Australia's model WHS Regulations are implemented
    per state/territory, so heat_stress again uses the harmonized ACGIH
    cross-check (no single national WBGT figure). Australia's genuine
    divergences: the Bureau of Meteorology / Cancer Council SunSmart UV
    Index action scale (sun-protection controls required from UV Index 3
    upward), a 2020 national Workplace Exposure Standard for respirable
    crystalline silica (0.05 mg/m3 = 50 ug/m3, stricter than the harmonized
    default), a national noise exposure standard of 85 dB(A) LAeq,8h at a
    3 dB exchange rate, an ambient PM2.5 standard under the National
    Environment Protection (Ambient Air Quality) Measure (2021 variation)
    used as the "bushfire smoke" ambient reference, and the model WHS
    Regulations' isolated-worker "effective communication system"
    requirement (s.48-49) - encoded here as a periodic check-in
    requirement, not a numeric exposure limit.
  - GLOBAL fallback: when GPS auto-detects a real country that has no
    profile registered in REGULATORY_PROFILES yet, the app falls back to
    this explicit "GLOBAL" entry (identical numbers to the harmonized
    USA/ACGIH/OSHA profile, but labeled as a fallback) rather than silently
    reusing "USA" - so the UI can tell the user honestly that no local
    profile exists yet, instead of implying a USA-specific determination
    was made.

Documented divergences actually modeled here:
  - Heat stress: ACGIH TLV (USA) vs ISO 7243 reference values (France/EU,
    via INRS) use genuinely different table structures, not just different
    numbers - ACGIH indexes by work/rest cycle, ISO 7243 by continuous
    metabolic-rate class. UAE's OSHAD-SF references ACGIH-style TLVs
    itself, so it uses the harmonized ACGIH profile PLUS its own distinct
    and much more consequential rule: a statutory midday outdoor-work ban
    (a hard calendar/clock rule, not a WBGT number).
  - Crane wind-shear: no country in this file has a specific *statutory*
    wind-speed number for crane operation - all three defer to
    manufacturer/OEM load-chart limits in practice (OSHA, Code du Travail,
    and UAE codes all use general duty-of-care language here, not a fixed
    number). What genuinely differs is EU/France's common EN 13000
    practice of mandating anemometer-linked automatic cutout systems on
    cranes above a given capacity - a real, citable difference in
    equipment practice, modeled here as a modestly more conservative
    default suspend threshold for France, clearly flagged as reflecting a
    common equipment-standard convention rather than a single statutory
    number.
  - Air quality: occupational OEL (enclosed-space PM2.5/CO limits used by
    the Underground module) has no widely-published country-specific
    PM2.5-only figure in any of these three jurisdictions - it stays at
    the harmonized default. AMBIENT PM2.5 (used for outdoor-worker general
    context) genuinely differs: US EPA NAAQS 24-hr standard is a real,
    stable, long-standing figure; the EU/France Directive 2008/50/EC limit
    value is a real figure but with a DIFFERENT averaging period (annual,
    not 24-hr) - these are not directly comparable, and the code below
    keeps that averaging-period distinction explicit rather than silently
    presenting two numbers as equivalent. UAE's ambient PM2.5 standard is
    not confidently sourced from memory here, so it explicitly defers to
    the WHO Air Quality Guideline value rather than inventing a number.
"""

from __future__ import annotations

from datetime import date

# ---------------------------------------------------------------------------
# THRESHOLD CLASSIFICATION SYSTEM
# ---------------------------------------------------------------------------
# Every numeric threshold this module hands to the UI sits somewhere on a
# spectrum from "this is codified law" to "this is a number MAKU made up so
# the screen isn't blank". Showing all of them the same way invites exactly
# the mistake this system exists to prevent: a user treating a MAKU
# screening default as if it were a statutory limit they could be cited
# against, or skipping a real legal requirement because it looked the same
# as a rule of thumb. Every threshold gets tagged with exactly one of the
# five categories below, and the UI (see ui_helpers.render_regulatory_badge)
# renders that tag as a visible, color-coded badge next to the number.
#
# CATEGORY_LEGAL_REQUIREMENT: a number written into a statute, regulation,
#   directive, or ministerial resolution that has the force of law in the
#   jurisdiction shown - e.g. OSHA 29 CFR limits, EU Directives transposed
#   into national law, HSE Statutory Instruments, CNESST's RSST.
# CATEGORY_STANDARD: a number published by a recognized standards body or
#   industry-consensus reference (ACGIH, ISO) that regulators commonly point
#   to, but which is not itself primary legislation in every jurisdiction
#   that uses it.
# CATEGORY_GUIDANCE: a number from official but non-binding guidance - a
#   government agency's classification scale, a recommended (not mandated)
#   practice, or an international body's guideline (e.g. WHO) that has not
#   been adopted into local law.
# CATEGORY_SITE_OEM_REQUIREMENT: the regulator explicitly defers to
#   manufacturer/OEM documentation or site-specific procedure for this
#   figure (most crane wind-speed limits fall here) - MAKU's displayed
#   number is a placeholder, and the real, authoritative limit is the
#   load chart or site procedure the crew is required to consult.
# CATEGORY_MAKU_SCREENING_VALUE: MAKU's own harmonized illustrative default,
#   used only because no country-specific or authoritative figure is
#   registered for that jurisdiction/topic - explicitly NOT a citation of
#   any regulator, standards body, or manufacturer document.
#
# See _THRESHOLD_CATEGORY_TABLE below for the topic-by-topic classification
# and the reasoning summary attached to each entry.
CATEGORY_LEGAL_REQUIREMENT = "LEGAL_REQUIREMENT"
CATEGORY_STANDARD = "STANDARD"
CATEGORY_GUIDANCE = "GUIDANCE"
CATEGORY_SITE_OEM_REQUIREMENT = "SITE_OEM_REQUIREMENT"
CATEGORY_MAKU_SCREENING_VALUE = "MAKU_SCREENING_VALUE"

# Display metadata for each category - the exact bracketed label text is a
# fixed UI requirement; color/icon are used by ui_helpers.render_regulatory_
# badge() to render a small, consistently-colored HTML badge. Ordered from
# "most authoritative" to "least authoritative" so a legend can list them in
# a meaningful order.
THRESHOLD_CATEGORY_META: dict[str, dict[str, str]] = {
    CATEGORY_LEGAL_REQUIREMENT: {
        "label": "[LEGAL REQUIREMENT]",
        "color": "#8b1e1e",
        "bg": "#fdeaea",
        "icon": "⚖️",
        "description": "Codified in a statute, regulation, directive, or ministerial "
                        "resolution with the force of law in the jurisdiction shown.",
    },
    CATEGORY_STANDARD: {
        "label": "[STANDARD]",
        "color": "#1e4e8b",
        "bg": "#eaf1fd",
        "icon": "📘",
        "description": "Published by a recognized standards body or industry-consensus "
                        "reference (e.g. ACGIH, ISO) commonly used by regulators, but not "
                        "itself primary legislation everywhere it is applied.",
    },
    CATEGORY_GUIDANCE: {
        "label": "[GUIDANCE]",
        "color": "#1e7a5f",
        "bg": "#e9f8f2",
        "icon": "🧭",
        "description": "Official but non-binding guidance - an agency classification "
                        "scale, recommended practice, or international guideline not "
                        "adopted into local law.",
    },
    CATEGORY_SITE_OEM_REQUIREMENT: {
        "label": "[SITE/OEM REQUIREMENT]",
        "color": "#8a5a00",
        "bg": "#fdf3e1",
        "icon": "🔧",
        "description": "The regulator explicitly defers to manufacturer/OEM "
                        "documentation or site-specific procedure - MAKU's number is a "
                        "placeholder; consult the load chart / site procedure.",
    },
    CATEGORY_MAKU_SCREENING_VALUE: {
        "label": "[MAKU SCREENING VALUE]",
        "color": "#555555",
        "bg": "#f0f0f0",
        "icon": "🧪",
        "description": "MAKU's own harmonized illustrative default, used only because no "
                        "country-specific or authoritative figure is registered here - "
                        "NOT a citation of any regulator, standard, or manufacturer.",
    },
}

# (country_code, topic) -> category. "GLOBAL" acts as the fallback used for
# any country code not otherwise listed in REGULATORY_PROFILES (mirrors
# get_regulatory_profile()'s own fallback behavior). Topics mirror the
# sub-sections/fields actually shown in the UI - see ui_helpers.
# render_regulatory_badge() and its call sites in app.py.
_THRESHOLD_CATEGORY_TABLE: dict[tuple[str, str], str] = {
    # heat_stress: the WBGT/Humidex action limit shown in the ACGIH/ISO7243/
    # Humidex reference panel on every module page.
    ("USA", "heat_stress"): CATEGORY_STANDARD,               # ACGIH TLV, referenced by OSHA enforcement guidance
    ("FRANCE", "heat_stress"): CATEGORY_STANDARD,             # ISO 7243, per INRS guidance
    ("UAE", "heat_stress"): CATEGORY_STANDARD,                # OSHAD-SF references ACGIH-style TLVs directly
    ("UK", "heat_stress"): CATEGORY_MAKU_SCREENING_VALUE,     # HSE publishes no numeric table; ACGIH used as MAKU's cross-check
    ("CANADA", "heat_stress"): CATEGORY_GUIDANCE,             # ECCC Humidex classification, referenced by provincial guidance
    ("AUSTRALIA", "heat_stress"): CATEGORY_MAKU_SCREENING_VALUE,  # SWA publishes no national WBGT table; ACGIH used as cross-check
    ("GLOBAL", "heat_stress"): CATEGORY_MAKU_SCREENING_VALUE,  # explicit "no profile registered" fallback

    # wind_shear: crane suspend/restrict wind speed. Every profile in this
    # file says the same thing - no statutory number exists, real authority
    # is the crane's own OEM load chart.
    ("USA", "wind_shear"): CATEGORY_SITE_OEM_REQUIREMENT,
    ("FRANCE", "wind_shear"): CATEGORY_SITE_OEM_REQUIREMENT,
    ("UAE", "wind_shear"): CATEGORY_SITE_OEM_REQUIREMENT,
    ("UK", "wind_shear"): CATEGORY_SITE_OEM_REQUIREMENT,
    ("CANADA", "wind_shear"): CATEGORY_SITE_OEM_REQUIREMENT,
    ("AUSTRALIA", "wind_shear"): CATEGORY_SITE_OEM_REQUIREMENT,
    ("GLOBAL", "wind_shear"): CATEGORY_SITE_OEM_REQUIREMENT,

    # air_quality_ambient: the outdoor/ambient PM2.5 figure (extended air
    # quality + bushfire-smoke panels).
    ("USA", "air_quality_ambient"): CATEGORY_LEGAL_REQUIREMENT,      # EPA NAAQS, 40 CFR Part 50
    ("FRANCE", "air_quality_ambient"): CATEGORY_LEGAL_REQUIREMENT,   # EU Directive 2008/50/EC, transposed into French law
    ("UAE", "air_quality_ambient"): CATEGORY_GUIDANCE,               # explicitly defers to the WHO AQG, not a UAE regulation
    ("UK", "air_quality_ambient"): CATEGORY_LEGAL_REQUIREMENT,       # Air Quality Standards Regulations 2010 (retained post-Brexit)
    ("CANADA", "air_quality_ambient"): CATEGORY_STANDARD,            # CAAQS 2020 (CCME-published national standard)
    ("AUSTRALIA", "air_quality_ambient"): CATEGORY_LEGAL_REQUIREMENT,  # National Environment Protection Measure (legislative instrument)
    ("GLOBAL", "air_quality_ambient"): CATEGORY_MAKU_SCREENING_VALUE,  # fallback reuse of the US NAAQS figure, no local citation

    # air_quality_occupational: the enclosed-space PM2.5/CO OEL figures -
    # every profile explicitly flags these as MAKU's harmonized default.
    ("USA", "air_quality_occupational"): CATEGORY_MAKU_SCREENING_VALUE,
    ("FRANCE", "air_quality_occupational"): CATEGORY_MAKU_SCREENING_VALUE,
    ("UAE", "air_quality_occupational"): CATEGORY_MAKU_SCREENING_VALUE,
    ("UK", "air_quality_occupational"): CATEGORY_MAKU_SCREENING_VALUE,
    ("CANADA", "air_quality_occupational"): CATEGORY_MAKU_SCREENING_VALUE,
    ("AUSTRALIA", "air_quality_occupational"): CATEGORY_MAKU_SCREENING_VALUE,
    ("GLOBAL", "air_quality_occupational"): CATEGORY_MAKU_SCREENING_VALUE,

    # noise: noise_criterion_dba / noise_exchange_rate_db.
    ("USA", "noise"): CATEGORY_LEGAL_REQUIREMENT,        # OSHA 29 CFR 1910.95
    ("FRANCE", "noise"): CATEGORY_LEGAL_REQUIREMENT,     # Code du Travail R4431-2, EU Directive 2003/10/EC
    ("UAE", "noise"): CATEGORY_MAKU_SCREENING_VALUE,     # harmonized default (no UAE-specific figure sourced)
    ("UK", "noise"): CATEGORY_LEGAL_REQUIREMENT,         # Control of Noise at Work Regulations 2005
    ("CANADA", "noise"): CATEGORY_LEGAL_REQUIREMENT,     # CNESST RSST
    ("AUSTRALIA", "noise"): CATEGORY_LEGAL_REQUIREMENT,  # SWA model WHS Regulations, adopted into law per state/territory
    ("GLOBAL", "noise"): CATEGORY_MAKU_SCREENING_VALUE,  # fallback reuse, no local citation

    # silica: silica_action_level_ugm3.
    ("USA", "silica"): CATEGORY_LEGAL_REQUIREMENT,        # OSHA 29 CFR 1926.1153 construction silica standard
    ("FRANCE", "silica"): CATEGORY_MAKU_SCREENING_VALUE,  # harmonized default
    ("UAE", "silica"): CATEGORY_MAKU_SCREENING_VALUE,     # harmonized default
    ("UK", "silica"): CATEGORY_LEGAL_REQUIREMENT,         # HSE EH40/2005 WEL, enforced under the COSHH Regulations
    ("CANADA", "silica"): CATEGORY_LEGAL_REQUIREMENT,     # CNESST RSST permissible exposure value
    ("AUSTRALIA", "silica"): CATEGORY_LEGAL_REQUIREMENT,  # SWA Workplace Exposure Standard, adopted per state/territory
    ("GLOBAL", "silica"): CATEGORY_MAKU_SCREENING_VALUE,  # fallback reuse, no local citation

    # uv_heat: SunSmart UV Index action scale (Australia only).
    ("AUSTRALIA", "uv_heat"): CATEGORY_GUIDANCE,

    # bushfire_smoke: the descriptive AQI banding shown in the bushfire-
    # smoke panel - explicitly documented as an illustrative mapping onto
    # state-published descriptive categories, not a single uniform national
    # AQI standard (Australia only).
    ("AUSTRALIA", "bushfire_smoke"): CATEGORY_GUIDANCE,

    # cold_stress: Environment Canada Wind Chill Index (Canada only).
    ("CANADA", "cold_stress"): CATEGORY_GUIDANCE,

    # remote_comms: isolated-worker check-in interval (Australia only) - the
    # DUTY is legal (WHS Reg s.48-49), but the specific 60-minute interval
    # is explicitly documented as common-practice guidance, not a fixed
    # statutory number, so the number itself is badged as guidance.
    ("AUSTRALIA", "remote_comms"): CATEGORY_GUIDANCE,

    # midday_ban: UAE's statutory midday outdoor-work break window.
    ("UAE", "midday_ban"): CATEGORY_LEGAL_REQUIREMENT,

    # air_quality_who_guideline: the general-purpose (every country)
    # extended air-quality panel screens PM2.5/PM10/O3/NO2 against the WHO
    # 2021 Global Air Quality Guidelines, not against any REGULATORY_
    # PROFILES country figure - a single GLOBAL entry so it classifies the
    # same way regardless of which country is active.
    ("GLOBAL", "air_quality_who_guideline"): CATEGORY_GUIDANCE,
}


def get_threshold_category(country_code: str, topic: str) -> str:
    """Returns one of the CATEGORY_* constants for a given (country, topic)
    pair. Falls back to the GLOBAL entry for that topic when the country
    isn't listed (mirrors get_regulatory_profile()'s own fallback), and
    falls back further to CATEGORY_MAKU_SCREENING_VALUE if even that isn't
    registered - an unclassified figure is always treated as the LEAST
    authoritative category by default, never silently presented as more
    authoritative than it's actually been verified to be."""
    return _THRESHOLD_CATEGORY_TABLE.get(
        (country_code, topic),
        _THRESHOLD_CATEGORY_TABLE.get(("GLOBAL", topic), CATEGORY_MAKU_SCREENING_VALUE),
    )


def get_threshold_category_badge(country_code: str, topic: str) -> dict:
    """Returns the full badge dict {"category", "label", "color", "bg",
    "icon", "description"} for a (country, topic) pair - everything
    ui_helpers.render_regulatory_badge() needs to draw the badge, with no
    knowledge of the classification table required on the caller's side."""
    category = get_threshold_category(country_code, topic)
    meta = dict(THRESHOLD_CATEGORY_META[category])
    meta["category"] = category
    return meta


# ---------------------------------------------------------------------------
# Heat stress: ACGIH TLV table (USA baseline / harmonized default, also used
# by UAE) vs ISO 7243 reference-value table (France/EU)
# ---------------------------------------------------------------------------
# ACGIH structure: WBGT (deg C) action limit per work_rate, indexed by
# work/rest ratio ["100/0", "75/25", "50/50", "25/75"], unacclimatized worker.
ACGIH_WBGT_LIMITS = {
    "light": [29.5, 30.5, 31.5, 32.5],
    "moderate": [27.5, 28.5, 29.5, 31.0],
    "heavy": [26.0, 27.5, 29.0, 30.5],
}

# ISO 7243 structure: a single WBGT reference value per metabolic-rate
# class, for CONTINUOUS work (no work/rest cycle axis) - genuinely a
# different table shape, not just different numbers. Values below are
# representative of the ISO 7243 reference-value approach for
# unacclimatized workers; treat as illustrative of the METHOD's structure
# rather than a guaranteed-current exact figure - always verify the
# current ISO 7243 edition before using this for a real compliance
# decision (same verification caveat regulatory_references.py already
# states for every citation in this app).
ISO7243_WBGT_REFERENCE_VALUES = {
    "light": 29.0,
    "moderate": 27.0,
    "heavy": 25.0,
}


def resolve_heat_stress_limit(profile: dict, work_rate: str, work_rest_ratio: str = "100/0") -> dict:
    """
    Returns {"limit": float, "method": str, "source_note": str} for the
    given profile's heat-stress method. ACGIH-method profiles use the
    work_rest_ratio axis; ISO7243-method profiles ignore it (continuous-
    work reference value); HUMIDEX-method profiles (Canada) ignore both
    work_rate and work_rest_ratio and return the profile's single published
    critical safety cutoff (Environment Canada's Humidex "Danger" threshold,
    45 by default) - Humidex is a public comfort/danger index, not a
    workload-indexed occupational table, so there is no genuine work-rate
    axis to apply here. Callers should not assume work_rate/work_rest_ratio
    always change the result.
    """
    heat = profile["heat_stress"]
    if heat["method"] == "HUMIDEX":
        limit = heat["critical_cutoff"]
    elif heat["method"] == "ISO7243":
        limit = heat["wbgt_reference_values"][work_rate]
    else:
        idx_map = {"100/0": 0, "75/25": 1, "50/50": 2, "25/75": 3}
        idx = idx_map.get(work_rest_ratio, 0)
        limit = heat["wbgt_limits"][work_rate][idx]
    return {"limit": limit, "method": heat["method"], "source_note": heat["source_note"]}


# ---------------------------------------------------------------------------
# Full per-country regulatory profiles
# ---------------------------------------------------------------------------
REGULATORY_PROFILES: dict[str, dict] = {
    "USA": {
        "label": "United States (OSHA / ACGIH)",
        "heat_stress": {
            "method": "ACGIH",
            "wbgt_limits": ACGIH_WBGT_LIMITS,
            "source_note": "ACGIH Threshold Limit Values (TLVs) for Heat Stress and Strain - "
                            "the reference used in OSHA enforcement guidance.",
        },
        "wind_shear": {
            "crane_suspend_knots": 30.0,
            "crane_restrict_knots": 22.0,
            "source_note": "No single OSHA statutory wind-speed number for crane operation - "
                            "29 CFR 1926 Subpart CC defers to manufacturer/OEM load-chart limits. "
                            "This value is MAKU's harmonized illustrative default, not a cited "
                            "OSHA figure.",
        },
        "air_quality": {
            "pm25_oel_ugm3": 250.0,   # harmonized default (see honesty note above)
            "co_oel_ppm": 25.0,       # harmonized default
            "pm25_ambient_ugm3": 35.0,
            "ambient_averaging_period": "24-hour",
            "source_note": "EPA National Ambient Air Quality Standard (NAAQS) for PM2.5, "
                            "24-hour standard (40 CFR Part 50). Occupational OEL figures above "
                            "are MAKU's harmonized default, not a distinct OSHA PM2.5-specific PEL.",
        },
        "noise_criterion_dba": 90.0,
        "noise_exchange_rate_db": 5.0,
        "silica_action_level_ugm3": 25.0,
        "midday_outdoor_work_ban": False,
    },
    "FRANCE": {
        "label": "France (Code du Travail / INRS)",
        "heat_stress": {
            "method": "ISO7243",
            "wbgt_reference_values": ISO7243_WBGT_REFERENCE_VALUES,
            "source_note": "ISO 7243 WBGT reference-value method, as referenced by INRS "
                            "(Institut National de Recherche et de Sécurité) guidance under the "
                            "Code du Travail's general heat-risk-assessment duty (Art. L4121-1).",
        },
        "wind_shear": {
            "crane_suspend_knots": 27.0,
            "crane_restrict_knots": 20.0,
            "source_note": "No single French statutory wind-speed number either - this reflects "
                            "the common EU/EN 13000 practice of anemometer-linked automatic crane "
                            "cutout systems, which is standard equipment practice in France/EU but "
                            "not a single fixed number in law (varies by crane model/capacity). "
                            "Modeled here as a modestly more conservative illustrative default than "
                            "the USA/UAE baseline, not a cited statutory threshold.",
        },
        "air_quality": {
            "pm25_oel_ugm3": 250.0,   # harmonized default
            "co_oel_ppm": 25.0,       # harmonized default
            "pm25_ambient_ugm3": 25.0,
            "ambient_averaging_period": "annual",
            "source_note": "EU Directive 2008/50/EC PM2.5 annual limit value - NOTE the different "
                            "averaging period (annual, not 24-hour) versus the US NAAQS figure; "
                            "these two numbers are not directly comparable on a like-for-like basis.",
        },
        "noise_criterion_dba": 85.0,      # EU Directive 2003/10/EC, Code du Travail R4431-2
        "noise_exchange_rate_db": 3.0,    # EU Directive 2003/10/EC
        "silica_action_level_ugm3": 25.0,  # harmonized default
        "midday_outdoor_work_ban": False,
        "source_note": "Code du Travail Art. R4431 et seq., transposing EU Directive 2003/10/EC",
    },
    "UAE": {
        "label": "United Arab Emirates (OSHAD-SF / MOHRE)",
        "heat_stress": {
            "method": "ACGIH",
            "wbgt_limits": ACGIH_WBGT_LIMITS,
            "source_note": "UAE's OSHAD-SF Heat Stress Management Code of Practice references "
                            "ACGIH-style TLVs directly rather than publishing a distinct numeric "
                            "table - so this uses the harmonized ACGIH profile. UAE's genuinely "
                            "distinct rule is the statutory midday outdoor-work ban below, which "
                            "is a hard calendar/clock rule layered on top of (not a replacement "
                            "for) the WBGT-based assessment.",
        },
        "wind_shear": {
            "crane_suspend_knots": 30.0,
            "crane_restrict_knots": 22.0,
            "source_note": "Same harmonized illustrative default as USA - ADOSH-SF's Working at "
                            "Height and Lifting Operations Code of Practice defers to "
                            "manufacturer/OEM limits, same as OSHA.",
        },
        "air_quality": {
            "pm25_oel_ugm3": 250.0,   # harmonized default
            "co_oel_ppm": 25.0,       # harmonized default
            "pm25_ambient_ugm3": 15.0,
            "ambient_averaging_period": "24-hour",
            "source_note": "No UAE-specific ambient PM2.5 standard is confidently sourced from "
                            "memory here, so this defers to the WHO 2021 Air Quality Guideline "
                            "24-hour value (a global reference, not a UAE-specific regulation) "
                            "rather than inventing a plausible-looking national figure.",
        },
        "noise_criterion_dba": 90.0,    # harmonized default
        "noise_exchange_rate_db": 5.0,  # harmonized default
        "silica_action_level_ugm3": 25.0,  # harmonized default
        "midday_outdoor_work_ban": True,
        "midday_ban_start_month": 6,   # June 15 - September 15, per UAE MOHRE Ministerial Resolution
        "midday_ban_start_day": 15,
        "midday_ban_end_month": 9,
        "midday_ban_end_day": 15,
        "midday_ban_start_hour": 12,   # 12:30
        "midday_ban_start_minute": 30,
        "midday_ban_end_hour": 15,     # 15:00
        "midday_ban_end_minute": 0,
        "source_note": "MOHRE Ministerial Resolution on midday outdoor work break "
                        "(annually renewed, mid-June to mid-September, 12:30-15:00)",
    },
    "UK": {
        "label": "United Kingdom (HSE / COSHH)",
        "heat_stress": {
            "method": "ACGIH",
            "wbgt_limits": ACGIH_WBGT_LIMITS,
            "source_note": "HSE does not publish a distinct statutory WBGT heat-stress "
                            "table - thermal risk is assessed qualitatively under the "
                            "Management of Health and Safety at Work Regulations 1999 "
                            "general duty (HSE 'thermal comfort' / working in high "
                            "temperatures guidance). This uses the harmonized ACGIH "
                            "profile as the numeric cross-check, same treatment as "
                            "USA/UAE.",
        },
        "wind_shear": {
            "crane_suspend_knots": 30.0,
            "crane_restrict_knots": 22.0,
            "crane_suspend_mph": round(30.0 * 1.15078, 1),
            "crane_restrict_mph": round(22.0 * 1.15078, 1),
            "source_note": "No UK statutory crane wind-speed figure either - LOLER/PUWER "
                            "defer to manufacturer/OEM load-chart limits, the same pattern "
                            "as OSHA. Harmonized illustrative default, shown in mph as well "
                            "as knots since UK site anemometry commonly reports in mph.",
        },
        "air_quality": {
            "pm25_oel_ugm3": 250.0,   # harmonized default
            "co_oel_ppm": 25.0,       # harmonized default
            "pm25_ambient_ugm3": 20.0,
            "ambient_averaging_period": "annual",
            "source_note": "Air Quality Standards Regulations 2010 (as retained post-Brexit) "
                            "PM2.5 annual mean exposure-reduction target - NOTE the annual "
                            "averaging period, not directly comparable to the US 24-hour "
                            "NAAQS figure elsewhere in this file.",
        },
        "noise_criterion_dba": 85.0,       # HSE upper exposure action value - mandatory hearing protection zone
        "noise_exchange_rate_db": 3.0,     # Control of Noise at Work Regulations 2005
        "noise_lower_action_dba": 80.0,
        "noise_upper_action_dba": 85.0,
        "noise_limit_value_dba": 87.0,     # exposure limit value (accounting for any hearing protection worn)
        "silica_action_level_ugm3": 100.0,  # HSE EH40/2005 WEL for respirable crystalline silica, 2020 update
        "dust_general_oel_mgm3": {"inhalable": 10.0, "respirable": 4.0},  # EH40/2005 dust (NOS) WELs
        "midday_outdoor_work_ban": False,
        "source_note": "HSE EH40/2005 Workplace Exposure Limits (5th edition, 2020 COSHH "
                        "update); Control of Noise at Work Regulations 2005.",
    },
    "CANADA": {
        "label": "Canada (OHS / CNESST)",
        "heat_stress": {
            "method": "HUMIDEX",
            "critical_cutoff": 45.0,
            "source_note": "Environment and Climate Change Canada Humidex classification. "
                            "CNESST (Quebec's provincial OHS regulator, used here as "
                            "Canada's representative baseline - OHS is provincially "
                            "regulated and other provinces/territories maintain their own, "
                            "broadly similar regulators) and other provincial guidance "
                            "reference Humidex-based heat-stress management. A Humidex of "
                            "45 or higher is ECCC's published 'Dangerous - heat stroke "
                            "possible' threshold, applied here as the critical safety "
                            "cutoff triggering mandatory work stoppage/rotation.",
        },
        "cold_stress": {
            "method": "WIND_CHILL",
            "formula": "WCI = 13.12 + 0.6215*T - 11.37*V^0.16 + 0.3965*T*V^0.16 "
                       "(T in deg C, V in km/h; valid for T <= 10C and V > 4.8 km/h)",
            "source_note": "Environment and Climate Change Canada Wind Chill Index and "
                            "hazard categories - the only baseline jurisdiction in this "
                            "file where sub-zero cold-stress conditions are a routine site "
                            "reality, so this is the only profile carrying a cold_stress "
                            "section.",
        },
        "wind_shear": {
            "crane_suspend_knots": 30.0,
            "crane_restrict_knots": 22.0,
            "source_note": "No Canadian federal or provincial statutory crane wind-speed "
                            "figure - same OEM/load-chart deferral pattern as OSHA. "
                            "Harmonized illustrative default.",
        },
        "air_quality": {
            "pm25_oel_ugm3": 250.0,   # harmonized default
            "co_oel_ppm": 25.0,       # harmonized default
            "pm25_ambient_ugm3": 27.0,
            "ambient_averaging_period": "24-hour",
            "source_note": "Canadian Ambient Air Quality Standard (CAAQS) 2020, PM2.5 "
                            "24-hour standard (Canadian Council of Ministers of the "
                            "Environment / Environment and Climate Change Canada).",
        },
        "noise_criterion_dba": 90.0,      # CNESST RSST criterion, harmonized with OSHA's figure
        "noise_exchange_rate_db": 5.0,
        "silica_action_level_ugm3": 100.0,  # CNESST RSST permissible exposure value, RCS (quartz)
        "midday_outdoor_work_ban": False,
        "source_note": "CNESST Reglement sur la sante et la securite du travail (RSST) - "
                        "Quebec's provincial OHS regulator, used as Canada's representative "
                        "baseline in this app; other provinces/territories maintain their "
                        "own OHS regulators with broadly similar but not identical figures.",
    },
    "AUSTRALIA": {
        "label": "Australia (Safe Work Australia)",
        "heat_stress": {
            "method": "ACGIH",
            "wbgt_limits": ACGIH_WBGT_LIMITS,
            "source_note": "Safe Work Australia's model Work Health and Safety Regulations "
                            "are implemented per state/territory and do not publish a single "
                            "national statutory WBGT table, so this uses the harmonized "
                            "ACGIH profile as the numeric cross-check, same treatment as "
                            "USA/UAE/UK.",
        },
        "uv_heat": {
            "uv_index_bands": [
                (2.9, "Low"), (5.9, "Moderate"), (7.9, "High"),
                (10.9, "Very High"), (999.0, "Extreme"),
            ],
            "action_at_or_above_uv_index": 3,
            "source_note": "Bureau of Meteorology / Cancer Council Australia SunSmart UV "
                            "Index scale. Safe Work Australia's 'Managing the risks of "
                            "working in heat' and SunSmart workplace guidance trigger "
                            "mandatory sun-protection controls (shade, clothing, sunscreen, "
                            "scheduling) from UV Index 3 upward.",
        },
        "wind_shear": {
            "crane_suspend_knots": 30.0,
            "crane_restrict_knots": 22.0,
            "source_note": "No single Australian national statutory crane wind-speed "
                            "figure - same OEM/load-chart deferral pattern as OSHA. "
                            "Harmonized illustrative default.",
        },
        "air_quality": {
            "pm25_oel_ugm3": 250.0,   # harmonized default
            "co_oel_ppm": 25.0,       # harmonized default
            "pm25_ambient_ugm3": 25.0,
            "ambient_averaging_period": "24-hour",
            "bushfire_smoke_aqi_bands": [
                (8.9, "Good"), (25.9, "Fair"), (50.9, "Poor"),
                (100.9, "Very Poor"), (999.0, "Hazardous"),
            ],
            "source_note": "National Environment Protection (Ambient Air Quality) Measure, "
                            "2021 variation, PM2.5 24-hour standard (25 ug/m3). The "
                            "'bushfire smoke' banding above is an illustrative mapping onto "
                            "the descriptive AQI categories several Australian state health "
                            "departments publish during smoke events - exact category "
                            "cut-points vary state to state, so treat these as "
                            "representative screening bands, not a single uniform national "
                            "AQI standard.",
        },
        "noise_criterion_dba": 85.0,   # SWA model WHS Regulations exposure standard, LAeq,8h
        "noise_exchange_rate_db": 3.0,
        "silica_action_level_ugm3": 50.0,  # SWA Workplace Exposure Standard for RCS, 2020
        "midday_outdoor_work_ban": False,
        "remote_comms": {
            "required": True,
            "check_in_interval_minutes": 60,
            "source_note": "Safe Work Australia model Work Health and Safety Regulations "
                            "2011, s.48-49 (isolated/remote workers) - an effective means of "
                            "communication must be maintained; a periodic check-in is common "
                            "practice guidance, not a single fixed statutory interval.",
        },
        "source_note": "Safe Work Australia model Work Health and Safety Regulations 2011; "
                        "state/territory WHS regulators implement and enforce locally.",
    },
    "GLOBAL": {
        "label": "Global ACGIH / OSHA Reference Guidelines (Fallback)",
        "heat_stress": {
            "method": "ACGIH",
            "wbgt_limits": ACGIH_WBGT_LIMITS,
            "source_note": "No country-specific regulatory profile is registered for this "
                            "location yet - falling back to the internationally-referenced "
                            "ACGIH Threshold Limit Values used as the harmonized default "
                            "throughout this app.",
        },
        "wind_shear": {
            "crane_suspend_knots": 30.0,
            "crane_restrict_knots": 22.0,
            "source_note": "Harmonized illustrative default (same as the USA baseline) - "
                            "no local crane wind-speed figure is registered for this "
                            "location.",
        },
        "air_quality": {
            "pm25_oel_ugm3": 250.0,
            "co_oel_ppm": 25.0,
            "pm25_ambient_ugm3": 35.0,
            "ambient_averaging_period": "24-hour",
            "source_note": "US EPA NAAQS 24-hour PM2.5 standard, used as the global "
                            "reference figure in the absence of a registered local profile.",
        },
        "noise_criterion_dba": 90.0,
        "noise_exchange_rate_db": 5.0,
        "silica_action_level_ugm3": 25.0,
        "midday_outdoor_work_ban": False,
        "is_fallback": True,
        "source_note": "No country-specific regulatory profile is registered for this GPS "
                        "location yet. MAKU has fallen back to the harmonized global "
                        "ACGIH/OSHA reference guidelines used elsewhere in this app as the "
                        "safest documented default - this is NOT a determination that "
                        "ACGIH/OSHA is the legally applicable framework at this location; "
                        "verify and select the correct local framework manually.",
    },
}

# Shown as a warning toast whenever a GPS auto-detected country resolves to a
# real, real-world jurisdiction that simply isn't registered in
# REGULATORY_PROFILES yet, so the "GLOBAL" fallback above is applied instead
# of silently guessing. Kept as a single exported constant (rather than
# re-typed at each call site) so app.py and data_feeds.py always show the
# identical, exact wording.
FALLBACK_WARNING_MESSAGE = (
    "Local legislation profile not found. Falling back to Global ACGIH/OSHA "
    "reference guidelines."
)
FALLBACK_COUNTRY_CODE = "GLOBAL"

# Backward-compatible name some earlier code and callers use.
COUNTRY_OVERRIDES = REGULATORY_PROFILES
COUNTRY_LABELS = {code: cfg["label"] for code, cfg in REGULATORY_PROFILES.items()}
DEFAULT_COUNTRY_CODE = "USA"


def get_regulatory_profile(country_code: str) -> dict:
    """
    Returns the full regulatory profile dict for a country code. Unknown
    codes fall back to the USA harmonized baseline rather than raising - a
    missing/unrecognized country selection (or a GPS point outside all
    three known jurisdictions) should degrade to the safest documented
    default, not break the app.
    """
    profile = REGULATORY_PROFILES.get(country_code, REGULATORY_PROFILES[DEFAULT_COUNTRY_CODE])
    # Return a shallow copy with country_code guaranteed present, so callers
    # can always read profile["country_code"] regardless of lookup outcome.
    resolved = dict(profile)
    resolved["country_code"] = country_code if country_code in REGULATORY_PROFILES else DEFAULT_COUNTRY_CODE
    return resolved


# Backward-compatible alias - app.py's Mining & Quarrying page (built in an
# earlier iteration) already calls get_country_thresholds(); keep it working
# unchanged rather than forcing every call site to migrate at once.
get_country_thresholds = get_regulatory_profile


def is_midday_outdoor_ban_active(country_code: str, check_date: date | None = None,
                                  check_hour: int | None = None, check_minute: int = 0) -> bool:
    """
    Evaluates the UAE-style statutory midday outdoor-work ban for the given
    country/date/time. Returns False immediately for any country without
    such a rule.
    """
    cfg = REGULATORY_PROFILES.get(country_code, {})
    if not cfg.get("midday_outdoor_work_ban"):
        return False

    check_date = check_date or date.today()
    in_season = (
        (check_date.month, check_date.day) >= (cfg["midday_ban_start_month"], cfg["midday_ban_start_day"])
    ) and (
        (check_date.month, check_date.day) <= (cfg["midday_ban_end_month"], cfg["midday_ban_end_day"])
    )
    if not in_season or check_hour is None:
        return in_season and check_hour is None  # season-only check when no time supplied

    start = (cfg["midday_ban_start_hour"], cfg["midday_ban_start_minute"])
    end = (cfg["midday_ban_end_hour"], cfg["midday_ban_end_minute"])
    now = (check_hour, check_minute)
    return in_season and start <= now <= end


# ---------------------------------------------------------------------------
# New-country feature helpers (UK / Canada / Australia)
# ---------------------------------------------------------------------------
# Deliberately thin data-lookup helpers only - see risk_engine.py for the
# actual formulas/classification functions (wind_chill_c, classify_humidex,
# classify_wind_chill, classify_uv_index, classify_bushfire_smoke_pm25).
# Mathematical Isolation rule: this file supplies NUMBERS/BANDS, never
# computes a risk formula itself.

def get_cold_stress_config(country_code: str) -> dict | None:
    """Returns the cold_stress config dict (formula/source_note) for a
    country, or None if that country's profile doesn't define one (every
    profile except Canada, currently)."""
    cfg = REGULATORY_PROFILES.get(country_code, {})
    return cfg.get("cold_stress")


def get_uv_heat_config(country_code: str) -> dict | None:
    """Returns the uv_heat config dict (uv_index_bands/source_note) for a
    country, or None if undefined (every profile except Australia,
    currently)."""
    cfg = REGULATORY_PROFILES.get(country_code, {})
    return cfg.get("uv_heat")


def get_bushfire_smoke_bands(country_code: str) -> list | None:
    """Returns the bushfire-smoke PM2.5 AQI band table for a country, or
    None if undefined (every profile except Australia, currently)."""
    cfg = REGULATORY_PROFILES.get(country_code, {})
    return cfg.get("air_quality", {}).get("bushfire_smoke_aqi_bands")


def get_remote_comms_config(country_code: str) -> dict | None:
    """Returns the remote/isolated-worker communication requirement config
    for a country, or None if undefined (every profile except Australia,
    currently)."""
    cfg = REGULATORY_PROFILES.get(country_code, {})
    return cfg.get("remote_comms")


def is_remote_comms_required(country_code: str) -> bool:
    """True if this country's profile requires a periodic remote/isolated-
    worker communication check-in (currently only Australia's Safe Work
    Australia isolated-worker rule)."""
    cfg = get_remote_comms_config(country_code)
    return bool(cfg and cfg.get("required"))


def is_fallback_profile(country_code: str) -> bool:
    """True only for the explicit GLOBAL fallback entry - used by the UI to
    decide whether to show the 'no local profile registered' warning."""
    return bool(REGULATORY_PROFILES.get(country_code, {}).get("is_fallback"))
