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
        {"region": "Australia", "body": "Safe Work Australia", "doc": "Managing the risks of working in heat - Code of Practice", "url": "https://www.safeworkaustralia.gov.au"},
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
}


def get_library_topic(module: str) -> str:
    return MODULE_LIBRARY_TOPICS.get(module, "occupational safety and health engineering")
