"""Render WebsiteSafeExportDocument to self-contained static HTML.

Presentation only — no intelligence recalculation. Consumes Design System 1.0
tokens via ``styles.REPORT_CSS``. Stable section anchors are preserved.
"""

from __future__ import annotations

import html

from codestrata_platform.intelligence_reporting.application.website_export.models import (
    WebsiteSafeExportDocument,
)
from codestrata_platform.intelligence_reporting.application.website_export.policy import (
    CONTENT_SECURITY_POLICY,
)
from codestrata_platform.intelligence_reporting.presentation.static_html.anchors import (
    drilldown_anchor,
    observation_anchor,
    pattern_anchor,
    section_anchor,
)
from codestrata_platform.intelligence_reporting.presentation.static_html.styles import (
    REPORT_CSS,
)

PRODUCT_NAME = "CodeStrata"
PRODUCT_REPORT_LABEL = "Engineering Intelligence Report"

# Approved report derivative of the CodeStrata master brand mark (Slice 14.10).
# Byte-identical to design-system/assets/brand/codestrata-mark-mono.svg so the
# Assessment and Intelligence reports share one brand geometry.
BRAND_MARK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 22 22" class="cs-mark" '
    'aria-hidden="true" focusable="false">\n'
    '  <rect x="1" y="3" width="20" height="3" rx="1.2" fill="currentColor"/>\n'
    '  <rect x="4" y="8" width="17" height="3" rx="1.2" fill="currentColor" opacity="0.78"/>\n'
    '  <rect x="1" y="13" width="14" height="3" rx="1.2" fill="currentColor" opacity="0.56"/>\n'
    '  <rect x="6" y="18" width="12" height="3" rx="1.2" fill="currentColor" opacity="0.38"/>\n'
    "</svg>"
)


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _table_wrap(inner: str) -> str:
    # tabindex keeps the horizontal scroll reachable without a pointer.
    return f'<div class="table-wrap" tabindex="0">{inner}</div>'


def _severity_badge(label: str | None) -> str:
    text = (label or "n/a").strip() or "n/a"
    key = text.lower().replace(" ", "-")
    if key in {"critical", "high", "medium", "low", "informational"}:
        # The prefix is a hidden text node rather than aria-label, which ARIA
        # prohibits on a span's generic role.
        return (
            f'<span class="status-badge status-severity-{escape(key)}">'
            f'<span class="sr-only">Severity: </span>{escape(text)}</span>'
        )
    return escape(text)


def _kpi(label: str, value: object) -> str:
    return (
        f'<div class="kpi"><p class="kpi-label">{escape(label)}</p>'
        f'<p class="kpi-value">{escape(value)}</p></div>'
    )


