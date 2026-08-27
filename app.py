"""
MAKU - Multi-Environment AI for Kinetic Risk Assessment
Main dashboard entry point. Per project structure, this file only hosts the
landing/overview page - each environment's assessment UI lives in its own
file under pages/, and all risk math lives in risk_engine.py (never here).
"""

import os

import streamlit as st
from i18n import t, language_selector

st.set_page_config(page_title="MAKU - Kinetic Risk Platform", page_icon="🛡️", layout="wide")

# Brand assets. Expected at the project root, alongside app.py.
LOGO_MODERNE_PATH = "logo_moderne.png"
LOGO_CROQUIS_PATH = "logo_croquis.png"

# ---------------------------------------------------------------------------
# Sidebar - brand mark, then language selector (persists via session_state
# across every page), then the rest of the shared shell.
# ---------------------------------------------------------------------------
if os.path.exists(LOGO_CROQUIS_PATH):
    st.sidebar.image(LOGO_CROQUIS_PATH, use_container_width=True, caption="The Five Worlds of MAKU")

lang = language_selector(st)

st.sidebar.title(t("app_title", lang))
st.sidebar.caption(t("app_tagline", lang))
st.sidebar.markdown("---")
st.sidebar.caption(t("env_inputs_note", lang))

# ---------------------------------------------------------------------------
# Main dashboard
# ---------------------------------------------------------------------------
if os.path.exists(LOGO_MODERNE_PATH):
    st.image(LOGO_MODERNE_PATH, use_container_width=True)

st.title(t("app_title", lang))
st.caption(t("app_tagline", lang))

st.header(t("dashboard_intro_header", lang))
st.write(t("dashboard_intro_body", lang))

st.subheader(t("dashboard_module_col_header", lang))

MODULES = [
    ("☀️", "solar_header", "solar_caption"),
    ("🌊", "offshore_header", "offshore_caption"),
    ("🚇", "underground_header", "underground_caption"),
    ("🏙️", "highrise_header", "highrise_caption"),
    ("🖥️", "datacenter_header", "datacenter_caption"),
]

cols = st.columns(len(MODULES))
for col, (icon, header_key, caption_key) in zip(cols, MODULES):
    with col:
        st.markdown(f"### {icon}")
        st.markdown(f"**{t(header_key, lang).split(' - ')[0].lstrip(icon).strip()}**")
        st.caption(t(caption_key, lang))

st.info(
    "👈 " + (
        "Choisissez un module dans le menu de gauche pour lancer une évaluation."
        if lang == "fr"
        else "Pick a module from the left-hand menu to run an assessment."
    )
)

st.sidebar.markdown("---")
st.sidebar.caption(t("dashboard_footer", lang))
