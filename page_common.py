"""
MAKU - Shared Page Scaffolding for the 5 Module Pages
======================================================
Small helpers used by every file under pages/ so the boilerplate that has
nothing to do with a specific module's risk math (brand image, explicit
cross-page nav links, the Anthropic API key box, the ACGIH TLV reference
panel) isn't copy-pasted five times.

Mathematical Isolation rule still applies: render_acgih_reference_panel()
only *displays* the shared acgih_action_level()/wbgt_outdoor_approx()
helpers already defined in risk_engine.py - it doesn't compute a new
formula of its own, and it never feeds into any module's risk_band. It's
a supplementary cross-check panel, not part of the module's own verdict.
"""

from __future__ import annotations

import os

import streamlit as st

from i18n import t
from auth import render_logout_control
from risk_engine import wbgt_outdoor_approx, acgih_action_level

LOGO_CROQUIS_PATH = "logo_croquis.png"

# (page path, i18n nav key, icon) - single source of truth for the explicit
# page_link nav block repeated in every page's sidebar. Kept here rather than
# duplicated per-file so adding/renaming a page only touches one place.
NAV_ENTRIES = [
    ("app.py", "nav_dashboard", "🛡️"),
    ("pages/1_Solar_Farms.py", "nav_solar", "☀️"),
    ("pages/2_Offshore_Oil_Gas.py", "nav_offshore", "🌊"),
    ("pages/3_Metros_Tunnels.py", "nav_metros", "🚇"),
    ("pages/4_High_Rise.py", "nav_highrise", "🏙️"),
    ("pages/5_Data_Centers.py", "nav_datacenter", "🖥️"),
]


def render_page_sidebar_header(st_module, lang: str) -> None:
    """Brand image + explicit nav links + logout control. Call near the top
    of every module page, right after the language selector."""
    if os.path.exists(LOGO_CROQUIS_PATH):
        st_module.sidebar.image(LOGO_CROQUIS_PATH, width="stretch")

    st_module.sidebar.subheader(t("nav_header", lang))
    for page_path, nav_key, icon in NAV_ENTRIES:
        st_module.sidebar.page_link(page_path, label=t(nav_key, lang), icon=icon)

    st_module.sidebar.markdown("---")
    render_logout_control(st_module)
    st_module.sidebar.markdown("---")


def render_ai_layer_sidebar(st_module, lang: str) -> str:
    """The Anthropic API key box, shared verbatim across every page (same
    session_state key 'api_key' so the value the user enters on one page
    is still there after navigating to another)."""
    st_module.sidebar.subheader(t("ai_layer_header", lang))
    return st_module.sidebar.text_input(
        t("api_key_label", lang),
        type="password",
        help=t("api_key_help", lang),
        key="api_key",
    )


def render_acgih_reference_panel(st_module, lang: str, ambient_temp: float, relative_humidity: float) -> None:
    """Optional ACGIH TLV work/rest reference cross-check, shown alongside
    (never instead of) a module's own risk band. Every heat-driven module
    (Solar, Offshore, Underground) has its own independent band thresholds
    already - this panel just answers the separate, commonly-asked
    question 'does this also exceed the ACGIH action limit for our current
    work/rest cadence', using the WBGT approximation already defined in
    risk_engine.py."""
    with st_module.expander("ACGIH TLV" + (" - Référence" if lang == "fr" else " - Reference Check")):
        col1, col2 = st_module.columns(2)
        with col1:
            work_rate = st_module.selectbox(
                t("work_rate_label", lang),
                options=["light", "moderate", "heavy"],
                format_func=lambda v: t(f"wr_{v}", lang),
                index=1,
                key="acgih_work_rate",
            )
        with col2:
            work_rest = st_module.selectbox(
                t("work_rest_label", lang),
                options=["100/0", "75/25", "50/50", "25/75"],
                help=t("work_rest_help", lang),
                key="acgih_work_rest",
            )
        wbgt = wbgt_outdoor_approx(ambient_temp, relative_humidity)
        action = acgih_action_level(wbgt, work_rate, work_rest)
        st_module.metric("WBGT (approx.)", f"{wbgt:.1f} °C")
        exceeded_label = t("acgih_exceeded_label", lang)
        verdict = t("yes", lang) if action["exceeds"] else t("no", lang)
        st_module.write(
            f"**{exceeded_label}:** {verdict}  \n"
            f"{t('vs_limit', lang)} {action['limit']} °C "
            f"({'+' if action['margin'] >= 0 else ''}{action['margin']} °C)"
        )