def render_website_safe_html(document: WebsiteSafeExportDocument) -> str:
    """Render HTML from the website-safe projection only."""

    toc = _toc(document)
    conf_level = document.confidence.level if document.confidence else "unavailable"
    repo_count = document.dataset_summary.get("repository_count", 0)
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="color-scheme" content="light dark">',
        # Trusted constant — do not HTML-escape quotes (matches Engine HTML CSP emission).
        f'<meta http-equiv="Content-Security-Policy" content="{CONTENT_SECURITY_POLICY}">',
        f"<title>{escape(document.title)}</title>",
        f"<style>{REPORT_CSS}</style>",
        "</head>",
        "<body>",
        '<a class="skip-link" href="#main">Skip to main content</a>',
        '<div class="report-shell">',
        (
            '<header class="report-product-bar" role="banner">'
            f'<span class="report-product-mark">{BRAND_MARK_SVG}</span>'
            f'<span class="report-product-name">{escape(PRODUCT_NAME)}</span>'
            f'<span class="report-product-label">{escape(PRODUCT_REPORT_LABEL)}</span>'
            "</header>"
        ),
        # A section rather than a second <header>: only one banner landmark.
        '<section class="cover" aria-label="Report cover">'
        '<div class="wrap"><div class="cover-panel">',
        f"<h1>{escape(document.title)}</h1>",
        f'<p class="badge badge-status">{escape(document.classification)}</p>',
        '<div class="cover-meta">',
        f'<div class="meta-item"><span class="meta-label">Scope</span>'
        f'<span class="meta-value">{escape(document.scope)}</span></div>',
        f'<div class="meta-item"><span class="meta-label">Repositories</span>'
        f'<span class="meta-value">{escape(repo_count)}</span></div>',
        f'<div class="meta-item"><span class="meta-label">Confidence</span>'
        f'<span class="meta-value">{escape(conf_level)}</span></div>',
        f'<div class="meta-item"><span class="meta-label">Report ID</span>'
        f'<span class="meta-value tech-ref">{escape(document.report_id)}</span></div>',
        f'<div class="meta-item"><span class="meta-label">EIR schema</span>'
        f'<span class="meta-value">{escape(document.report_schema_version)}</span></div>',
        f'<div class="meta-item"><span class="meta-label">Export schema</span>'
        f'<span class="meta-value">{escape(document.export_schema_version)}</span></div>',
        "</div>",
        "</div></div></section>",
        '<div class="wrap">',
        toc,
        '<main id="main">',
        _section_scope(document),
        _section_orientation(document),
        _section_summary(document),
        _section_technology(document),
        _section_capability(document),
        _section_heads(document),
        _section_patterns(document),
        _section_observations(document),
        _section_confidence(document),
        _section_limitations(document),
        _section_drilldowns(document),
        _section_methodology(document),
        _section_metadata(document),
        "</main>",
        '<footer class="site-footer"><p>Website-safe sanitized projection of a commercial '
        "Engineering Intelligence Report. Not a canonical repository assessment artifact.</p>"
        "</footer>",
        "</div>",
        "</div>",
        "</body>",
        "</html>",
    ]
    return "\n".join(parts) + "\n"


def _toc(document: WebsiteSafeExportDocument) -> str:
    items = [
        ("scope", "Report Scope and Dataset"),
        ("orientation", "Executive Orientation"),
        ("summary", "Engineering Intelligence Summary"),
        ("technology", "Technology Distribution"),
        ("capability", "Capability Comparison"),
        ("heads", "Assessment-Head Distributions"),
        ("patterns", "Recurring Patterns"),
        ("observations", "Modernization Observations"),
        ("confidence", "Report Confidence"),
        ("limitations", "Dataset Limitations"),
        ("drilldowns", "Repository Drill-Downs"),
        ("methodology", "Methodology"),
        ("metadata", "Export Metadata"),
    ]
    links = []
    for key, label in items:
        links.append(f'<li><a href="#{section_anchor(key)}">{escape(label)}</a></li>')
    for item in document.repository_drilldowns:
        links.append(
            f'<li><a href="#{drilldown_anchor(item.drilldown_id)}">'
            f"Repository: {escape(item.repository_alias)}</a></li>"
        )
    return (
        f'<nav class="toc" aria-label="Table of contents">'
        f"<h2>Contents</h2><ol>{''.join(links)}</ol></nav>"
    )


def _section_scope(document: WebsiteSafeExportDocument) -> str:
    rows = "".join(
        f"<tr><td>{escape(alias)}</td><td>{escape(source)}</td></tr>"
        for alias, source in document.repository_population
    )
    table = f"""
<table>
<caption>Repository population (safe aliases)</caption>
<thead><tr><th scope="col">Repository</th><th scope="col">Source type</th></tr></thead>
<tbody>{rows or "<tr><td colspan='2' class='empty-state'>No repositories exported.</td></tr>"}</tbody>
</table>
"""
    return f"""
<section id="{section_anchor("scope")}">
<h2>Report Scope and Dataset</h2>
<p>Classification: <strong>{escape(document.classification)}</strong></p>
<p>Export scope: {escape(document.scope)}. Repository count:
{escape(document.dataset_summary.get("repository_count", 0))}.</p>
{_table_wrap(table)}
</section>
"""


