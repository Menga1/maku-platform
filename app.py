"""
MAKU - Multi-Environment AI for Kinetic Risk Assessment
Main entry point / router.

Authentication gate (auth.require_login()) runs first, before anything
else in this file - no module layout, sidebar navigation, or dashboard
content is defined or executed for an unauthenticated visitor. See auth.py
for credential handling.

Uses Streamlit's explicit st.navigation() / st.Page() API (the modern,
officially supported multipage mechanism) instead of the older
folder-auto-discovery + st.sidebar page list. That older mechanism proved
unreliable in some deployment environments (pages not appearing, or
st.page_link raising KeyError against an incompletely-populated page
registry) - explicit registration here removes that failure mode entirely.

The dashboard/overview UI itself lives in render_dashboard() below; each
environment's assessment UI is still a separate file under pages/, and all
risk math still lives in risk_engine.py (never here).
"""

import os

import streamlit as st
from auth import require_login, render_logout_control
from i18n import t, language_selector
from ui_helpers import render_official_report, render_analytics_section

# ---------------------------------------------------------------------------
# Authentication gate - must be the first Streamlit-affecting call in this
# script. Every navigation event re-executes app.py from the top (that's
# how st.navigation/pg.run() dispatch works), so this check applies
# uniformly to the dashboard AND to all 5 module pages: there is no way to
# reach a module page without first passing this gate.
# ---------------------------------------------------------------------------
require_login()


def render_dashboard():
    """The landing/overview page. Must call st.set_page_config as its own
    first Streamlit command, exactly like every other page - with
    st.navigation, each page (function or file) is its own script run."""
    st.set_page_config(page_title="MAKU - Kinetic Risk Platform", page_icon="🛡️", layout="wide")

    # Brand assets. Expected at the project root, alongside app.py.
    LOGO_MODERNE_PATH = "logo_moderne.png"
    LOGO_CROQUIS_PATH = "logo_croquis.png"

    if os.path.exists(LOGO_CROQUIS_PATH):
        st.sidebar.image(LOGO_CROQUIS_PATH, width='stretch', caption="The Five Worlds of MAKU")

    lang = language_selector(st)

    st.sidebar.title(t("app_title", lang))
    st.sidebar.caption(t("app_tagline", lang))
    st.sidebar.markdown("---")
    render_logout_control(st)
    st.sidebar.markdown("---")

    if os.path.exists(LOGO_MODERNE_PATH):
        st.image(LOGO_MODERNE_PATH, width='stretch')

    st.title(t("app_title", lang))
    st.caption(t("app_tagline", lang))

    st.header(t("dashboard_intro_header", lang))
    st.write(t("dashboard_intro_body", lang))

    st.subheader(t("dashboard_module_col_header", lang))

    st.sidebar.markdown("---")
    st.sidebar.caption(t("dashboard_footer", lang))
    render_official_report(
        st,
        result=st.session_state.get("latest_risk_result", {}),
        narrative=st.session_state.get("latest_ai_narrative", ""),
        controls=st.session_state.get("latest_controls", []),
        lang=lang,
    )

    st.markdown("---")
    render_analytics_section(st, lang)


# The dashboard is callable-backed so app.py is not executed recursively as
# a child page. The remaining pages are registered from their file paths.
pg = st.navigation([
    st.Page(render_dashboard, title="Dashboard", icon="🛡️", default=True),
    st.Page("pages/1_Solar_Farms.py", title="Solar Farms", icon="☀️"),
    st.Page("pages/2_Offshore_Oil_Gas.py", title="Offshore Oil & Gas", icon="🌊"),
    st.Page("pages/3_Metros_Tunnels.py", title="Metros & Tunnels", icon="🚇"),
    st.Page("pages/4_High_Rise.py", title="High Rise", icon="🏗️"),
    st.Page("pages/5_Data_Centers.py", title="Data Centers", icon="🏢"),
])
pg.run()
