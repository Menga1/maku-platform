"""
MAKU translations beyond i18n.STRINGS.

Each supported language (except English, the source language) has its own
module here - translations/<code>.py - exposing up to three dictionaries:

    UI      {i18n key: text}     fills keys that i18n.STRINGS has no entry
                                 for in that language (i18n.t() looks here
                                 before falling back), plus the sidebar page
                                 names (keys "page_*").
    ENGINE  {English text: text} the risk engine's own vocabulary: driver
                                 table labels, primary hazards, risk bands,
                                 and control recommendations.
    ENGINE_TEMPLATES {pattern key: text with {0}, {1}...}
                                 translations of the few engine sentences
                                 that embed a computed value (see
                                 ENGINE_PATTERNS below).

The risk engine itself keeps producing English - its strings are the
audited, test-pinned vocabulary - and translation happens only at display
time, through engine() / drivers_table() below. Anything without a
translation is shown in English, never in another language.
"""

from __future__ import annotations

import importlib
import re
from functools import lru_cache

# Engine sentences that embed a computed value. The captured groups are
# re-inserted into the translated template; a captured group that is itself
# a known engine string (e.g. a wind status) is translated too.
ENGINE_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("wind_status", re.compile(r"^Wind risk status: (.+)$")),
    ("noise_dose", re.compile(
        r"^Noise dose at (.+?)% of the permissible 8-hour limit - mandatory hearing protection, "
        r"reduce continuous exposure duration, isolate/enclose plant noise sources where feasible$")),
    ("splash_zone", re.compile(
        r"^Splash-zone hardware estimated at (.+?)% of rated capacity - schedule a certified structural "
        r"inspection before continued use; consider derating safe working load$")),
    ("arc_flash_ppe", re.compile(r"^Arc-flash PPE for energized work: (.+) \(source: (.+)\)$")),
    ("work_rest", re.compile(
        r"^Adopt a (.+?) work/rest cycle to stay within the ACGIH TLV action limit for this workload "
        r"category and clothing ensemble$")),
]


@lru_cache(maxsize=None)
def _module(lang: str):
    if not lang or lang == "en" or not re.fullmatch(r"[a-z]{2}", lang):
        return None
    try:
        return importlib.import_module(f"translations.{lang}")
    except ImportError:
        return None


def ui(key: str, lang: str) -> str | None:
    """Interface string for an i18n key, or None when this language has none."""
    mod = _module(lang)
    return getattr(mod, "UI", {}).get(key) if mod else None


def engine(text, lang: str):
    """Translate one piece of risk-engine vocabulary for display. Returns
    the input unchanged when it is not a string, the language is English,
    or no translation exists."""
    if not isinstance(text, str):
        return text
    mod = _module(lang)
    if mod is None:
        return text
    table = getattr(mod, "ENGINE", {})
    if text in table:
        return table[text]
    templates = getattr(mod, "ENGINE_TEMPLATES", {})
    for key, pattern in ENGINE_PATTERNS:
        match = pattern.match(text)
        if match and key in templates:
            parts = [engine(g, lang) for g in match.groups()]
            return templates[key].format(*parts)
    return text


def engine_list(items, lang: str) -> list:
    return [engine(item, lang) for item in (items or [])]


def drivers_table(drivers: dict, lang: str, yes: str = "Yes", no: str = "No") -> dict:
    """The 'Environmental drivers' table with labels and text values
    translated. Booleans are shown as the localized yes/no."""
    out = {}
    for key, value in (drivers or {}).items():
        if isinstance(value, bool):
            shown = yes if value else no
        elif isinstance(value, str):
            shown = engine(value, lang)
        else:
            shown = str(value)
        out[engine(key, lang)] = shown
    return out


def inline(fr_text: str, en_text: str, lang: str) -> str:
    """For interface text written directly in the code as a French/English
    pair: French for "fr", otherwise the language's translation of the
    English text (translations/<lang>.py INLINE), else English."""
    if lang == "fr":
        return fr_text
    mod = _module(lang)
    if mod is not None:
        found = getattr(mod, "INLINE", {}).get(en_text)
        if found is not None:
            return found
    return en_text