def _section_orientation(document: WebsiteSafeExportDocument) -> str:
    items = "".join(f"<li>{escape(item)}</li>" for item in document.orientation)
    notes = "".join(f"<li>{escape(item)}</li>" for item in document.empty_section_notes)
    s = document.dataset_summary
    kpis = (
        # role=group so the label is honoured; a bare div has no nameable role.
        '<div class="summary-kpis" role="group" aria-label="Dataset coverage metrics">'
        f"{_kpi('Repositories', s.get('repository_count', 0))}"
        f"{_kpi('Recurring patterns', s.get('pattern_count', 0))}"
        f"{_kpi('Modernization observations', s.get('observation_count', 0))}"
        f"{_kpi('Limitations', s.get('limitation_count', 0))}"
        f"{_kpi('Repository drill-downs', s.get('drilldown_count', 0))}"
        "</div>"
    )
    return f"""
<section id="{section_anchor("orientation")}">
<h2>Executive Orientation</h2>
<p class="muted">Structured orientation only — not a free-form narrative.</p>
{kpis}
<ul>{items}</ul>
{f'<div class="empty-state"><ul>{notes}</ul></div>' if notes else ""}
</section>
"""


def _section_summary(document: WebsiteSafeExportDocument) -> str:
    s = document.dataset_summary
    table = f"""
<table>
<caption>Section availability counts</caption>
<tbody>
<tr><th scope="row">Repositories</th><td class="numeric">{escape(s.get("repository_count", 0))}</td></tr>
<tr><th scope="row">Recurring patterns</th><td class="numeric">{escape(s.get("pattern_count", 0))}</td></tr>
<tr><th scope="row">Modernization observations</th><td class="numeric">{escape(s.get("observation_count", 0))}</td></tr>
<tr><th scope="row">Limitations</th><td class="numeric">{escape(s.get("limitation_count", 0))}</td></tr>
<tr><th scope="row">Repository drill-downs</th><td class="numeric">{escape(s.get("drilldown_count", 0))}</td></tr>
</tbody>
</table>
"""
    return f"""
<section id="{section_anchor("summary")}">
<h2>Engineering Intelligence Summary</h2>
{_table_wrap(table)}
</section>
"""


def _section_technology(document: WebsiteSafeExportDocument) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{escape(item.category)}</td>"
        f"<td>{escape(item.technology)}</td>"
        f'<td class="numeric">{escape(item.repository_count)}</td>'
        f'<td class="numeric">{escape(item.denominator)}</td>'
        f"<td>{escape(item.ratio or 'unavailable')}</td>"
        f"<td>{escape(', '.join(item.version_states) or 'n/a')}</td>"
        "</tr>"
        for item in document.technology_distribution
    )
    empty = "<tr><td colspan='6'><p class='empty-state'>No technology observations in scope.</p></td></tr>"
    table = f"""
<table>
<caption>Technology presence</caption>
<thead><tr>
<th scope="col">Category</th><th scope="col">Technology</th>
<th scope="col" class="numeric">Repositories</th><th scope="col" class="numeric">Denominator</th>
<th scope="col">Ratio</th><th scope="col">Version states</th>
</tr></thead>
<tbody>{rows or empty}</tbody>
</table>
"""
    return f"""
<section id="{section_anchor("technology")}">
<h2>Technology Distribution</h2>
<p class="muted">Descriptive presence only — no lifecycle support claims.</p>
{_table_wrap(table)}
</section>
"""


