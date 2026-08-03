"""Render WebsiteSafeExportDocument to self-contained static HTML."""

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


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_website_safe_html(document: WebsiteSafeExportDocument) -> str:
    """Render HTML from the website-safe projection only."""

    toc = _toc(document)
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        # Trusted constant — do not HTML-escape quotes (matches Engine HTML CSP emission).
        f'<meta http-equiv="Content-Security-Policy" content="{CONTENT_SECURITY_POLICY}">',
        f"<title>{escape(document.title)}</title>",
        f"<style>{REPORT_CSS}</style>",
        "</head>",
        "<body>",
        '<a class="skip-link" href="#main">Skip to main content</a>',
        '<header class="cover"><div class="wrap">',
        f"<h1>{escape(document.title)}</h1>",
        f'<p class="badge">{escape(document.classification)}</p>',
        f'<p class="meta">Scope: {escape(document.scope)} · '
        f"Repositories: {escape(document.dataset_summary.get('repository_count', 0))} · "
        f"Confidence: {escape(document.confidence.level if document.confidence else 'unavailable')}</p>",
        f'<p class="meta">Report ID: {escape(document.report_id)} · '
        f"EIR schema: {escape(document.report_schema_version)} · "
        f"Export schema: {escape(document.export_schema_version)}</p>",
        "</div></header>",
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
        "<footer><p>Website-safe sanitized projection of a commercial Engineering "
        "Intelligence Report. Not a canonical repository assessment artifact.</p></footer>",
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
    return f"""
<section id="{section_anchor("scope")}">
<h2>Report Scope and Dataset</h2>
<p>Classification: <strong>{escape(document.classification)}</strong></p>
<p>Export scope: {escape(document.scope)}. Repository count:
{escape(document.dataset_summary.get("repository_count", 0))}.</p>
<table>
<caption>Repository population (safe aliases)</caption>
<thead><tr><th scope="col">Repository</th><th scope="col">Source type</th></tr></thead>
<tbody>{rows or "<tr><td colspan='2'>No repositories exported.</td></tr>"}</tbody>
</table>
</section>
"""


def _section_orientation(document: WebsiteSafeExportDocument) -> str:
    items = "".join(f"<li>{escape(item)}</li>" for item in document.orientation)
    notes = "".join(f"<li>{escape(item)}</li>" for item in document.empty_section_notes)
    return f"""
<section id="{section_anchor("orientation")}">
<h2>Executive Orientation</h2>
<p class="muted">Structured orientation only — not a free-form narrative.</p>
<ul>{items}</ul>
{f"<ul>{notes}</ul>" if notes else ""}
</section>
"""


def _section_summary(document: WebsiteSafeExportDocument) -> str:
    s = document.dataset_summary
    return f"""
<section id="{section_anchor("summary")}">
<h2>Engineering Intelligence Summary</h2>
<table>
<caption>Section availability counts</caption>
<tbody>
<tr><th scope="row">Repositories</th><td>{escape(s.get("repository_count", 0))}</td></tr>
<tr><th scope="row">Recurring patterns</th><td>{escape(s.get("pattern_count", 0))}</td></tr>
<tr><th scope="row">Modernization observations</th><td>{escape(s.get("observation_count", 0))}</td></tr>
<tr><th scope="row">Limitations</th><td>{escape(s.get("limitation_count", 0))}</td></tr>
<tr><th scope="row">Repository drill-downs</th><td>{escape(s.get("drilldown_count", 0))}</td></tr>
</tbody>
</table>
</section>
"""


def _section_technology(document: WebsiteSafeExportDocument) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{escape(item.category)}</td>"
        f"<td>{escape(item.technology)}</td>"
        f"<td>{escape(item.repository_count)}</td>"
        f"<td>{escape(item.denominator)}</td>"
        f"<td>{escape(item.ratio or 'unavailable')}</td>"
        f"<td>{escape(', '.join(item.version_states) or 'n/a')}</td>"
        "</tr>"
        for item in document.technology_distribution
    )
    return f"""
<section id="{section_anchor("technology")}">
<h2>Technology Distribution</h2>
<p class="muted">Descriptive presence only — no lifecycle support claims.</p>
<table>
<caption>Technology presence</caption>
<thead><tr>
<th scope="col">Category</th><th scope="col">Technology</th>
<th scope="col">Repositories</th><th scope="col">Denominator</th>
<th scope="col">Ratio</th><th scope="col">Version states</th>
</tr></thead>
<tbody>{rows or "<tr><td colspan='6'>No technology observations in scope.</td></tr>"}</tbody>
</table>
</section>
"""


