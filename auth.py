"""
MAKU - Authentication utility
==============================
A minimal login gate for app.py. Renders a centered French-language login
form ("Identifiant" / "Mot de passe" / "Se connecter") and blocks all
further script execution (st.stop()) until the credentials match.

Credential resolution order:
  1. st.secrets["auth"]["username"] / ["password"] - the production path.
     Configure these in Streamlit Cloud under App settings -> Secrets, or
     locally in a `.streamlit/secrets.toml` file that is NOT committed to
     git (see .streamlit/secrets.toml.example for the format; real secrets
     stay out of version control - .gitignore already excludes
     .streamlit/secrets.toml).
  2. A hardcoded fallback (admin / Maku2026!) - ONLY so the app still runs
     before secrets are configured. Anything hardcoded in a source file is
     visible to anyone who can read this repo, so replace the secrets
     before treating this as a real production credential.

This file only handles auth state - no risk math, no UI beyond the login
form itself.
"""

from __future__ import annotations

import os

import streamlit as st

_FALLBACK_USERNAME = "admin"
_FALLBACK_PASSWORD = "Maku2026!"


def _get_credentials() -> tuple[str, str]:
    try:
        return st.secrets["auth"]["username"], st.secrets["auth"]["password"]
    except Exception:
        return _FALLBACK_USERNAME, _FALLBACK_PASSWORD


def _using_fallback_credentials() -> bool:
    try:
        st.secrets["auth"]["username"]
        st.secrets["auth"]["password"]
        return False
    except Exception:
        return True


def require_login() -> None:
    """Call this as the very first thing app.py does. Returns immediately
    if already authenticated (st.session_state['authenticated'] is True).
    Otherwise renders the login form and st.stop()s the script - nothing
    after this call (module layout, sidebar nav, st.navigation, etc.) ever
    executes for an unauthenticated visitor."""
    if st.session_state.get("authenticated", False):
        return

    st.set_page_config(page_title="MAKU - Connexion", page_icon="🔒", layout="centered")

    st.markdown("<div style='height: 8vh'></div>", unsafe_allow_html=True)
    col_l, col_mid, col_r = st.columns([1, 1.3, 1])

    with col_mid:
        if os.path.exists("logo_croquis.png"):
            st.image("logo_croquis.png", width="stretch")

        st.markdown("### 🔒 MAKU — Accès sécurisé")
        st.caption("Plateforme d'évaluation des risques cinétiques multi-environnement")

        if _using_fallback_credentials():
            st.warning(
                "Identifiants de secours actifs (aucun secret configuré). "
                "À remplacer avant une mise en production réelle - voir "
                "`.streamlit/secrets.toml.example`.",
                icon="⚠️",
            )

        with st.form("login_form"):
            username = st.text_input("Identifiant")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", width="stretch")

        if submitted:
            valid_username, valid_password = _get_credentials()
            if username == valid_username and password == valid_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect.")

    st.stop()


def render_logout_control(st_module) -> None:
    """Small sidebar logout control. Call from the dashboard/pages once
    authenticated, if you want a visible way to sign out."""
    if st_module.sidebar.button("🔓 Se déconnecter"):
        st_module.session_state["authenticated"] = False
        st_module.rerun()
