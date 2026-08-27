"""
MAKU - Shared UI helpers for the Manuel/Simulation <-> Automatique/Temps Reel
data mode switch. Used identically across all 5 pages/ modules so the
control always looks and behaves the same way.

UI only - no risk math here (Mathematical Isolation rule).
"""

from i18n import t


def render_data_mode_selector(st, lang: str, module_key: str) -> str:
    """Renders the "Mode d'Alimentation des Donnees" container at the top
    of the sidebar and returns "manual" or "auto"."""
    st.sidebar.markdown("### 🎛️ " + t("data_mode_header", lang))
    mode = st.sidebar.radio(
        t("data_mode_prompt", lang),
        options=["manual", "auto"],
        format_func=lambda v: t(f"data_mode_{v}", lang),
        key=f"data_mode_{module_key}",
    )
    st.sidebar.markdown("---")
    return mode


def render_stream_arm_toggle(st, lang: str, module_key: str, label: str) -> bool:
    """Renders the module-specific telemetry-stream toggle (only meaningful
    when the general mode above is 'auto'). Returns whether the stream is
    armed."""
    return st.checkbox(f"📡 {label}", key=f"stream_armed_{module_key}", value=False)


def render_feed_ok_banner(st, lang: str, source: str, fetched_at: str) -> None:
    st.success(f"🟢 {t('feed_live_badge', lang)} · {source} · {t('feed_last_update', lang)}: {fetched_at}")


def render_feed_error_banner(st, lang: str, detail: str) -> None:
    st.error(f"⚠️ {t('feed_error_banner', lang)}\n\n`{detail}`")


def render_stream_not_armed_note(st, lang: str) -> None:
    st.info(t("feed_not_armed_note", lang))
