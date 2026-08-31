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

XSS AUDIT (P0 "SECURITY EXPOSURE & AUDIT CONCURRENCY"): every
st.markdown(..., unsafe_allow_html=True) call site in this file was
re-audited for the v1.0 hardening pass. Result: every site interpolating
a value that can trace back to user input (the evidence-traceability
sensor/equipment free-text field, the AI narrative, hazard names/notes,
stop-work trigger/formula-standards table cells, regulatory badge labels)
already runs that value through html.escape() before interpolation - see
`from html import escape` below. The remaining unsafe_allow_html sites
render fixed, hardcoded HTML/CSS with no user-controlled interpolation at
all (the risk-matrix band legend colors, the arrow-transition divider, the
high-contrast-mode stylesheet). No gaps were found; this note documents
that the audit happened and what it covers, so a future addition of a new
unsafe_allow_html block has a standard to be checked against - any new one
MUST escape() every interpolated value that did not originate as a fixed,
hardcoded constant in this codebase.
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
    """fpdf2's core fonts (Helvetica) render an input str's codepoints
    0-255 using WinAnsiEncoding, which is cp1252, not plain Latin-1 - the
    two agree for French accented letters but cp1252 additionally covers
    "smart" punctuation the app's own copy uses (em dash, curly quotes),
    which plain Latin-1 silently drops. Round-tripping through cp1252
    first (encode) then Latin-1 (decode) maps each survivable character
    to the codepoint fpdf2's core-font table expects, so e.g. an em dash
    in a required-exact-wording disclaimer actually renders instead of
    vanishing. Anything outside cp1252 (emoji, non-Latin scripts) is
    still dropped rather than crashing the PDF build - see the Arabic
    narrative section below for the one place that needs more than this."""
    return text.encode("cp1252", errors="ignore").decode("latin-1")


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
    evidence: dict | None = None,
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

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(255, 244, 214)
    pdf.multi_cell(0, 6, _pdf_safe(HSE_DISCLAIMER_TEXT), border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    h2("Current Assessment")
    metric_rows = [(k, v) for k, v in result.items() if k not in ("drivers", "risk_matrix")]
    kv_table(metric_rows if metric_rows else [("-", "No assessment metrics supplied")])

    risk_matrix_lines = _risk_matrix_pdf_lines(result)
    if risk_matrix_lines:
        h2("Risk Matrix (Likelihood x Severity, 1-25)")
        for line in risk_matrix_lines:
            body(line)

    if evidence:
        h2("Evidence & Traceability")
        kv_table(list(evidence.items()))

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


# ---------------------------------------------------------------------------
# HSE decision-support disclaimer - required verbatim wording. This EXACT
# English string is the authoritative, legally-reviewed text and must
# never be paraphrased, shortened, or run through the i18n t()
# translation system (which is meant for ordinary UI copy, not a fixed
# compliance disclaimer). A French rendering is shown alongside it for
# readability when the interface language is French, clearly labeled as
# a convenience translation - the English text above it remains the
# authoritative version either way.
# ---------------------------------------------------------------------------
HSE_DISCLAIMER_TEXT = (
    "MAKU HSE Decision-Support System — Results are intended for risk "
    "screening and decision support and do not replace a competent "
    "person's assessment, engineering analysis, statutory requirement, "
    "manufacturer instruction or formal specialist study."
)

HSE_DISCLAIMER_TEXT_FR = (
    "Système d'aide à la décision HSE MAKU — Les résultats sont destinés "
    "au dépistage des risques et à l'aide à la décision et ne remplacent "
    "pas l'évaluation d'une personne compétente, une analyse technique, "
    "une exigence réglementaire, une instruction du fabricant ou une "
    "étude spécialisée formelle."
)


def render_hse_disclaimer(st_module, lang: str = "fr", compact: bool = False) -> None:
    """Renders the mandatory HSE decision-support disclaimer prominently.
    Call this on every calculation-result screen (every module page's
    result block, the dashboard, and both the HTML and PDF official
    reports render their own copy - see render_official_report() and
    _build_report_pdf() below).

    compact=True renders a single-line st.warning (for tight spaces, e.g.
    directly under a metrics row); compact=False (default) renders the
    fuller bordered container used at the top of a result screen. Either
    way the exact required English wording is always present and never
    altered."""
    if compact:
        st_module.warning(HSE_DISCLAIMER_TEXT, icon="⚠️")
        return

    with st_module.container(border=True):
        st_module.markdown(f"⚠️ **{HSE_DISCLAIMER_TEXT}**")
        if lang != "en":
            st_module.caption(HSE_DISCLAIMER_TEXT_FR if lang == "fr" else HSE_DISCLAIMER_TEXT)


# ---------------------------------------------------------------------------
# Regulatory threshold classification badges - see regulatory_country_
# thresholds.py's THRESHOLD CLASSIFICATION SYSTEM section for the category
# definitions and the topic-by-topic classification table this renders.
# Every numeric threshold shown anywhere in the app (heat-stress action
# limit, crane wind-shear, noise, silica, ambient/occupational air quality,
# UV index, cold stress, remote-worker check-in interval, the UAE midday
# ban) must be shown with one of these badges so a user can never mistake a
# MAKU screening default for a statutory limit, or vice-versa.
# ---------------------------------------------------------------------------
def render_regulatory_badge(st_module, country_code: str, topic: str, show_description: bool = True) -> None:
    """Renders a small color-coded badge (e.g. "⚖️ [LEGAL REQUIREMENT]")
    classifying the threshold about to be/just been shown, immediately
    next to it. show_description=True (default) also renders a one-line
    caption explaining what that category means, so a first-time user
    doesn't have to already know the classification system - set False for
    a denser repeated display (e.g. inside a table) once the meaning has
    already been shown once on the same screen."""
    # Local import - regulatory_country_thresholds already imports nothing
    # from ui_helpers, so this isn't circular, but keeping it local (rather
    # than a module-level import) avoids widening ui_helpers.py's import
    # surface for a single small helper, matching how render_official_
    # report() already imports analytics lazily just above.
    from regulatory_country_thresholds import get_threshold_category_badge

    badge = get_threshold_category_badge(country_code, topic)
    st_module.markdown(
        f"<span style='display:inline-block;padding:2px 8px;border-radius:10px;"
        f"font-size:0.78em;font-weight:700;color:{badge['color']};"
        f"background:{badge['bg']};border:1px solid {badge['color']}55;'>"
        f"{badge['icon']} {escape(badge['label'])}</span>",
        unsafe_allow_html=True,
    )
    if show_description:
        st_module.caption(badge["description"])


def render_regulatory_category_legend(st_module, lang: str = "fr") -> None:
    """Renders all 5 classification categories once, e.g. in a collapsed
    expander near the top of a page, so a user can look up what a badge
    they've seen elsewhere on the screen means without hunting for it."""
    from regulatory_country_thresholds import THRESHOLD_CATEGORY_META

    title = "Légende des seuils réglementaires" if lang == "fr" else "Regulatory threshold legend"
    with st_module.expander(f"ℹ️ {title}"):
        for meta in THRESHOLD_CATEGORY_META.values():
            st_module.markdown(
                f"<span style='display:inline-block;padding:2px 8px;border-radius:10px;"
                f"font-size:0.78em;font-weight:700;color:{meta['color']};"
                f"background:{meta['bg']};border:1px solid {meta['color']}55;'>"
                f"{meta['icon']} {escape(meta['label'])}</span> — {escape(meta['description'])}",
                unsafe_allow_html=True,
            )


def render_official_report(
    st_module,
    result: dict | None = None,
    narrative: str = "",
    controls: list | None = None,
    lang: str = "fr",
    evidence: dict | None = None,
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
        if key not in {"drivers", "risk_matrix"}
    )
    driver_rows = "".join(
        f"<tr><th>{escape(str(key))}</th><td>{escape(str(value))}</td></tr>"
        for key, value in result.get("drivers", {}).items()
    )
    risk_matrix_lines_html = _risk_matrix_pdf_lines(result)
    risk_matrix_section_html = (
        "<h2>Risk Matrix (Likelihood x Severity, 1-25)</h2><ul>"
        + "".join(f"<li>{escape(line)}</li>" for line in risk_matrix_lines_html)
        + "</ul>"
    ) if risk_matrix_lines_html else ""
    evidence_section_html = (
        "<h2>Evidence &amp; Traceability</h2><table>"
        + "".join(f"<tr><th>{escape(str(k))}</th><td>{escape(str(v))}</td></tr>" for k, v in evidence.items())
        + "</table>"
    ) if evidence else ""
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
.hse-disclaimer{{background:#fff4d6;border:1px solid #e0b64a;border-radius:6px;padding:12px 14px;
font-weight:600;margin:16px 0}}
@media print{{body{{padding:0}}}}@media(max-width:600px){{body{{padding:14px;font-size:14px}}}}
</style></head><body><h1>MAKU | Official HSE Site Report</h1>
<p><strong>Corporate / Project:</strong> ______________________________</p>
<p><strong>Site / Client:</strong> ____________________________________</p>
<p><strong>Generated:</strong> {escape(generated_at)}</p>
<div class="hse-disclaimer">⚠️ {escape(HSE_DISCLAIMER_TEXT)}</div>
<h2>Current Assessment</h2><table>{metrics or '<tr><td>No assessment metrics supplied</td></tr>'}</table>
{risk_matrix_section_html}
{evidence_section_html}
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
        pdf_bytes = _build_report_pdf(result, narrative, controls, references, bibliography, generated_at, lang,
                                       evidence=evidence)
        pdf_clicked = st_module.download_button(
            "📄 Télécharger le PDF" if lang == "fr" else "📄 Download PDF",
            data=pdf_bytes,
            file_name="maku_official_hse_report.pdf",
            mime="application/pdf",
            width='stretch',
        )
    with col_html:
        html_clicked = st_module.download_button(
            "🌐 Télécharger le HTML" if lang == "fr" else "🌐 Download HTML",
            data=report_html,
            file_name="maku_official_hse_report.html",
            mime="text/html",
            width='stretch',
        )

    if pdf_clicked or html_clicked:
        # Audit trail: report generation is one of the security-relevant
        # actions this deployment must record (see analytics.py's
        # AUDIT_EVENT_REPORT_GENERATED). Best-effort only - a failure here
        # must never block the download the operator already has in hand.
        try:
            import analytics as _analytics
            actor = st_module.session_state.get("_auth_username", "unknown")
            fmt = "PDF" if pdf_clicked else "HTML"
            _analytics.log_audit_event(
                _analytics.AUDIT_EVENT_REPORT_GENERATED, actor=actor,
                detail=f"{fmt} report - module: {result.get('module', '')}",
            )
        except Exception:  # noqa: BLE001
            pass

    with st_module.expander("Aperçu imprimable / Print preview"):
        st_module.markdown(report_html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Risk matrix transparency panel (Likelihood x Severity, 1-25)
# ---------------------------------------------------------------------------
# HSE audit corrective action: the scoring methodology must be fully
# transparent, the exact formula displayed, hardcoded numerical band
# thresholds must be visible in the UI, and individual hazards must be
# scored/rated/displayed separately before aggregation. This panel is the
# UI half of that requirement - risk_engine.py's risk_matrix.py module (the
# math half) supplies the already-computed, already-tested numbers; this
# function only renders them. Purely additive/defensive: does nothing if a
# result has no "risk_matrix" key (e.g. an empty/legacy session-state
# result), so it never breaks an existing page.

RISK_MATRIX_BAND_ROWS = [
    ("Low", "1 - 4", "#2e7d32"),
    ("Moderate", "5 - 9", "#f2b705"),
    ("High", "10 - 15", "#e07b00"),
    ("Extreme / Critical", "16 - 25", "#c0392b"),
]


def render_risk_matrix_breakdown(st_module, result: dict | None, lang: str = "fr") -> None:
    """Renders the transparent Likelihood x Severity risk-matrix breakdown
    for one module's already-computed result: the exact scoring formula,
    the hardcoded band thresholds, a per-hazard table (each hazard scored
    and rated individually, per the audit requirement), and the aggregated
    overall score/band with the governing (worst) hazard named. No-ops
    gracefully when result is empty or predates this feature (no
    "risk_matrix" key) - purely additive, never blocks an existing page."""
    result = result or {}
    risk_matrix = result.get("risk_matrix")
    if not risk_matrix or not risk_matrix.get("hazards"):
        return

    heading = "Matrice de risque (transparence du calcul)" if lang == "fr" else "Risk Matrix (calculation transparency)"
    formula_label = "Formule : Score = Probabilité (1-5) x Gravité (1-5)" if lang == "fr" \
        else "Formula: Score = Likelihood (1-5) x Severity (1-5)"

    with st_module.expander(heading, expanded=False):
        st_module.caption(formula_label)

        band_html = "".join(
            f'<span style="display:inline-block;margin:2px 6px 2px 0;padding:3px 9px;border-radius:4px;'
            f'background:{color};color:#fff;font-size:0.82em;font-weight:600;">{escape(label)}: {escape(rng)}</span>'
            for label, rng, color in RISK_MATRIX_BAND_ROWS
        )
        st_module.markdown(band_html, unsafe_allow_html=True)

        hazard_rows = "".join(
            f"<tr><td>{escape(str(h.get('name', '')))}</td>"
            f"<td style='text-align:center'>{escape(str(h.get('likelihood', '')))}</td>"
            f"<td style='text-align:center'>{escape(str(h.get('severity', '')))}</td>"
            f"<td style='text-align:center'><strong>{escape(str(h.get('score', '')))}</strong></td>"
            f"<td>{escape(str(h.get('band', '')))}</td>"
            f"<td style='font-size:0.85em;color:#4a5a5e'>{escape(str(h.get('note', '')))}</td></tr>"
            for h in risk_matrix.get("hazards", [])
        )
        header = (
            "<tr><th>Aléa</th><th>Probabilité</th><th>Gravité</th><th>Score</th><th>Bande</th><th>Note</th></tr>"
            if lang == "fr" else
            "<tr><th>Hazard</th><th>Likelihood</th><th>Severity</th><th>Score</th><th>Band</th><th>Note</th></tr>"
        )
        table_html = (
            "<table style='width:100%;border-collapse:collapse;margin-top:8px'>"
            "<style>th,td{border:1px solid #ccd5d8;padding:6px 8px;text-align:left}"
            "th{background:#edf3f3}</style>"
            f"{header}{hazard_rows}</table>"
        )
        st_module.markdown(table_html, unsafe_allow_html=True)

        overall_label = "Score global (pire aléa)" if lang == "fr" else "Overall score (worst hazard governs)"
        col_score, col_band, col_gov = st_module.columns(3)
        col_score.metric(overall_label, f"{risk_matrix.get('overall_score', 0)} / 25")
        col_band.metric("Bande" if lang == "fr" else "Band", str(risk_matrix.get("overall_band", "")))
        col_gov.metric(
            "Aléa dominant" if lang == "fr" else "Governing hazard",
            str(risk_matrix.get("governing_hazard", "-")),
        )


# ---------------------------------------------------------------------------
# 2-stage risk workflow: Initial Risk -> Applied Controls -> Residual Risk
# ---------------------------------------------------------------------------
# HSE audit corrective action. Mathematical Isolation rule still applies:
# this file only renders the controls-applied selector and displays the
# initial-vs-residual comparison a caller (app.py) computed via
# risk_matrix.apply_controls_residual_risk() - it never computes the
# residual score itself.

def render_applied_controls_selector(st_module, controls: list, lang: str = "fr", key_suffix: str = "") -> list:
    """Renders a multiselect of the module's own AI-advisor control
    recommendations (get_controls(result) - the exact same list shown in
    the Mitigation Action Plan, so there is only one control list in the
    whole system, never a second, disconnected one) and returns the
    subset the user has marked as actually applied on site. Returns []
    when there are no controls to select from (no-op, never errors)."""
    controls = controls or []
    if not controls:
        return []
    label = "Contrôles appliqués sur site" if lang == "fr" else "Controls applied on site"
    help_text = (
        "Sélectionnez les mesures ci-dessus réellement mises en œuvre pour calculer le risque résiduel."
        if lang == "fr" else
        "Select which of the controls above have actually been implemented, to calculate residual risk."
    )
    return st_module.multiselect(
        label, options=controls, default=[], help=help_text,
        key=f"applied_controls_{key_suffix}",
    )


def render_residual_risk_comparison(st_module, initial_matrix: dict | None, residual_matrix: dict | None,
                                     lang: str = "fr") -> None:
    """Displays the Initial Risk -> Applied Controls -> Residual Risk
    comparison: the two aggregate_risk_matrix()-shaped dicts side by side,
    plus the explicit, non-fabricated methodology note (residual risk
    reduces LIKELIHOOD only, never severity - see
    risk_matrix.apply_controls_residual_risk()'s own docstring for the
    full reasoning). No-ops when either matrix is missing/empty."""
    if not initial_matrix or not initial_matrix.get("hazards") or not residual_matrix:
        return
    heading = "Risque initial -> Contrôles appliqués -> Risque résiduel" if lang == "fr" \
        else "Initial Risk -> Applied Controls -> Residual Risk"
    st_module.markdown(f"#### {heading}")

    col_initial, col_arrow, col_residual = st_module.columns([5, 1, 5])
    with col_initial:
        st_module.caption("Risque initial" if lang == "fr" else "Initial risk")
        st_module.metric("Score", f"{initial_matrix.get('overall_score', 0)} / 25",
                          help=str(initial_matrix.get("overall_band", "")))
        st_module.write(f"**{initial_matrix.get('overall_band', '')}**")
    with col_arrow:
        st_module.markdown("<div style='text-align:center;font-size:1.6em;padding-top:22px'>&rarr;</div>",
                            unsafe_allow_html=True)
    with col_residual:
        st_module.caption("Risque résiduel" if lang == "fr" else "Residual risk")
        delta = residual_matrix.get("overall_score", 0) - initial_matrix.get("overall_score", 0)
        st_module.metric("Score", f"{residual_matrix.get('overall_score', 0)} / 25",
                          delta=delta, delta_color="inverse",
                          help=str(residual_matrix.get("overall_band", "")))
        st_module.write(f"**{residual_matrix.get('overall_band', '')}**")

    n_applied = residual_matrix.get("controls_applied_count", 0)
    reduction = residual_matrix.get("likelihood_reduction_applied", 0)
    if n_applied > 0:
        st_module.caption(
            (f"{n_applied} contrôle(s) appliqué(s) - réduction de probabilité de {reduction} point(s) sur l'aléa "
             f"dominant. La gravité n'est jamais réduite par des contrôles administratifs/EPI - seule une mesure "
             f"d'ingénierie/élimination/substitution le justifierait.")
            if lang == "fr" else
            (f"{n_applied} control(s) applied - likelihood reduced by {reduction} point(s) on the governing "
             f"hazard. Severity is never reduced by administrative/PPE controls alone - only an engineering/"
             f"elimination/substitution measure would justify that.")
        )
    else:
        st_module.caption(
            "Aucun contrôle sélectionné - le risque résiduel est identique au risque initial."
            if lang == "fr" else
            "No controls selected yet - residual risk equals initial risk."
        )


def _risk_matrix_pdf_lines(result: dict) -> list[str]:
    """Plain-text rendering of the risk_matrix breakdown for the PDF report
    (Task: comprehensive PDF audit traceability - the matrix that's shown
    on-screen must also be captured in the exported/archived report, not
    just the live UI). Returns a list of lines; empty list if no
    risk_matrix is present, so callers can skip the section cleanly."""
    risk_matrix = (result or {}).get("risk_matrix")
    if not risk_matrix or not risk_matrix.get("hazards"):
        return []
    lines = [
        "Formula: Score = Likelihood (1-5) x Severity (1-5). Bands: Low 1-4, "
        "Moderate 5-9, High 10-15, Extreme/Critical 16-25.",
    ]
    for h in risk_matrix["hazards"]:
        lines.append(
            f"- {h.get('name', '')}: Likelihood {h.get('likelihood', '')} x "
            f"Severity {h.get('severity', '')} = {h.get('score', '')} ({h.get('band', '')})"
            + (f" - {h.get('note', '')}" if h.get("note") else "")
        )
    lines.append(
        f"Overall: {risk_matrix.get('overall_score', 0)}/25 ({risk_matrix.get('overall_band', '')}) "
        f"- governing hazard: {risk_matrix.get('governing_hazard', '-')}"
    )
    return lines


# ---------------------------------------------------------------------------
# Stop-Work Trigger Registry panel
# ---------------------------------------------------------------------------
# HSE audit corrective action: safety override trigger thresholds must be
# explicitly defined/documented and visible. risk_engine.STOP_WORK_TRIGGERS
# (via get_stop_work_triggers()) is the single source of truth; this file
# only renders it. Purely additive/read-only display - never influences
# any module's own safety_override/override_required computation.

def render_stop_work_trigger_registry(st_module, triggers: list[dict], lang: str = "fr",
                                       expanded: bool = False) -> None:
    """Renders the Stop-Work Trigger Registry (or a module-filtered subset
    of it, per risk_engine.get_stop_work_triggers()) as a table: which
    hazard, the exact documented threshold, and the named source constant
    in code it comes from - so a supervisor or auditor can see precisely
    why a stop-work condition fired (or would fire) without reading
    risk_engine.py's source. No-ops gracefully on an empty/None list."""
    if not triggers:
        return
    heading = "Registre des seuils d'arrêt de travail" if lang == "fr" else "Stop-Work Trigger Registry"
    with st_module.expander(heading, expanded=expanded):
        st_module.caption(
            "Seuils numériques exacts qui déclenchent un arrêt de travail obligatoire (safety_override), "
            "avec la constante nommée du code d'où provient chaque seuil."
            if lang == "fr" else
            "The exact numeric thresholds that force a mandatory stop-work condition (safety_override), "
            "with the named source constant in code each threshold comes from."
        )
        rows = "".join(
            f"<tr><td><strong>{escape(str(tr.get('module', '')))}</strong></td>"
            f"<td>{escape(str(tr.get('trigger', '')))}</td>"
            f"<td>{escape(str(tr.get('threshold', '')))}"
            + (" <em>(jurisdiction-dependent)</em>" if tr.get("profile_dependent") else "") +
            f"</td>"
            f"<td style='font-family:monospace;font-size:0.82em'>{escape(str(tr.get('source_constant', '')))}</td></tr>"
            for tr in triggers
        )
        header = (
            "<tr><th>Module</th><th>Déclencheur</th><th>Seuil</th><th>Constante source</th></tr>"
            if lang == "fr" else
            "<tr><th>Module</th><th>Trigger condition</th><th>Threshold</th><th>Source constant</th></tr>"
        )
        table_html = (
            "<table style='width:100%;border-collapse:collapse;margin-top:6px;font-size:0.9em'>"
            "<style>th,td{border:1px solid #ccd5d8;padding:6px 8px;text-align:left;vertical-align:top}"
            "th{background:#edf3f3}</style>"
            f"{header}{rows}</table>"
        )
        st_module.markdown(table_html, unsafe_allow_html=True)


def render_formula_standards_map(st_module, formulas: list[dict], lang: str = "fr",
                                  expanded: bool = False) -> None:
    """Renders regulatory_references.FORMULA_STANDARDS_MAP (HSE audit
    corrective action - Regulatory Algorithm Validation): one row per
    named scoring formula, its claimed standard(s), and an honest
    Direct/Adapted/Illustrative validation status - so an auditor can see
    at a glance which numbers in this app are certified-standard
    calculations versus this app's own MVP screening heuristics. No-ops
    gracefully on an empty/None list."""
    if not formulas:
        return
    heading = "Validation des formules par rapport aux normes" if lang == "fr" \
        else "Regulatory Algorithm Validation"
    status_colors = {
        "Direct implementation": "#2e7d32",
        "Adapted / approximated": "#f2b705",
        "Illustrative (not standards-derived)": "#8a5a00",
    }
    with st_module.expander(heading, expanded=expanded):
        st_module.caption(
            "Chaque formule de notation est mise en correspondance avec la norme revendiquée, avec un statut "
            "honnête : mise en œuvre directe, adaptée/approximée, ou illustrative (non dérivée d'une norme)."
            if lang == "fr" else
            "Every scoring formula mapped against its claimed standard, with an honest status: direct "
            "implementation, adapted/approximated, or illustrative (not standards-derived)."
        )
        rows = "".join(
            f"<tr><td style='font-family:monospace;font-size:0.82em'>{escape(str(f.get('function', '')))}</td>"
            f"<td>{escape(', '.join(f.get('cited_standards', [])))}</td>"
            f"<td><span style='display:inline-block;padding:2px 8px;border-radius:4px;background:"
            f"{status_colors.get(f.get('validation_status', ''), '#666')};color:#fff;font-size:0.82em;"
            f"white-space:nowrap'>{escape(str(f.get('validation_status', '')))}</span></td>"
            f"<td style='font-size:0.85em;color:#4a5a5e'>{escape(str(f.get('caveat', '')))}</td></tr>"
            for f in formulas
        )
        header = (
            "<tr><th>Formule</th><th>Norme(s) revendiquée(s)</th><th>Statut</th><th>Remarque</th></tr>"
            if lang == "fr" else
            "<tr><th>Formula</th><th>Cited standard(s)</th><th>Status</th><th>Caveat</th></tr>"
        )
        table_html = (
            "<table style='width:100%;border-collapse:collapse;margin-top:6px;font-size:0.9em'>"
            "<style>th,td{border:1px solid #ccd5d8;padding:6px 8px;text-align:left;vertical-align:top}"
            "th{background:#edf3f3}</style>"
            f"{header}{rows}</table>"
        )
        st_module.markdown(table_html, unsafe_allow_html=True)


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


def render_feed_ok_banner(st_module, lang: str, source: str, fetched_at, cache_ttl_seconds: int | None = None) -> None:
    """Success banner shown once a live/simulated feed is actively
    supplying values (sliders are then disabled/read-only upstream).

    P0 "SENSOR & LIVE-FEED GOVERNANCE": explicitly renders the data
    source, its own reported timestamp, AND an active LIVE status -
    `cache_ttl_seconds`, when supplied (the real API feeds' @st.cache_data
    ttl from data_feeds.py), also states the freshness guarantee that
    backs the LIVE claim, since a raw computed "age in seconds" against a
    source timestamp of unknown/local timezone would be dishonestly
    precise (Open-Meteo's `fetched_at` has no UTC offset - see
    data_feeds.py). Simulated telemetry (Modules 3-5) has no cache/TTL - a
    fresh value is generated on every script rerun - so cache_ttl_seconds
    is left None there and the freshness line is simply omitted."""
    lines = [
        f"🟢 {t('feed_live_badge', lang)} — {source}",
        f"{t('feed_last_update', lang)}: {fetched_at}",
    ]
    if cache_ttl_seconds:
        lines.append(
            f"{'Fraîcheur' if lang == 'fr' else 'Freshness'}: "
            + (f"actualisé au moins toutes les {cache_ttl_seconds}s" if lang == "fr"
               else f"refreshed at least every {cache_ttl_seconds}s while this page is open")
        )
    st_module.success("  \n".join(lines))


def render_feed_error_banner(st_module, lang: str, error_message: str) -> None:
    """Warning banner shown when a live/simulated feed failed and the page
    has safely reverted to manual sliders. The raw error is tucked behind
    an expander rather than shown inline, since it's a technical detail.
    Used for non-safety-critical/ancillary feed failures (e.g. the 7-day
    forecast panel) - see render_data_unavailable_banner() for the
    stricter banner required on a safety-critical auto-mode data path."""
    st_module.warning(t("feed_error_banner", lang))
    with st_module.expander("Technical details" if lang == "en" else "Détails techniques"):
        st_module.code(error_message)


DATA_UNAVAILABLE_MESSAGE = "DATA UNAVAILABLE — MANUAL VERIFICATION REQUIRED."


def render_data_unavailable_banner(st_module, lang: str, error_message: str, source_label: str = "") -> None:
    """P0 "SENSOR & LIVE-FEED GOVERNANCE" - FAIL-SAFE STATUS. Renders the
    literal, mandated DATA_UNAVAILABLE_MESSAGE string (kept untranslated -
    a compliance string, not UI copy, per the audit spec) as a hard error
    (st.error, not st.warning) whenever a live external API or hardware
    sensor feed feeding a safety-critical calculation fails - i.e. the
    calling page has stopped auto-scoring from that feed and reverted to
    requiring a manual, human-verified value. `source_label` names which
    feed failed (e.g. "Open-Meteo /v1/forecast") when known, for the
    operator's context; the technical exception text is tucked behind an
    expander, same pattern as render_feed_error_banner()."""
    prefix = f"{source_label}: " if source_label else ""
    st_module.error(f"🛑 {prefix}{DATA_UNAVAILABLE_MESSAGE}")
    st_module.caption(
        "Le flux de données en direct est indisponible - entrez les valeurs mesurées manuellement "
        "ci-dessous avant de lancer l'évaluation." if lang == "fr" else
        "The live data feed is unavailable - enter measured values manually below before running "
        "the assessment."
    )
    with st_module.expander("Technical details" if lang == "en" else "Détails techniques"):
        st_module.code(error_message)


def render_db_fatal_banner(st_module, backend_status: dict, lang: str = "fr") -> None:
    """P0 "DATABASE SAFETY & FAIL-SAFE RUNTIME" - renders the literal,
    mandated CRITICAL DATABASE ERROR message (kept untranslated - a
    compliance string, not UI copy, per the audit spec) whenever
    analytics.get_backend_status()["fatal"] is True. No-ops entirely when
    the database is healthy (or in the ordinary, non-fatal default-SQLite-
    unconfigured state) - this function only ever renders something in the
    one specific fatal condition. Call from the dashboard (and, for
    defense-in-depth, any other page's sidebar) with
    render_db_fatal_banner(st, analytics.get_backend_status(), lang)."""
    if not backend_status.get("fatal"):
        return
    st_module.error(f"🛑 {backend_status.get('fatal_message') or 'CRITICAL DATABASE ERROR'}")
    st_module.caption(
        "La base de données de production configurée (Postgres/Supabase) est injoignable. "
        "Toutes les écritures sont gelées - aucune donnée n'est redirigée silencieusement vers un "
        "stockage local éphémère. Contactez un administrateur." if lang == "fr" else
        "The configured production database (Postgres/Supabase) is unreachable. All writes are "
        "frozen - no data is being silently redirected to ephemeral local storage. Contact an "
        "administrator."
    )


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


# ---------------------------------------------------------------------------
# High-Contrast / Full Sun mobile mode
# ---------------------------------------------------------------------------

def inject_high_contrast_css(st_module) -> None:
    """Injects a pure-white/massive-black-text/fluorescent-warning CSS
    override, opt-in via the sidebar toggle in app.py. Targets exactly the
    same 'read this in harsh outdoor glare' problem inject_mobile_css()
    already addresses for critical buttons - this goes further, overriding
    the whole page's color scheme, for a foreman standing in direct
    sunlight who can barely make out a normal-contrast screen. Purely
    additive CSS layered on top of inject_mobile_css() (both can be
    active at once) - never changes any risk calculation or layout logic,
    only visual contrast."""
    st_module.markdown(
        """
        <style>
        .stApp, [data-testid="stSidebar"], [data-testid="stHeader"] {
            background-color: #ffffff !important;
        }
        .stApp p, .stApp li, .stApp span, .stApp label, .stApp caption,
        .stMarkdown, .stCaption, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
        [data-testid="stSidebar"] * , [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"] {
            color: #000000 !important;
            font-weight: 700 !important;
        }
        .stApp h1, .stApp h2 { font-weight: 900 !important; }
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 3px solid #000000 !important;
            border-radius: 4px;
        }
        div.stButton > button {
            background-color: #000000 !important;
            color: #ffff00 !important;
            border: 3px solid #000000 !important;
            font-weight: 900 !important;
        }
        div[data-testid="stAlert"] {
            border-width: 4px !important;
            font-weight: 800 !important;
        }
        /* Fluorescent high-visibility warning/error cards - the "can't miss
           it in direct sunlight" requirement */
        div[data-baseweb="notification"][kind="warning"],
        .stApp [data-testid="stNotificationContentWarning"] {
            background-color: #fff200 !important;
            color: #000000 !important;
            border: 3px solid #000000 !important;
        }
        .stApp [data-testid="stNotificationContentError"] {
            background-color: #ff3d00 !important;
            color: #000000 !important;
            border: 3px solid #000000 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_high_contrast_toggle(st_module, lang: str) -> bool:
    """Sidebar checkbox controlling High-Contrast/Full Sun mode. Session-
    state-backed like every other sidebar selector in this app, so the
    choice persists across page navigation. Returns the current state and
    applies the CSS immediately when active - callers don't need a
    separate inject_high_contrast_css() call."""
    from i18n import t as _t
    if "high_contrast_mode" not in st_module.session_state:
        st_module.session_state["high_contrast_mode"] = False
    active = st_module.sidebar.checkbox(
        _t("high_contrast_toggle_label", lang),
        key="high_contrast_mode",
        help=_t("high_contrast_help", lang),
    )
    if active:
        inject_high_contrast_css(st_module)
    return active


def render_meteorology_forecast(st_module, lang: str, forecast: dict, fields: list[tuple[str, str]]) -> None:
    """Small 7-day forecast trend chart for Solar/Offshore (the two modules
    with a real free forecast API). fields: list of (dict_key, display_label)
    pairs to plot as separate lines."""
    import pandas as pd

    st_module.caption(f"📡 {forecast.get('source', '')}")
    chart_df = pd.DataFrame({label: forecast[key] for key, label in fields}, index=forecast["dates"])
    st_module.line_chart(chart_df)