def _section_capability(document: WebsiteSafeExportDocument) -> str:
    rows = "".join(
        "<tr>"
        f"<td><code class='tech-ref'>{escape(item.assessment_head_id)}</code></td>"
        f"<td>{escape(item.repository_alias)}</td>"
        f"<td>{escape(item.activation_status)}</td>"
        f"<td>{escape(item.coverage_status)}</td>"
        f"<td>{escape(item.confidence_level)}</td>"
        f'<td class="numeric">{escape(item.finding_count)}</td>'
        f'<td class="numeric">{escape(item.recommendation_count)}</td>'
        f'<td class="numeric">{escape(item.priority_action_count)}</td>'
        f"<td>{_severity_badge(item.highest_severity)}</td>"
        "</tr>"
        for item in document.capability_comparisons
    )
    empty = "<tr><td colspan='9'><p class='empty-state'>No capability snapshots exported.</p></td></tr>"
    table = f"""
<table>
<caption>Repository capability snapshots</caption>
<thead><tr>
<th scope="col">Head</th><th scope="col">Repository</th>
<th scope="col">Activation</th><th scope="col">Coverage</th>
<th scope="col">Confidence</th>
<th scope="col" class="numeric">Findings</th>
<th scope="col" class="numeric">Recommendations</th>
<th scope="col" class="numeric">Priority Actions</th>
<th scope="col">Highest severity</th>
</tr></thead>
<tbody>{rows or empty}</tbody>
</table>
"""
    return f"""
<section id="{section_anchor("capability")}">
<h2>Capability Comparison</h2>
<p class="muted">Factual snapshots only — no ranking or composite portfolio scores.</p>
{_table_wrap(table)}
</section>
"""


def _section_heads(document: WebsiteSafeExportDocument) -> str:
    rows = "".join(
        "<tr>"
        f"<td><code class='tech-ref'>{escape(item.assessment_head_id)}</code></td>"
        f'<td class="numeric">{escape(item.repository_count)}</td>'
        f'<td class="numeric">{escape(item.activated_count)}</td>'
        f'<td class="numeric">{escape(item.complete_coverage_count)}</td>'
        f'<td class="numeric">{escape(item.partial_coverage_count)}</td>'
        f'<td class="numeric">{escape(item.finding_count)}</td>'
        f'<td class="numeric">{escape(item.recommendation_count)}</td>'
        f'<td class="numeric">{escape(item.priority_action_count)}</td>'
        "</tr>"
        for item in document.assessment_head_distributions
    )
    empty = "<tr><td colspan='8'><p class='empty-state'>No head distributions exported.</p></td></tr>"
    table = f"""
<table>
<caption>Assessment-head distribution</caption>
<thead><tr>
<th scope="col">Head</th>
<th scope="col" class="numeric">Repositories</th>
<th scope="col" class="numeric">Activated</th>
<th scope="col" class="numeric">Complete</th>
<th scope="col" class="numeric">Partial</th>
<th scope="col" class="numeric">Findings</th>
<th scope="col" class="numeric">Recommendations</th>
<th scope="col" class="numeric">Priority Actions</th>
</tr></thead>
<tbody>{rows or empty}</tbody>
</table>
"""
    return f"""
<section id="{section_anchor("heads")}">
<h2>Assessment-Head Distributions</h2>
<p class="muted">Cross-sectional counts — not temporal trends.</p>
{_table_wrap(table)}
</section>
"""


def _section_patterns(document: WebsiteSafeExportDocument) -> str:
    blocks = []
    for item in document.recurring_patterns:
        blocks.append(
            f'<details id="{pattern_anchor(item.pattern_id)}">'
            f"<summary>{escape(item.title)}</summary>"
            f"<p>{escape(item.statement)}</p>"
            f"<p class='meta'>Repositories: {escape(item.repository_count)} / "
            f"{escape(item.denominator)} · Confidence: {escape(item.confidence)}</p>"
            f"<p class='meta'>Heads: {escape(', '.join(item.assessment_head_ids))}</p>"
            f"<p class='meta'>Members: {escape(', '.join(item.repository_aliases))}</p>"
            "</details>"
        )
    body = "".join(blocks) or (
        '<p class="empty-state">No recurring patterns met the configured '
        "multi-repository threshold.</p>"
    )
    return f"""
<section id="{section_anchor("patterns")}">
<h2>Recurring Patterns</h2>
{body}
</section>
"""