def _section_capability(document: WebsiteSafeExportDocument) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{escape(item.assessment_head_id)}</td>"
        f"<td>{escape(item.repository_alias)}</td>"
        f"<td>{escape(item.activation_status)}</td>"
        f"<td>{escape(item.coverage_status)}</td>"
        f"<td>{escape(item.confidence_level)}</td>"
        f"<td>{escape(item.finding_count)}</td>"
        f"<td>{escape(item.recommendation_count)}</td>"
        f"<td>{escape(item.priority_action_count)}</td>"
        f"<td>{escape(item.highest_severity or 'n/a')}</td>"
        "</tr>"
        for item in document.capability_comparisons
    )
    return f"""
<section id="{section_anchor("capability")}">
<h2>Capability Comparison</h2>
<p class="muted">Factual snapshots only — no ranking or composite portfolio scores.</p>
<table>
<caption>Repository capability snapshots</caption>
<thead><tr>
<th scope="col">Head</th><th scope="col">Repository</th>
<th scope="col">Activation</th><th scope="col">Coverage</th>
<th scope="col">Confidence</th><th scope="col">Findings</th>
<th scope="col">Recommendations</th><th scope="col">Priority Actions</th>
<th scope="col">Highest severity</th>
</tr></thead>
<tbody>{rows or "<tr><td colspan='9'>No capability snapshots exported.</td></tr>"}</tbody>
</table>
</section>
"""


def _section_heads(document: WebsiteSafeExportDocument) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{escape(item.assessment_head_id)}</td>"
        f"<td>{escape(item.repository_count)}</td>"
        f"<td>{escape(item.activated_count)}</td>"
        f"<td>{escape(item.complete_coverage_count)}</td>"
        f"<td>{escape(item.partial_coverage_count)}</td>"
        f"<td>{escape(item.finding_count)}</td>"
        f"<td>{escape(item.recommendation_count)}</td>"
        f"<td>{escape(item.priority_action_count)}</td>"
        "</tr>"
        for item in document.assessment_head_distributions
    )
    return f"""
<section id="{section_anchor("heads")}">
<h2>Assessment-Head Distributions</h2>
<p class="muted">Cross-sectional counts — not temporal trends.</p>
<table>
<caption>Assessment-head distribution</caption>
<thead><tr>
<th scope="col">Head</th><th scope="col">Repositories</th>
<th scope="col">Activated</th><th scope="col">Complete</th>
<th scope="col">Partial</th><th scope="col">Findings</th>
<th scope="col">Recommendations</th><th scope="col">Priority Actions</th>
</tr></thead>
<tbody>{rows or "<tr><td colspan='8'>No head distributions exported.</td></tr>"}</tbody>
</table>
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
    body = "".join(blocks) or "<p>No recurring patterns met the configured multi-repository threshold.</p>"
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
        "<p>No modernization observations met the deterministic support policy.</p>"
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
        return f'<section id="{section_anchor("confidence")}"><h2>Report Confidence</h2><p>Unavailable.</p></section>'
    basis = "".join(f"<li>{escape(item)}</li>" for item in conf.basis)
    return f"""
