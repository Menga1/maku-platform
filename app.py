"""MAKU Streamlit entrypoint and explicit page navigation."""

import os

import streamlit as st
from i18n import t, language_selector

st.set_page_config(page_title="MAKU - Kinetic Risk Platform", page_icon="🛡️", layout="wide")

# Brand assets. Expected at the project root, alongside app.py.
LOGO_MODERNE_PATH = "logo_moderne.png"
LOGO_CROQUIS_PATH = "logo_croquis.png"

def render_dashboard() -> None:
    """Render the landing page used as the navigation home page."""
    if os.path.exists(LOGO_CROQUIS_PATH):
        st.sidebar.image(LOGO_CROQUIS_PATH, width="stretch", caption="The Five Worlds of MAKU")

    lang = language_selector(st)
    st.sidebar.title(t("app_title", lang))
    st.sidebar.caption(t("app_tagline", lang))
    st.sidebar.markdown("---")

    if os.path.exists(LOGO_MODERNE_PATH):
        st.image(LOGO_MODERNE_PATH, width="stretch")

    st.title(t("app_title", lang))
    st.caption(t("app_tagline", lang))
    st.header(t("dashboard_intro_header", lang))
    st.write(t("dashboard_intro_body", lang))
    st.subheader(t("dashboard_module_col_header", lang))

    modules = [
        ("☀️", "solar_header", "solar_caption"),
        ("🌊", "offshore_header", "offshore_caption"),
        ("🚇", "underground_header", "underground_caption"),
        ("🏙️", "highrise_header", "highrise_caption"),
        ("🖥️", "datacenter_header", "datacenter_caption"),
    ]
    cols = st.columns(len(modules))
    for col, (icon, header_key, caption_key) in zip(cols, modules):
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


pages = [
    st.Page(render_dashboard, title="Dashboard", icon="🏠", default=True),
    st.Page("pages/01_Solar.py", title="Solar (Desert)", icon="☀️"),
    st.Page("pages/02_Offshore.py", title="Offshore (Marine)", icon="🌊"),
    st.Page("pages/03_Underground.py", title="Underground (Tunnel/Metro)", icon="🚇"),
    st.Page("pages/04_High_Rise.py", title="High-Rise (Vertical Urban)", icon="🏙️"),
    st.Page("pages/05_Data_Center.py", title="Data Center", icon="🖥️"),
]

navigation = st.navigation(pages)
navigation.run()