def _section_observations(document: WebsiteSafeExportDocument) -> str:
    blocks = []
    for item in document.modernization_observations:
        blocks.append(
            f'<details id="{observation_anchor(item.observation_id)}">'
            f"<summary>{escape(item.title)}</summary>"
            f"<p class='badge'>{escape(item.observation_label)}</p>"
            f"<p>{escape(item.statement)}</p>"
            f"<p class='meta'>Category: {escape(item.category)} · "
            f"Repositories: {escape(item.repository_count)} / {escape(item.denominator)} · "
            f"Confidence: {escape(item.confidence)}</p>"
            f"<p class='meta'>Members: {escape(', '.join(item.repository_aliases))}</p>"
            "</details>"
        )
    body = "".join(blocks) or (
        '<p class="empty-state">No modernization observations met the '
        "deterministic support policy.</p>"
    )
    return f"""
<section id="{section_anchor("observations")}">
<h2>Modernization Observations</h2>
{body}
</section>
"""


def _section_confidence(document: WebsiteSafeExportDocument) -> str:
    conf = document.confidence
    if conf is None:
        return (
            f'<section id="{section_anchor("confidence")}"><h2>Report Confidence</h2>'
            '<p class="empty-state">Unavailable.</p></section>'
        )
    basis = "".join(f"<li>{escape(item)}</li>" for item in conf.basis)
    level_key = (conf.level or "unavailable").strip().lower().replace(" ", "-")
    level_badge = (
        f'<span class="confidence-badge confidence-badge-{escape(level_key)}">'
        f"{escape(conf.level)}</span>"
    )
    table = f"""
<table>
<tbody>
<tr><th scope="row">Level</th><td>{level_badge}</td></tr>
<tr><th scope="row">Included repositories</th><td class="numeric">{escape(conf.repository_sample_count)}</td></tr>
<tr><th scope="row">Comparable repositories</th><td class="numeric">{escape(conf.comparable_repository_count)}</td></tr>
<tr><th scope="row">Dataset coverage</th><td>{escape(conf.dataset_coverage_status)}</td></tr>
<tr><th scope="row">Weakest material source confidence</th><td>{escape(conf.weakest_material_source_confidence)}</td></tr>
</tbody>
</table>
"""
    return f"""
<section id="{section_anchor("confidence")}">
<h2>Report Confidence</h2>
<p class="disclaimer"><strong>{escape(conf.disclaimer)}</strong></p>
<p class="muted">Confidence reflects evidence strength for this export — not repository health.</p>
{_table_wrap(table)}
<h3>Basis</h3>
<ul>{basis}</ul>
</section>
"""


def _section_limitations(document: WebsiteSafeExportDocument) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{escape(item.category)}</td>"
        f"<td>{escape(item.interpretation_severity)}</td>"
        f"<td>{escape(item.statement)}</td>"
        f"<td>{escape(', '.join(item.affected_scope) or 'report-wide')}</td>"
        "</tr>"
        for item in document.limitations
    )
    empty = "<tr><td colspan='4'><p class='empty-state'>No customer-visible limitations.</p></td></tr>"
    table = f"""
<table>
<caption>Structured dataset limitations</caption>
<thead><tr>
<th scope="col">Category</th><th scope="col">Impact</th>
<th scope="col">Statement</th><th scope="col">Affected scope</th>
</tr></thead>
<tbody>{rows or empty}</tbody>
</table>
"""
    return f"""
<section id="{section_anchor("limitations")}">
<h2>Dataset Limitations</h2>
<p class="muted">Interpretation impact — not Finding Severity.</p>
{_table_wrap(table)}
</section>
"""