<section id="{section_anchor("confidence")}">
<h2>Report Confidence</h2>
<p class="disclaimer"><strong>{escape(conf.disclaimer)}</strong></p>
<table>
<tbody>
<tr><th scope="row">Level</th><td>{escape(conf.level)}</td></tr>
<tr><th scope="row">Included repositories</th><td>{escape(conf.repository_sample_count)}</td></tr>
<tr><th scope="row">Comparable repositories</th><td>{escape(conf.comparable_repository_count)}</td></tr>
<tr><th scope="row">Dataset coverage</th><td>{escape(conf.dataset_coverage_status)}</td></tr>
<tr><th scope="row">Weakest material source confidence</th><td>{escape(conf.weakest_material_source_confidence)}</td></tr>
</tbody>
</table>
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
    return f"""
<section id="{section_anchor("limitations")}">
<h2>Dataset Limitations</h2>
<p class="muted">Interpretation impact — not Finding Severity.</p>
<table>
<caption>Structured dataset limitations</caption>
<thead><tr>
<th scope="col">Category</th><th scope="col">Impact</th>
<th scope="col">Statement</th><th scope="col">Affected scope</th>
</tr></thead>
<tbody>{rows or "<tr><td colspan='4'>No customer-visible limitations.</td></tr>"}</tbody>
</table>
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
            f'<article id="{drilldown_anchor(item.drilldown_id)}">'
            f"<h3>{escape(item.repository_alias)}</h3>"
            f"<p class='meta'>Source type: {escape(item.source_type)} · "
            f"Confidence: {escape(item.confidence)}</p>"
            f"<p>{escape(item.canonical_assessment_availability)}</p>"
            f"{f'<p class=\"disclaimer\">{escape(item.truncation_note)}</p>' if item.truncation_note else ''}"
            f"<h4>Technology summary</h4><ul>"
            + "".join(f"<li>{escape(tech)}</li>" for tech in item.technology_summary)
            + "</ul>"
            f"<h4>Selected findings</h4><ul>{findings or '<li>None in bounded subset.</li>'}</ul>"
            f"<h4>Selected recommendations</h4><ul>{recs or '<li>None in bounded subset.</li>'}</ul>"
            f"<h4>Highest priority action IDs</h4><ul>"
            + "".join(f"<li>{escape(action)}</li>" for action in item.priority_action_ids)
            + ("<li>None in bounded subset.</li>" if not item.priority_action_ids else "")
            + "</ul>"
            "</article>"
        )
    if len(blocks) == 1:
        blocks.append("<p>No repository drill-downs exported for this scope.</p>")
    blocks.append("</section>")
    return "\n".join(blocks)


def _section_methodology(document: WebsiteSafeExportDocument) -> str:
    method = document.methodology
    if method is None:
        return f'<section id="{section_anchor("methodology")}"><h2>Methodology</h2><p>Omitted by policy.</p></section>'
    notes = "".join(f"<li>{escape(item)}</li>" for item in method.notes)
    return f"""
<section id="{section_anchor("methodology")}">
<h2>Methodology</h2>
<table>
<tbody>
<tr><th scope="row">Assessment schema versions</th><td>{escape(', '.join(method.assessment_schema_versions))}</td></tr>
<tr><th scope="row">Interpretation policy bundle</th><td>{escape(method.interpretation_policy_bundle_id)}</td></tr>
<tr><th scope="row">Export policy</th><td>{escape(method.export_policy_id)}</td></tr>
<tr><th scope="row">Aggregation policy</th><td>{escape(method.aggregation_policy_id)}</td></tr>
</tbody>
</table>
<ul>{notes}</ul>
<p class="disclaimer">Public exports must not be presented as industry benchmarks unless the dataset and methodology independently support that claim.</p>
</section>
"""


def _section_metadata(document: WebsiteSafeExportDocument) -> str:
    meta = document.export_metadata
    if meta is None:
        return f'<section id="{section_anchor("metadata")}"><h2>Export Metadata</h2><p>Unavailable.</p></section>'
    return f"""
<section id="{section_anchor("metadata")}">
<h2>Export Metadata</h2>
<table>
<tbody>
<tr><th scope="row">Export ID</th><td>{escape(meta.export_id)}</td></tr>
<tr><th scope="row">Source report ID</th><td>{escape(meta.source_report_id)}</td></tr>
<tr><th scope="row">Export schema</th><td>{escape(meta.export_schema_version)}</td></tr>
<tr><th scope="row">JSON projection</th><td>{escape(meta.json_projection_version)}</td></tr>
<tr><th scope="row">HTML template</th><td>{escape(meta.html_template_version)}</td></tr>
<tr><th scope="row">Generated at</th><td>{escape(meta.generated_at or 'not supplied')}</td></tr>
</tbody>
</table>
</section>
"""
