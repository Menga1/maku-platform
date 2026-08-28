"""
MAKU - Shared UI Helper Widgets
================================
Small, reusable Streamlit rendering helpers shared across app.py's dashboard
and all 5 module pages: the dashboard's tappable navigation cards, the
official HSE report (HTML preview + real PDF download), and the
"Manuel / Simulation" <-> "Automatique / Temps Reel" data-feed UI (mode
selector, live-feed status banners, and the simulated-stream arm toggle used
by Modules 3-5).

Mathematical Isolation rule still applies: this file only renders UI. It
never computes risk (risk_engine.py) and never fetches data itself
(data_feeds.py) - callers pass already-fetched values/labels in.

Regulatory references note: the report includes a "Regulatory References"
and "Further Reading" section sourced from regulatory_references.py. That
file cites real standards bodies and documents by name - it does not
reproduce their text, and neither does this file. See
regulatory_references.py's module docstring for why that boundary matters
here specifically (copyright + safety-critical accuracy).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from html import escape

from fpdf import FPDF

from i18n import t
from regulatory_references import (
    get_references,
    get_further_reading,
    get_free_library,
    google_books_search_url,
    get_library_topic,
)


def _pdf_safe(text: str) -> str:
    """fpdf2's core fonts (Helvetica) support the Latin-1/cp1252 character
    set, which covers French accents (e, a, c, etc.) but not emoji or other
    non-Latin symbols. Strip anything that can't be encoded rather than
    letting the PDF build crash on an emoji that made it into a control
    string or narrative."""
    return text.encode("latin-1", errors="ignore").decode("latin-1")


# ---------------------------------------------------------------------------
# Arabic PDF support
# ---------------------------------------------------------------------------
# The "Regulatory AI Narrative" section is the only part of the official
# report that's actually localized per-language (the rest of the report
# skeleton - headers, tables, controls, references - stays in English by
# design, matching the existing fr/en behavior). When lang="ar", that
# narrative paragraph is real Arabic text, which fpdf2's core Helvetica
# font cannot render at all (Helvetica only covers Latin-1). Rather than
# silently stripping it to blank/garbled text via _pdf_safe(), this section
# embeds a real Arabic-capable Unicode font (Noto Sans Arabic) and properly
# reshapes + bidi-reorders the text before handing it to fpdf2, which does
# not do Arabic letter-shaping or right-to-left reordering on its own.
#
# Font source: the "fonts-noto-core" Debian/Ubuntu package (see
# packages.txt at the repo root, which Streamlit Cloud installs via apt
# before the app starts). If that package isn't present for any reason,
# _arabic_fonts_available() returns False and the narrative safely falls
# back to the existing Latin-1-stripped rendering rather than crashing the
# PDF build.
_NOTO_SANS_REGULAR = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
_NOTO_SANS_BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
_NOTO_ARABIC_REGULAR = "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"
_NOTO_ARABIC_BOLD = "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf"


def _arabic_fonts_available() -> bool:
    return os.path.exists(_NOTO_SANS_REGULAR) and os.path.exists(_NOTO_ARABIC_REGULAR)


def _shape_arabic(text: str) -> str:
    """Reshape Arabic letters into their correct positional (initial/
    medial/final/isolated) forms and reorder the string for correct
    right-to-left visual display, per the Unicode Bidirectional Algorithm.
    Safe to call on any string, including pure Latin/English text or a
    mix of both (fpdf2 itself does neither of these transformations -
    it only draws glyphs in the order it's given)."""
    import arabic_reshaper
    from bidi.algorithm import get_display
    return get_display(arabic_reshaper.reshape(text))


def _build_report_pdf(
    result: dict,
    narrative: str,
    controls: list,
    references: list[dict],
    bibliography: list[dict],
    generated_at: str,
    lang: str,
) -> bytes:
    """Builds the actual downloadable PDF (not a browser print-to-PDF of the
    HTML view) using fpdf2, a pure-Python library with no system
    dependencies - safe to run on Streamlit Cloud."""
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Register the Arabic-capable font once, only when actually needed -
    # see the "Arabic PDF support" note above _pdf_safe() for why this is
    # scoped to the narrative section rather than the whole document.
    use_arabic_narrative = (lang == "ar") and _arabic_fonts_available()
    if use_arabic_narrative:
        pdf.add_font("NotoSans", "", _NOTO_SANS_REGULAR)
        pdf.add_font("NotoSans", "B", _NOTO_SANS_BOLD)
        pdf.add_font("NotoSansArabic", "", _NOTO_ARABIC_REGULAR)
        pdf.add_font("NotoSansArabic", "B", _NOTO_ARABIC_BOLD)
        pdf.set_fallback_fonts(["NotoSansArabic"])

    def h1(txt):
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(12, 92, 99)
        pdf.multi_cell(0, 10, _pdf_safe(txt), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

    def h2(txt):
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(12, 92, 99)
        pdf.multi_cell(0, 8, _pdf_safe(txt), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

    def body(txt):
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, _pdf_safe(txt), new_x="LMARGIN", new_y="NEXT")

    def kv_table(rows):
        pdf.set_font("Helvetica", "", 10)
        col1, col2 = 55, 130
        for key, value in rows:
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(col1, 6, _pdf_safe(str(key)), border=1, new_x="RIGHT", new_y="TOP")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(col2, 6, _pdf_safe(str(value)), border=1, new_x="LMARGIN", new_y="NEXT")

    def bullet_list(items):
        pdf.set_font("Helvetica", "", 10)
        for item in items:
            pdf.multi_cell(0, 6, _pdf_safe(f"- {item}"), new_x="LMARGIN", new_y="NEXT")

    h1("MAKU | Official HSE Site Report")
    body(f"Corporate / Project: {'_' * 40}")
    body(f"Site / Client: {'_' * 44}")
    body(f"Generated: {generated_at}")

    h2("Current Assessment")
    metric_rows = [(k, v) for k, v in result.items() if k != "drivers"]
    kv_table(metric_rows if metric_rows else [("-", "No assessment metrics supplied")])

    h2("Risk Drivers")
    driver_rows = list(result.get("drivers", {}).items())
    kv_table(driver_rows if driver_rows else [("-", "No driver details supplied")])

    h2("Regulatory AI Narrative")
    if use_arabic_narrative:
        pdf.set_font("NotoSans", "", 10)
        pdf.multi_cell(0, 6, _shape_arabic(narrative or "-"), align="R", new_x="LMARGIN", new_y="NEXT")
    else:
        body(narrative or "-")

    h2("Mitigation Action Plan")
    bullet_list(controls if controls else ["Review site controls before work starts."])

    h2("Regulatory References")
    body(
        "Applicable standards bodies and documents for this module. MAKU cites these "
        "by name and (where publicly available) links to the official source - it does "
        "not reproduce their text. Verify the current, jurisdiction-correct version "
        "before relying on it."
    )
    if references:
        for ref in references:
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 6, _pdf_safe(f"{ref['region']} - {ref['body']}"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, _pdf_safe(ref["doc"]), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 5, _pdf_safe(ref.get("url", "")), new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1)
    else:
        body("No module-specific references available.")

    h2("Further Reading")
    for entry in bibliography:
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 6, _pdf_safe(f"{entry['author']} - {entry['title']}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 5, _pdf_safe(f"{entry['publisher']}. {entry.get('note', '')}"), new_x="LMARGIN", new_y="NEXT")
        if entry.get("url"):
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 5, _pdf_safe(entry["url"]), new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

    h2("Formal HSE Sign-off")
    body(f"HSE Director: {'_' * 30}   Date: {'_' * 12}")
    body(f"Site Manager: {'_' * 30}   Date: {'_' * 12}")
    body("Conditions accepted / stop-work actions closed: " + "_" * 30)

    return bytes(pdf.output())


def render_official_report(
    st_module,
    result: dict | None = None,
    narrative: str = "",
    controls: list | None = None,
    lang: str = "fr",
) -> None:
    """Render the official HSE report: an HTML preview/download (unchanged
    from before) plus a genuine downloadable PDF (not a browser print of the
    HTML - an actual .pdf built with fpdf2), both including the module's
    regulatory references and a general bibliography."""
    result = result or {}
    controls = controls or []
    references = get_references(result.get("module", ""))
    bibliography = get_further_reading()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    metrics = "".join(
        f"<tr><th>{escape(str(key))}</th><td>{escape(str(value))}</td></tr>"
        for key, value in result.items()
        if key not in {"drivers"}
    )
    driver_rows = "".join(
        f"<tr><th>{escape(str(key))}</th><td>{escape(str(value))}</td></tr>"
        for key, value in result.get("drivers", {}).items()
    )
    controls_html = "".join(f"<li>{escape(str(control))}</li>" for control in controls)
    references_html = "".join(
        f"<li><strong>{escape(ref['region'])} - {escape(ref['body'])}:</strong> "
        f"{escape(ref['doc'])}"
        + (f' - <a href="{escape(ref["url"])}">{escape(ref["url"])}</a>' if ref.get("url") else "")
        + "</li>"
        for ref in references
    )
    bibliography_html = "".join(
        f"<li><strong>{escape(entry['author'])} - {escape(entry['title'])}</strong> "
        f"({escape(entry['publisher'])}). {escape(entry.get('note', ''))}"
        + (f' - <a href="{escape(entry["url"])}">{escape(entry["url"])}</a>' if entry.get("url") else "")
        + "</li>"
        for entry in bibliography
    )
    report_html = f"""<!doctype html>
<html lang="{escape(lang)}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MAKU - Official HSE Site Report</title>
<style>body{{font-family:Arial,sans-serif;max-width:860px;margin:0 auto;padding:24px;color:#17212b}}
h1{{color:#0c5c63}}table{{border-collapse:collapse;width:100%;margin:12px 0 24px}}
th,td{{border:1px solid #ccd5d8;padding:8px;text-align:left;vertical-align:top}}
th{{background:#edf3f3;width:36%}}.signoff{{margin-top:42px;border-top:2px solid #17212b;padding-top:16px}}
.refs-note{{font-size:0.85em;color:#4a5a5e;margin-bottom:8px}}
@media print{{body{{padding:0}}}}@media(max-width:600px){{body{{padding:14px;font-size:14px}}}}
</style></head><body><h1>MAKU | Official HSE Site Report</h1>
<p><strong>Corporate / Project:</strong> ______________________________</p>
<p><strong>Site / Client:</strong> ____________________________________</p>
<p><strong>Generated:</strong> {escape(generated_at)}</p>
<h2>Current Assessment</h2><table>{metrics or '<tr><td>No assessment metrics supplied</td></tr>'}</table>
<h2>Risk Drivers</h2><table>{driver_rows or '<tr><td>No driver details supplied</td></tr>'}</table>
<h2>Regulatory AI Narrative</h2><p>{escape(narrative).replace(chr(10), '<br>')}</p>
<h2>Mitigation Action Plan</h2><ul>{controls_html or '<li>Review site controls before work starts.</li>'}</ul>
<h2>Regulatory References</h2>
<p class="refs-note">Applicable standards bodies and documents for this module, cited by name with a link to the official source where publicly available. MAKU does not reproduce their text - verify the current, jurisdiction-correct version before relying on it.</p>
<ul>{references_html or '<li>No module-specific references available.</li>'}</ul>
<h2>Further Reading</h2><ul>{bibliography_html}</ul>
<div class="signoff"><h2>Formal HSE Sign-off</h2>
<p>HSE Director: ____________________ Date: __________</p>
<p>Site Manager: ____________________ Date: __________</p>
<p>Conditions accepted / stop-work actions closed: __________________________</p>
</div></body></html>"""

    st_module.markdown("### Official HSE Report")

    col_pdf, col_html = st_module.columns(2)
    with col_pdf:
        pdf_bytes = _build_report_pdf(result, narrative, controls, references, bibliography, generated_at, lang)
        st_module.download_button(
            "📄 Télécharger le PDF" if lang == "fr" else "📄 Download PDF",
            data=pdf_bytes,
            file_name="maku_official_hse_report.pdf",
            mime="application/pdf",
            width='stretch',
        )
    with col_html:
        st_module.download_button(
            "🌐 Télécharger le HTML" if lang == "fr" else "🌐 Download HTML",
            data=report_html,
            file_name="maku_official_hse_report.html",
            mime="text/html",
            width='stretch',
        )

    with st_module.expander("Aperçu imprimable / Print preview"):
        st_module.markdown(report_html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data-feed mode UI (Manuel/Simulation <-> Automatique/Temps Reel)
# ---------------------------------------------------------------------------

def render_data_mode_selector(st_module, lang: str, module_key: str) -> str:
    """Per-page sidebar radio choosing between manual sliders and the live/
    simulated feed. Returns 'manual' or 'auto'. State key is namespaced per
    module_key so each page's choice is independent."""
    st_module.sidebar.subheader(t("data_mode_header", lang))
    return st_module.sidebar.radio(
        t("data_mode_prompt", lang),
        options=["manual", "auto"],
        format_func=lambda v: t("data_mode_manual", lang) if v == "manual" else t("data_mode_auto", lang),
        key=f"data_mode_{module_key}",
        horizontal=True,
    )


def render_stream_arm_toggle(st_module, lang: str, module_key: str, label: str) -> bool:
    """Explicit 'arm the simulated sensor stream' checkbox for Modules 3-5
    (there's no keyless real-time API for those sensors, so this is an
    opt-in simulation rather than an automatic network call). Returns True
    once armed."""
    return st_module.checkbox(label, key=f"stream_armed_{module_key}", value=False)


def render_stream_not_armed_note(st_module, lang: str) -> None:
    """Shown when auto mode is selected but the simulated stream hasn't
    been armed yet - tells the user how to proceed."""
    st_module.info(t("feed_not_armed_note", lang))


def render_feed_ok_banner(st_module, lang: str, source: str, fetched_at) -> None:
    """Success banner shown once a live/simulated feed is actively
    supplying values (sliders are then disabled/read-only upstream)."""
    st_module.success(
        f"🟢 {t('feed_live_badge', lang)} — {source}  \n"
        f"{t('feed_last_update', lang)}: {fetched_at}"
    )


def render_feed_error_banner(st_module, lang: str, error_message: str) -> None:
    """Warning banner shown when a live/simulated feed failed and the page
    has safely reverted to manual sliders. The raw error is tucked behind
    an expander rather than shown inline, since it's a technical detail."""
    st_module.warning(t("feed_error_banner", lang))
    with st_module.expander("Technical details" if lang == "en" else "Détails techniques"):
        st_module.code(error_message)


# ---------------------------------------------------------------------------
# Virtual library (free HSE publications + Google Books search + web-search toggle)
# ---------------------------------------------------------------------------

def render_virtual_library(st_module, lang: str, module: str = "") -> None:
    """Renders the free/open-access HSE publication directory plus a Google
    Books search link for this module's topic. Links only - never fetches,
    caches, or displays reproduced book/publication content. See
    regulatory_references.py for the copyright/accuracy rationale."""
    st_module.markdown(
        "### 📚 " + ("Bibliothèque HSE" if lang == "fr" else "HSE Virtual Library")
    )
    st_module.caption(
        "Ressources gratuites et légalement accessibles. MAKU ne reproduit aucun "
        "contenu protégé - ces liens mènent aux sources officielles."
        if lang == "fr" else
        "Free, legally accessible resources. MAKU reproduces no copyrighted "
        "content - these links go to the official sources."
    )
    for entry in get_free_library():
        st_module.markdown(f"**{entry['body']}**  \n{entry['description']}  \n{entry['url']}")

    if module:
        topic = get_library_topic(module)
        books_url = google_books_search_url(topic)
        st_module.markdown(
            f"🔎 [{'Rechercher des ouvrages sur ce sujet (Google Books)' if lang == 'fr' else 'Search books on this topic (Google Books)'}]({books_url})"
        )

    st_module.caption(
        "Pour les ouvrages sous droits d'auteur (ex. Brauer, *Safety and Health "
        "for Engineers*), achetez-les ou consultez votre bibliothèque "
        "institutionnelle - voir la section Further Reading du rapport officiel."
        if lang == "fr" else
        "For copyrighted texts (e.g. Brauer's *Safety and Health for "
        "Engineers*), purchase them or check your institutional library - see "
        "the Further Reading section of the official report."
    )


def render_web_search_toggle(st_module, lang: str, module_key: str) -> bool:
    """Opt-in sidebar checkbox enabling Claude's live web_search tool for the
    AI narrative on this page. Off by default (extra API cost/latency).
    Reuses the same Anthropic API key already entered - no separate search
    API key needed."""
    return st_module.sidebar.checkbox(
        "🔎 Recherche légale en direct (coût API supplémentaire)"
        if lang == "fr" else
        "🔎 Live legislation search (extra API cost)",
        key=f"web_search_{module_key}",
        value=False,
        help=(
            "Autorise Claude à effectuer une recherche web en direct pour "
            "vérifier la réglementation applicable, en plus des références "
            "vérifiées ci-dessous. Utilise votre clé API existante."
            if lang == "fr" else
            "Lets Claude search the web live to check applicable legislation, "
            "on top of the verified references below. Uses your existing API key."
        ),
    )


# ---------------------------------------------------------------------------
# Trend analytics & monthly Excel export (see analytics.py for the
# persistence caveat - this is a session-scoped log, not a database)
# ---------------------------------------------------------------------------

def render_analytics_section(st_module, lang: str) -> None:
    """Dashboard section: session assessment log, an in-app trend chart,
    CSV download/merge for manual cross-session persistence, and a real
    downloadable monthly Excel report with an embedded chart."""
    from analytics import get_log_dataframe, monthly_summary, build_monthly_excel, merge_uploaded_csv

    st_module.markdown(
        "### 📊 " + ("Analyse des Tendances & Rapport Mensuel" if lang == "fr" else "Trend Analysis & Monthly Report")
    )
    st_module.caption(
        "Journal des évaluations de cette session uniquement (pas de base de "
        "données persistante sur Streamlit Cloud). Téléchargez le CSV "
        "régulièrement et réimportez-le lors d'une session future pour "
        "construire un historique multi-mois."
        if lang == "fr" else
        "This session's assessment log only (Streamlit Cloud has no "
        "persistent database). Download the CSV periodically and re-upload "
        "it in a future session to build a multi-month history."
    )

    uploaded = st_module.file_uploader(
        "Importer un journal précédent (CSV) pour fusionner" if lang == "fr"
        else "Upload a previous log (CSV) to merge",
        type=["csv"],
        key="analytics_csv_upload",
    )
    if uploaded is not None:
        try:
            added = merge_uploaded_csv(st_module, uploaded)
            st_module.success(
                (f"{added} nouvelle(s) ligne(s) fusionnée(s)." if lang == "fr"
                 else f"{added} new row(s) merged.")
            )
        except Exception as exc:
            st_module.error(f"{'Échec de la fusion' if lang == 'fr' else 'Merge failed'}: {exc}")

    df = get_log_dataframe(st_module)

    if df.empty:
        st_module.info(
            "Aucune évaluation enregistrée pour l'instant cette session - "
            "lancez une évaluation sur n'importe quel module pour commencer."
            if lang == "fr" else
            "No assessments logged yet this session - run an assessment on "
            "any module to start building the log."
        )
        return

    st_module.caption(f"{len(df)} " + ("évaluation(s) enregistrée(s) cette session" if lang == "fr" else "assessment(s) logged this session"))

    chart_data = df.groupby("module").size()
    st_module.bar_chart(chart_data)

    col_csv, col_xlsx = st_module.columns(2)
    with col_csv:
        st_module.download_button(
            "⬇️ Télécharger le journal (CSV)" if lang == "fr" else "⬇️ Download log (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="maku_assessment_log.csv",
            mime="text/csv",
            width='stretch',
        )
    with col_xlsx:
        st_module.download_button(
            "📊 Rapport Excel Mensuel" if lang == "fr" else "📊 Monthly Excel Report",
            data=build_monthly_excel(df),
            file_name="maku_monthly_trend_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width='stretch',
        )

    with st_module.expander("Résumé mensuel" if lang == "fr" else "Monthly summary"):
        st_module.dataframe(monthly_summary(df), width='stretch')


def render_meteorology_forecast(st_module, lang: str, forecast: dict, fields: list[tuple[str, str]]) -> None:
    """Small 7-day forecast trend chart for Solar/Offshore (the two modules
    with a real free forecast API). fields: list of (dict_key, display_label)
    pairs to plot as separate lines."""
    import pandas as pd

    st_module.caption(f"📡 {forecast.get('source', '')}")
    chart_df = pd.DataFrame({label: forecast[key] for key, label in fields}, index=forecast["dates"])
    st_module.line_chart(chart_df)