def _section_drilldowns(document: WebsiteSafeExportDocument) -> str:
    blocks = [
        f'<section id="{section_anchor("drilldowns")}"><h2>Repository Drill-Downs</h2>'
        "<p class='muted'>Bounded navigation subsets — not complete assessment reports.</p>"
    ]
    for item in document.repository_drilldowns:
        findings = "".join(
            f"<li>{escape(ref.entity_kind)}: {escape(ref.label or ref.entity_id)}</li>"
            for ref in item.finding_refs
        )
        recs = "".join(
            f"<li>{escape(ref.entity_kind)}: {escape(ref.label or ref.entity_id)}</li>"
            for ref in item.recommendation_refs
        )
        blocks.append(
            f'<article class="drilldown-card" id="{drilldown_anchor(item.drilldown_id)}">'
            f"<h3>{escape(item.repository_alias)}</h3>"
            f"<p class='meta'>Source type: {escape(item.source_type)} · "
            f"Confidence: {escape(item.confidence)}</p>"
            f"<p>{escape(item.canonical_assessment_availability)}</p>"
            f"{f'<p class=\"disclaimer\">{escape(item.truncation_note)}</p>' if item.truncation_note else ''}"
            f"<h4>Technology summary</h4><ul class='trace-list'>"
            + "".join(f"<li>{escape(tech)}</li>" for tech in item.technology_summary)
            + "</ul>"
            f"<h4>Selected findings</h4>"
            f"<ul class='trace-list'>{findings or '<li>None in bounded subset.</li>'}</ul>"
            f"<h4>Selected recommendations</h4>"
            f"<ul class='trace-list'>{recs or '<li>None in bounded subset.</li>'}</ul>"
            f"<h4>Highest priority action IDs</h4><ul class='trace-list'>"
            + "".join(f"<li>{escape(action)}</li>" for action in item.priority_action_ids)
            + ("<li>None in bounded subset.</li>" if not item.priority_action_ids else "")
            + "</ul>"
            "</article>"
        )
    if len(blocks) == 1:
        blocks.append('<p class="empty-state">No repository drill-downs exported for this scope.</p>')
    blocks.append("</section>")
    return "\n".join(blocks)


def _section_methodology(document: WebsiteSafeExportDocument) -> str:
    method = document.methodology
    if method is None:
        return (
            f'<section id="{section_anchor("methodology")}"><h2>Methodology</h2>'
            '<p class="empty-state">Omitted by policy.</p></section>'
        )
    notes = "".join(f"<li>{escape(item)}</li>" for item in method.notes)
    table = f"""
<table>
<tbody>
<tr><th scope="row">Assessment schema versions</th><td>{escape(', '.join(method.assessment_schema_versions))}</td></tr>
<tr><th scope="row">Interpretation policy bundle</th><td class="tech-ref">{escape(method.interpretation_policy_bundle_id)}</td></tr>
<tr><th scope="row">Export policy</th><td class="tech-ref">{escape(method.export_policy_id)}</td></tr>
<tr><th scope="row">Aggregation policy</th><td class="tech-ref">{escape(method.aggregation_policy_id)}</td></tr>
</tbody>
</table>
"""
    return f"""
<section id="{section_anchor("methodology")}">
<h2>Methodology</h2>
{_table_wrap(table)}
<ul>{notes}</ul>
<p class="disclaimer">Public exports must not be presented as industry benchmarks unless the dataset and methodology independently support that claim.</p>
</section>
"""


def _section_metadata(document: WebsiteSafeExportDocument) -> str:
    meta = document.export_metadata
    if meta is None:
        return (
            f'<section id="{section_anchor("metadata")}"><h2>Export Metadata</h2>'
            '<p class="empty-state">Unavailable.</p></section>'
        )
    table = f"""
<table>
<tbody>
<tr><th scope="row">Export ID</th><td class="tech-ref">{escape(meta.export_id)}</td></tr>
<tr><th scope="row">Source report ID</th><td class="tech-ref">{escape(meta.source_report_id)}</td></tr>
<tr><th scope="row">Export schema</th><td>{escape(meta.export_schema_version)}</td></tr>
<tr><th scope="row">JSON projection</th><td>{escape(meta.json_projection_version)}</td></tr>
<tr><th scope="row">HTML template</th><td>{escape(meta.html_template_version)}</td></tr>
<tr><th scope="row">Generated at</th><td>{escape(meta.generated_at or 'not supplied')}</td></tr>
</tbody>
</table>
"""
    return f"""
<section id="{section_anchor("metadata")}">
<h2>Export Metadata</h2>
{_table_wrap(table)}
</section>
"""
