"""Self-contained CodeStrata Engineering Assessment HTML report renderer.

Presentation only — no analysis or enrichment business logic.
"""

from __future__ import annotations

from aimf.reporters.html_rendering import escape_and_wrap, escape_html
from aimf.reporting.ai_readiness.models import AiReadinessReportSection
from aimf.reporting.architecture.models import ArchitectureReportSection
from aimf.reporting.branding import (
    BRAND_FOOTER_LINE,
    BRAND_NAME,
    BRAND_REPORT_NAME,
    BRAND_VERSION,
    logo_data_uri,
)
from aimf.reporting.cloud.models import CloudReportSection
from aimf.reporting.dependency.models import DependencyReportSection
from aimf.reporting.html_v2.models import (
    AiEnrichmentView,
    FindingView,
    HtmlReportViewModel,
    RecommendationView,
)
from aimf.reporting.performance.models import PerformanceReportSection
from aimf.reporting.roadmap.models import RoadmapReportSection
from aimf.reporting.security.models import SecurityReportSection
from aimf.reporting.technical_debt.models import TechnicalDebtReportSection
from aimf.reporting.testing.models import TestingReportSection

CONTENT_SECURITY_POLICY = (
    "default-src 'none'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'none'; "
    "img-src data:; "
    "font-src 'none'; "
    "connect-src 'none'; "
    "object-src 'none'; "
    "script-src 'none'; "
    "style-src 'unsafe-inline'"
)

_TOP_FINDINGS = 5
_SEVERITY_ORDER = ("critical", "high", "medium", "low", "informational")


class HtmlReportRenderer:
    """Render HtmlReportViewModel to a complete HTML document.

    Contains no analysis or enrichment business logic.
    """

    def render(self, view: HtmlReportViewModel) -> str:
        parts = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            f'<meta http-equiv="Content-Security-Policy" content="{CONTENT_SECURITY_POLICY}">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{escape_html(BRAND_NAME)} {escape_html(BRAND_REPORT_NAME)} — "
            f"{escape_html(view.summary.repository_name)}</title>",
            f"<style>{_CSS}</style>",
            "</head>",
            "<body>",
            '<div class="page">',
            _render_hero(view),
            _section(
                "Executive Summary",
                _render_executive_cards(view),
                section_id="executive",
                note=(
                    "Leadership snapshot: counts and readiness signals only. "
                    "Detailed findings and phased initiatives follow below."
                ),
            ),
            _section(
                "Technology Overview",
                _render_technology(view),
                section_id="technology",
            ),
            _section(
                "Findings Overview",
                _render_findings_overview(view),
                section_id="findings",
                note=(
                    "Highest-severity deterministic findings first. "
                    "Full evidence and IDs are in Technical Details."
                ),
            ),
            _section(
                "Modernization Roadmap",
                _render_roadmap(view.recommendations),
                section_id="recommendations",
                note=(
                    "Priority-ordered deterministic recommendations with links "
                    "to related findings where available."
                ),
            ),
        ]
        if view.architecture_report is not None:
            parts.append(
                _section(
                    "Architecture Assessment",
                    _render_architecture(view.architecture_report),
                    section_id="architecture-assessment",
                    note=(
                        "Deterministic architecture assessment presentation. "
                        "Does not invent scores, business impact, or strengths."
                    ),
                )
            )
        if view.technical_debt_report is not None:
            parts.append(
                _section(
                    "Technical Debt Assessment",
                    _render_technical_debt(view.technical_debt_report),
                    section_id="technical-debt-assessment",
                    note=(
                        "Deterministic technical debt assessment presentation. "
                        "Does not invent composite scores, financial cost, or "
                        "remediation-hour estimates. Hotspot order is presentation "
                        "order, not priority ranking."
                    ),
                )
            )
        if view.dependency_report is not None:
            parts.append(
                _section(
                    "Dependency Assessment",
                    _render_dependency(view.dependency_report),
                    section_id="dependency-assessment",
                    note=(
                        "Deterministic declared-dependency assessment presentation. "
                        "Does not invent health scores, vulnerability verdicts, "
                        "license assessments, or latest-version advice. Hotspot "
                        "order is presentation order, not priority ranking."
                    ),
                )
            )
        if view.security_report is not None:
            parts.append(
                _section(
                    "Security Intelligence",
                    _render_security(view.security_report),
                    section_id="security-assessment",
                    note=(
                        "Deterministic repository Security hygiene assessment "
                        "presentation. Does not invent vulnerability verdicts, "
                        "compliance claims, scores, or exploitability. Zero findings "
                        "do not establish that the repository is secure. Hotspot "
                        "order is presentation order, not priority ranking."
                    ),
                )
            )
        if view.testing_report is not None:
            parts.append(
                _section(
                    "Test Intelligence",
                    _render_testing(view.testing_report),
                    section_id="testing-assessment",
                    note=(
                        "Deterministic repository Test Hygiene assessment "
                        "presentation. Does not invent test-quality scores, "
                        "pass/fail execution results, or runtime coverage. Zero "
                        "findings do not certify test sufficiency or readiness "
                        "for release."
                    ),
                )
            )
        if view.cloud_report is not None:
            parts.append(
                _section(
                    "Cloud Intelligence",
                    _render_cloud(view.cloud_report),
                    section_id="cloud-assessment",
                    note=(
                        "Deterministic repository Cloud Hygiene assessment "
                        "presentation. Does not invent readiness scores, "
                        "portability verdicts, or provider compliance claims. "
                        "Zero findings do not establish that the repository is "
                        "cloud ready."
                    ),
                )
            )
        if view.ai_readiness_report is not None:
            parts.append(
                _section(
                    "AI Readiness Intelligence",
                    _render_ai_readiness(view.ai_readiness_report),
                    section_id="ai-readiness-assessment",
                    note=(
                        "Deterministic repository AI Readiness Hygiene assessment "
                        "presentation. Does not invent readiness scores, agent "
                        "enablement verdicts, or RAG suitability claims. Zero "
                        "findings do not certify AI/agent enablement."
                    ),
                )
            )
        if view.performance_report is not None:
            parts.append(
                _section(
                    "Performance Intelligence",
                    _render_performance(view.performance_report),
                    section_id="performance-assessment",
                    note=(
                        "Deterministic repository Performance Hygiene assessment "
                        "presentation. Does not invent performance scores or "
                        "load suitability claims. Zero findings do not certify "
                        "load suitability."
                    ),
                )
            )
        if view.roadmap_report is not None:
            parts.append(
                _section(
                    "Phased Modernization Plan",
                    _render_phased_roadmap(view.roadmap_report),
                    section_id="modernization-roadmap-assessment",
                    note=(
                        "Deterministic phased plan derived from existing findings "
                        "and recommendations only. Does not invent initiatives, "
                        "schedules, cost estimates, or portfolio plans."
                    ),
                )
            )
        if view.ai_enrichment is not None:
            parts.append(
                _section(
                    "AI Executive Summary",
                    _render_ai(view.ai_enrichment),
                    section_id="ai-enrichment",
                    note=(
                        "AI-generated interpretation. Not merged into findings or recommendations."
                    ),
                    css_class="section section-ai",
                )
            )
        parts.append(
            _section(
                "Technical Details",
                _render_technical_details(view),
                section_id="technical-details",
                note="Engineering reference: evidence, graphs, artifacts, and metadata.",
            )
        )
        parts.extend(
            [
                _render_footer(),
                "</div>",
                "</body>",
                "</html>",
                "",
            ]
        )
        return "\n".join(parts)


def _section(
    title: str,
    body: str,
    *,
    section_id: str,
    note: str | None = None,
    css_class: str = "section",
) -> str:
    note_html = f'<p class="section-note">{escape_html(note)}</p>' if note else ""
    return (
        f'<section class="{css_class}" id="{escape_html(section_id)}">\n'
        f'<div class="section-head"><h2>{escape_html(title)}</h2></div>\n'
        f"{note_html}"
        f"{body}\n"
        "</section>"
    )


def _render_hero(view: HtmlReportViewModel) -> str:
    summary = view.summary
    mode_short = _mode_short(summary.assessment_mode_label)
    severity_tone = _severity_tone(summary.highest_finding_severity)
    return (
        '<header class="hero" id="hero">\n'
        '<div class="hero-brand">\n'
        f'<img class="brand-logo" src="{logo_data_uri()}" '
        f'alt="{escape_html(BRAND_NAME)}" width="140" height="40">\n'
        f'<p class="brand-name">{escape_html(BRAND_NAME)}</p>\n'
        f'<h1 class="report-title">{escape_html(BRAND_REPORT_NAME)}</h1>\n'
        "</div>\n"
        '<div class="hero-meta">\n'
        '<div class="meta-item"><span class="meta-label">Repository</span>'
        f'<span class="meta-value">{escape_and_wrap(summary.repository_name)}</span></div>\n'
        '<div class="meta-item"><span class="meta-label">Generated</span>'
        f'<span class="meta-value">{escape_html(view.metadata.generated_at_utc)}</span></div>\n'
        '<div class="meta-item"><span class="meta-label">Version</span>'
        f'<span class="meta-value">v{escape_html(BRAND_VERSION)}</span></div>\n'
        '<div class="meta-item"><span class="meta-label">Mode</span>'
        f'<span class="meta-value">{escape_html(mode_short)}</span></div>\n'
        '<div class="meta-item"><span class="meta-label">Source</span>'
        f'<span class="meta-value">{escape_html(view.repository.source_type)}</span></div>\n'
        "</div>\n"
        '<div class="hero-kpis">\n'
        f"{_kpi('Highest Finding Severity', summary.highest_finding_severity, '', severity_tone)}"
        f"{_kpi('Cloud Enablement Signals', _cloud_primary(view), _cloud_status(view), 'cloud')}"
        f"{_kpi('CI/CD', _cicd_value(view), '', 'cicd')}"
        f"{_kpi('Assessment mode', summary.assessment_mode_label, '', 'mode')}"
        "</div>\n"
        "</header>"
    )


def _severity_tone(label: str) -> str:
    key = label.lower().replace(" ", "-")
    if key in {"critical", "high", "medium", "low", "informational", "none-detected", "unknown"}:
        return f"severity-{key}"
    return "mode"


def _cloud_primary(view: HtmlReportViewModel) -> str:
    metrics = view.summary.metrics
    if metrics is None:
        return "Unknown"
    return metrics.cloud_signals_primary


def _cloud_status(view: HtmlReportViewModel) -> str:
    metrics = view.summary.metrics
    if metrics is None:
        return "Unknown"
    if metrics.cloud_signals_primary == "Unknown":
        return ""
    return metrics.cloud_signals_status


def _cicd_value(view: HtmlReportViewModel) -> str:
    metrics = view.summary.metrics
    if metrics is None:
        return "Unknown"
    return metrics.cicd_label


def _kpi(label: str, value: str, hint: str, tone: str) -> str:
    hint_html = f'<span class="kpi-hint">{escape_html(hint)}</span>' if hint else ""
    return (
        f'<article class="kpi kpi-{escape_html(tone)}">'
        f'<p class="kpi-label">{escape_html(label)}</p>'
        f'<p class="kpi-value">{escape_html(value)}</p>'
        f"{hint_html}"
        "</article>\n"
    )


def _mode_short(label: str) -> str:
    lower = label.lower()
    if "ai enhanced" in lower or (
        label.startswith("AI") and "fallback" not in lower and "requested" not in lower
    ):
        return "AI"
    if "deterministic" in lower:
        return "Deterministic"
    return label


def _render_executive_cards(view: HtmlReportViewModel) -> str:
    metrics = view.summary.metrics
    file_count = metrics.file_count if metrics else view.repository.file_count
    tech_count = metrics.technology_count if metrics else len(view.summary.technologies)
    findings = metrics.findings_count if metrics else view.summary.total_findings
    recommendations = (
        metrics.recommendations_count if metrics else view.summary.total_recommendations
    )
    tests = metrics.test_files_label if metrics else "Unknown"
    cicd = metrics.cicd_label if metrics else "Unknown"
    cloud_primary = metrics.cloud_signals_primary if metrics else "Unknown"
    cloud_status = (
        metrics.cloud_signals_status
        if metrics and metrics.cloud_signals_primary != "Unknown"
        else ""
    )
    size = metrics.repository_size_label if metrics else f"{file_count} files"
    highest = view.summary.highest_finding_severity
    return (
        '<div class="stat-grid">\n'
        f"{_stat_card('Files', str(file_count))}"
        f"{_stat_card('Technologies', str(tech_count))}"
        f"{_stat_card('Findings', str(findings))}"
        f"{_stat_card('Recommendations', str(recommendations))}"
        f"{_stat_card('Test Files Detected', tests)}"
        f"{_stat_card('CI/CD', cicd)}"
        f"{_stat_card('Cloud Enablement Signals', cloud_primary, cloud_status)}"
        f"{_stat_card('Repository Size', size)}"
        f"{_stat_card('Highest Finding Severity', highest)}"
        "</div>"
    )


def _stat_card(label: str, value: str, hint: str = "") -> str:
    hint_html = f'<p class="stat-hint">{escape_html(hint)}</p>' if hint else ""
    return (
        f'<article class="stat-card"><p class="stat-label">{escape_html(label)}</p>'
        f'<p class="stat-value">{escape_html(value)}</p>'
        f"{hint_html}"
        "</article>\n"
    )


def _render_technology(view: HtmlReportViewModel) -> str:
    if not view.technologies and not view.version_highlights:
        return (
            '<p class="muted">No technologies were detected in this repository scan. '
            "Confirm language manifests are present and re-run assessment if needed.</p>"
        )
    badges = (
        "".join(
            f'<span class="tech-badge">{escape_html(item.name)}'
            + (f"<em>{escape_html(item.version)}</em>" if item.version else "")
            + "</span>"
            for item in view.technologies
        )
        or '<span class="muted">None detected</span>'
    )
    highlights = ""
    if view.version_highlights:
        rows = "".join(
            "<tr>"
            f"<td>{escape_html(item.label)}</td>"
            f"<td>{escape_and_wrap(item.value)}</td>"
            f"<td>{escape_html(item.kind)}</td>"
            "</tr>"
            for item in view.version_highlights
        )
        highlights = (
            '<div class="table-card">\n'
            "<h3>Version highlights</h3>\n"
            '<div class="table-wrap"><table>\n'
            "<thead><tr><th>Label</th><th>Value</th><th>Kind</th></tr></thead>\n"
            f"<tbody>{rows}</tbody>\n</table></div>\n"
            "</div>"
        )
    return f'<div class="tech-badges">{badges}</div>\n{highlights}'


def _severity_counts(view: HtmlReportViewModel) -> dict[str, int]:
    counts = {key: 0 for key in _SEVERITY_ORDER}
    for name, count in view.summary.findings_by_severity:
        key = name.lower()
        if key in {"info", "informational"}:
            counts["informational"] += count
        elif key in counts:
            counts[key] += count
    return counts


def _render_findings_overview(view: HtmlReportViewModel) -> str:
    counts = _severity_counts(view)
    meters = "".join(
        f'<article class="severity-card severity-{escape_html(name)}">'
        f'<p class="severity-label">{escape_html(name if name != "informational" else "info")}</p>'
        f'<p class="severity-count">{counts[name]}</p>'
        "</article>\n"
        for name in _SEVERITY_ORDER
    )
    top = view.findings[:_TOP_FINDINGS]
    if not top:
        cards = (
            '<p class="muted">No deterministic findings were produced for this run. '
            "This does not certify that the repository is free of issues.</p>"
        )
    else:
        cards = (
            '<div class="card-stack">\n'
            + "\n".join(_render_finding_card(item, compact=True) for item in top)
            + "\n</div>"
        )
        if len(view.findings) > _TOP_FINDINGS:
            cards += (
                f'<p class="muted more-note">Showing top {_TOP_FINDINGS} of '
                f"{len(view.findings)}. Full list in Technical Details.</p>"
            )
    return f'<div class="severity-grid">{meters}</div>\n<h3>Priority findings</h3>\n{cards}'


def _render_finding_card(item: FindingView, *, compact: bool) -> str:
    nodes = _id_list(item.affected_nodes) or '<span class="muted">None</span>'
    evidence = "" if compact else _render_evidence_details(item.evidence)
    meta = ""
    if not compact:
        meta = (
            '<dl class="meta">\n'
            f"<div><dt>Finding ID</dt>"
            f"<dd><code>{escape_and_wrap(item.finding_id)}</code></dd></div>\n"
            f"<div><dt>Rule ID</dt><dd><code>{escape_and_wrap(item.rule_id)}</code></dd></div>\n"
            f"<div><dt>Category</dt><dd>{escape_html(item.category)}</dd></div>\n"
            f"<div><dt>Affected nodes</dt><dd>{nodes}</dd></div>\n"
            "</dl>\n"
        )
    description = ""
    if not compact:
        description = f'<p class="card-desc">{escape_html(item.description)}</p>\n'
    return (
        f'<article class="item-card finding" id="finding-{escape_html(item.finding_id)}">\n'
        f'<header class="item-header">'
        f'<span class="badge severity-{escape_html(item.severity)}">'
        f"{escape_html(item.severity)}</span> "
        f"<strong>{escape_html(item.title)}</strong>"
        f"</header>\n"
        f"{description}"
        f"{meta}"
        f"{evidence}\n"
        "</article>"
    )


def _roadmap_bucket(priority: str) -> str:
    key = priority.lower()
    if key in {"immediate", "critical"}:
        return "Immediate"
    if key in {"high", "medium"}:
        return "Near Term"
    return "Future"


def _render_roadmap(items: tuple[RecommendationView, ...]) -> str:
    if not items:
        return (
            '<p class="muted">No deterministic recommendations are available yet. '
            "Findings may still appear above when present.</p>"
        )
    buckets: dict[str, list[RecommendationView]] = {
        "Immediate": [],
        "Near Term": [],
        "Future": [],
    }
    for item in items:
        buckets[_roadmap_bucket(item.priority)].append(item)
    parts: list[str] = ['<div class="roadmap">']
    for name, group in buckets.items():
        if not group:
            continue
        cards = "\n".join(_render_recommendation_card(item, compact=True) for item in group)
        parts.append(
            f'<div class="roadmap-lane">\n'
            f'<h3>{escape_html(name)} <span class="count-pill">{len(group)}</span></h3>\n'
            f'<div class="card-stack">{cards}</div>\n'
            "</div>"
        )
    parts.append("</div>")
    return "\n".join(parts)


def _business_value(priority: str) -> str:
    key = priority.lower()
    if key in {"immediate", "critical", "high"}:
        return "High"
    if key == "medium":
        return "Medium"
    return "Incremental"


def _effort_label(item: RecommendationView) -> str:
    actions = len(item.actions)
    if actions <= 1:
        return "Small"
    if actions <= 3:
        return "Medium"
    return "Larger"


def _render_recommendation_card(item: RecommendationView, *, compact: bool) -> str:
    related = _finding_id_links(item.related_finding_ids) or '<span class="muted">None</span>'
    nodes = _id_list(item.affected_nodes) or '<span class="muted">None</span>'
    chips = (
        '<div class="chip-row">\n'
        f'<span class="chip"><em>Priority</em> {escape_html(item.priority)}</span>\n'
        f'<span class="chip"><em>Business Value</em> '
        f"{escape_html(_business_value(item.priority))}</span>\n"
        f'<span class="chip"><em>Effort</em> {escape_html(_effort_label(item))}</span>\n'
        "</div>\n"
        f'<p class="outcome"><em>Expected Outcome</em> {escape_html(item.summary)}</p>\n'
    )
    detail = ""
    if not compact:
        actions = (
            "".join(
                "<li>"
                f"<strong>{action.order}. {escape_html(action.title)}</strong>"
                f" — {escape_html(action.description)}"
                + (
                    f' <code class="cmd">{escape_and_wrap(action.command)}</code>'
                    if action.command
                    else ""
                )
                + "</li>"
                for action in item.actions
            )
            or "<li>None</li>"
        )
        detail = (
            f"<p><em>Rationale:</em> {escape_html(item.rationale)}</p>\n"
            '<dl class="meta">\n'
            f"<div><dt>Recommendation ID</dt>"
            f"<dd><code>{escape_and_wrap(item.recommendation_id)}</code></dd></div>\n"
            f"<div><dt>Category</dt><dd>{escape_html(item.category)}</dd></div>\n"
            f"<div><dt>Related finding IDs</dt><dd>{related}</dd></div>\n"
            f"<div><dt>Affected nodes</dt><dd>{nodes}</dd></div>\n"
            "</dl>\n"
            "<h4>Actions</h4>\n"
            f'<ol class="actions">{actions}</ol>\n'
            f"{_render_evidence_details(item.evidence)}\n"
        )
    return (
        f'<article class="item-card recommendation" '
        f'id="recommendation-{escape_html(item.recommendation_id)}">\n'
        f'<header class="item-header">'
        f'<span class="badge priority-{escape_html(item.priority)}">'
        f"{escape_html(item.priority)}</span> "
        f"<strong>{escape_html(item.title)}</strong>"
        f"</header>\n"
        f"{chips}"
        f"{detail}"
        "</article>"
    )


def _render_architecture(section: ArchitectureReportSection) -> str:
    metrics = "".join(
        "<div class='card'>"
        f"<div class='label'>{escape_html(item.label)}</div>"
        f"<div class='value'>{escape_html(item.value)}</div>"
        f"{f'<p class="muted">{escape_html(item.note)}</p>' if item.note else ''}"
        "</div>"
        for item in section.key_metrics
    )
    conclusions = (
        "".join(
            "<article class='card'>"
            f"<h4>{escape_html(item.title)}</h4>"
            f"<p>{escape_html(item.summary)}</p>"
            "<p class='muted'>"
            f"Materiality: {escape_html(item.materiality)} · "
            f"Confidence: {escape_html(item.confidence)} · "
            f"Business impact: {escape_html(item.business_impact)} · "
            f"Wave: {escape_html(item.modernization_relevance)}"
            "</p>"
            f"<p class='muted'>{escape_html(item.severity_summary)}</p>"
            f"<p class='muted'>Scope: {escape_html(', '.join(item.affected_scope) or '—')}</p>"
            "</article>"
            for item in section.conclusions
        )
        or "<p class='muted'>No architecture conclusions were generated.</p>"
    )
    recommendations = (
        "".join(
            "<article class='card'>"
            f"<h4>{escape_html(item.title)}</h4>"
            f"<p><strong>Objective:</strong> {escape_html(item.objective)}</p>"
            f"<p>{escape_html(item.rationale)}</p>"
            f"<p class='muted'>Wave: {escape_html(item.modernization_wave)}</p>"
            "</article>"
            for item in section.recommendation_groups
        )
        or "<p class='muted'>No consolidated architecture recommendation groups.</p>"
    )
    findings = "".join(
        "<tr>"
        f"<td>{escape_html(item.title)}</td>"
        f"<td>{escape_html(item.severity)}</td>"
        f"<td>{escape_html(item.confidence)}</td>"
        f"<td>{escape_html(', '.join(item.affected_scope) or '—')}</td>"
        f"<td>{'Yes' if item.linked_to_conclusion else 'No'}</td>"
        "</tr>"
        for item in section.findings
    )
    findings_table = (
        "<table><thead><tr>"
        "<th>Finding</th><th>Severity</th><th>Confidence</th>"
        "<th>Scope</th><th>Linked conclusion</th>"
        "</tr></thead><tbody>"
        f"{findings}</tbody></table>"
        if findings
        else "<p class='muted'>No visible architecture findings.</p>"
    )
    coverage = "".join(
        "<tr>"
        f"<td>{escape_html(item.label)}</td>"
        f"<td>{escape_html(item.status)}</td>"
        f"<td>{escape_html(item.display)}</td>"
        "</tr>"
        for item in section.coverage_summary
    )
    coverage_table = (
        "<table><thead><tr><th>Area</th><th>Status</th><th>Detail</th></tr></thead>"
        f"<tbody>{coverage}</tbody></table>"
        if coverage
        else "<p class='muted'>Coverage details unavailable.</p>"
    )
    limitations = (
        "".join(
            f"<li><strong>{escape_html(item.category)}</strong> — {escape_html(item.summary)}</li>"
            for item in section.limitations
        )
        or "<li>None recorded.</li>"
    )
    trace = (
        f"<p>{escape_html(section.traceability_summary.summary)}</p>"
        "<details><summary>Sample relationships</summary><ul>"
        + "".join(
            "<li>"
            f"{escape_html(edge.relation)}: "
            f"<code>{escape_html(edge.source_id)}</code> → "
            f"<code>{escape_html(edge.target_id)}</code>"
            "</li>"
            for edge in section.traceability_summary.sample_edges
        )
        + "</ul></details>"
    )
    pack = (
        f"{escape_html(section.architecture_pack_id or '—')}@"
        f"{escape_html(section.architecture_pack_version or '—')}"
    )
    return (
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>"
        f"<p><strong>Pack:</strong> {pack}</p>"
        f"<p>{escape_html(section.executive_summary)}</p>"
        f"<div class='grid'>{metrics}</div>"
        "<h3>Architecture conclusions</h3>"
        f"{conclusions}"
        "<h3>Recommended actions</h3>"
        f"{recommendations}"
        "<h3>Supporting findings</h3>"
        f"{findings_table}"
        "<h3>Coverage</h3>"
        f"{coverage_table}"
        "<h3>Limitations</h3>"
        f"<ul>{limitations}</ul>"
        "<h3>Traceability</h3>"
        f"{trace}"
    )


def _render_technical_debt(section: TechnicalDebtReportSection) -> str:
    metrics = "".join(
        "<div class='card'>"
        f"<div class='label'>{escape_html(item.label)}</div>"
        f"<div class='value'>{escape_html(item.value)}</div>"
        f"{f'<p class="muted">{escape_html(item.note)}</p>' if item.note else ''}"
        "</div>"
        for item in section.key_metrics
    )
    themes = "".join(
        "<tr>"
        f"<td>{escape_html(item.title)}</td>"
        f"<td><code>{escape_html(item.rule_id)}</code></td>"
        f"<td>{item.finding_count}</td>"
        f"<td>{item.high_severity_count}</td>"
        f"<td>{item.medium_severity_count}</td>"
        "</tr>"
        for item in section.significant_themes
    )
    themes_table = (
        "<table><thead><tr>"
        "<th>Theme</th><th>Rule</th><th>Findings</th>"
        "<th>High</th><th>Medium</th>"
        "</tr></thead><tbody>"
        f"{themes}</tbody></table>"
        if themes
        else "<p class='muted'>No significant production themes.</p>"
    )
    hotspots = "".join(
        "<tr>"
        f"<td>{item.presentation_order}</td>"
        f"<td><code>{escape_html(item.path)}</code></td>"
        f"<td>{escape_html(item.source_unit)}</td>"
        f"<td>{escape_html(item.highest_severity)}</td>"
        f"<td>{item.finding_count}</td>"
        f"<td>{escape_html(', '.join(item.rule_ids) or '—')}</td>"
        f"<td>{escape_html(item.metric_summary)}</td>"
        "</tr>"
        for item in section.top_production_hotspots
    )
    hotspots_table = (
        "<table><thead><tr>"
        "<th>#</th><th>Path</th><th>Unit</th><th>Highest severity</th>"
        "<th>Findings</th><th>Rules</th><th>Metrics</th>"
        "</tr></thead><tbody>"
        f"{hotspots}</tbody></table>"
        if hotspots
        else "<p class='muted'>No production hotspots to present.</p>"
    )
    conclusions = (
        "".join(
            "<article class='card'>"
            f"<h4>{escape_html(item.title)}</h4>"
            f"<p>{escape_html(item.summary)}</p>"
            "<p class='muted'>"
            f"Kind: {escape_html(item.kind)} · "
            f"Audience: {escape_html(item.audience)} · "
            f"Confidence: {escape_html(item.confidence)} · "
            f"Findings: {item.finding_count} · Hotspots: {item.hotspot_count}"
            "</p>"
            "</article>"
            for item in section.conclusions
        )
        or "<p class='muted'>No production-facing technical debt conclusions.</p>"
    )
    recommendations = (
        "".join(
            "<article class='card'>"
            f"<h4>{escape_html(item.title)}</h4>"
            f"<p><strong>Action:</strong> {escape_html(item.action)}</p>"
            f"<p>{escape_html(item.rationale)}</p>"
            f"<p class='muted'>"
            f"{'Conditional' if item.conditional else 'Direct'} · "
            f"Audience: {escape_html(item.audience)}"
            "</p>"
            "</article>"
            for item in section.recommendations
        )
        or "<p class='muted'>No production-facing technical debt recommendations.</p>"
    )
    test_obs = section.test_observation
    test_block = (
        "<div class='card td-test-observation'>"
        f"<h4>{escape_html(test_obs.title)}</h4>"
        f"<p>{escape_html(test_obs.summary)}</p>"
        f"<p class='muted'>Test findings: {test_obs.finding_count}</p>"
        "</div>"
        if test_obs.present
        else "<p class='muted'>No separate test-maintainability observation.</p>"
    )
    coverage = "".join(
        "<tr>"
        f"<td>{escape_html(item.label)}</td>"
        f"<td>{escape_html(item.status)}</td>"
        f"<td>{escape_html(item.display)}</td>"
        "</tr>"
        for item in section.coverage_summary
    )
    coverage_table = (
        "<table><thead><tr><th>Area</th><th>Status</th><th>Detail</th></tr></thead>"
        f"<tbody>{coverage}</tbody></table>"
        if coverage
        else "<p class='muted'>Coverage details unavailable.</p>"
    )
    limitations = (
        "".join(
            f"<li><strong>{escape_html(item.category)}</strong> — {escape_html(item.summary)}</li>"
            for item in section.limitations
        )
        or "<li>None recorded.</li>"
    )
    trace = (
        f"<p>{escape_html(section.traceability_summary.summary)}</p>"
        "<details><summary>Sample relationships</summary><ul>"
        + "".join(
            "<li>"
            f"{escape_html(edge.relation)}: "
            f"<code>{escape_html(edge.source_id)}</code> → "
            f"<code>{escape_html(edge.target_id)}</code>"
            "</li>"
            for edge in section.traceability_summary.sample_edges
        )
        + "</ul></details>"
    )
    pack = (
        f"{escape_html(section.technical_debt_pack_id or '—')}@"
        f"{escape_html(section.technical_debt_pack_version or '—')}"
    )
    return (
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>"
        f"<p><strong>Pack:</strong> {pack}</p>"
        f"<p>{escape_html(section.executive_summary)}</p>"
        f"<div class='grid'>{metrics}</div>"
        "<h3>Significant production themes</h3>"
        f"{themes_table}"
        "<h3>Top production hotspots</h3>"
        f"<p class='muted'>{escape_html(section.hotspot_presentation_note)}</p>"
        f"{hotspots_table}"
        "<h3>Production conclusions</h3>"
        f"{conclusions}"
        "<h3>Recommended actions</h3>"
        f"{recommendations}"
        "<h3>Test-maintainability observation</h3>"
        "<p class='muted'>Test findings are not production health signals.</p>"
        f"{test_block}"
        "<h3>Coverage</h3>"
        f"{coverage_table}"
        "<h3>Limitations</h3>"
        f"<ul>{limitations}</ul>"
        "<h3>Traceability</h3>"
        f"{trace}"
    )


def _render_dependency(section: DependencyReportSection) -> str:
    landscape_rows = "".join(
        "<tr>"
        f"<td>{escape_html(item.label)}</td>"
        f"<td>{item.count}</td>"
        f"<td>{escape_html(item.group)}</td>"
        "</tr>"
        for item in section.landscape
    )
    landscape_table = (
        "<table><thead><tr><th>Metric</th><th>Count</th><th>Group</th></tr></thead>"
        f"<tbody>{landscape_rows}</tbody></table>"
        if landscape_rows
        else ""
    )
    production = section.production_health
    if production.finding_count == 0 and production.none_detected_statement:
        production_findings = f"<p>{escape_html(production.none_detected_statement)}</p>"
    else:
        production_findings = (
            "".join(
                "<article class='card'>"
                f"<h4>{escape_html(item.title)}</h4>"
                f"<p>{escape_html(item.explanation)}</p>"
                f"<p><strong>Remediation:</strong> {escape_html(item.remediation)}</p>"
                "<p class='muted'>"
                f"ID: <code>{escape_html(item.finding_id)}</code> · "
                f"Rule: <code>{escape_html(item.rule_id)}</code> · "
                f"Severity: {escape_html(item.severity)} · "
                f"Confidence: {escape_html(item.confidence)} · "
                f"Source role: {escape_html(item.source_role)}"
                + (f" · Path: <code>{escape_html(item.path)}</code>" if item.path else "")
                + (
                    f" · Identity: <code>{escape_html(item.normalized_identity)}</code>"
                    if item.normalized_identity
                    else ""
                )
                + "</p>"
                "</article>"
                for item in production.findings
            )
            or "<p class='muted'>No production hygiene findings displayed.</p>"
        )
    production_block = (
        f"<p class='muted'>Production findings: {production.finding_count}"
        f" (showing {production.findings_displayed})</p>"
        f"{production_findings}"
    )
    test_obs = section.test_observations
    if test_obs.present:
        test_findings = "".join(
            "<article class='card'>"
            f"<h4>{escape_html(item.title)}</h4>"
            f"<p>{escape_html(item.explanation)}</p>"
            f"<p><strong>Remediation:</strong> {escape_html(item.remediation)}</p>"
            "<p class='muted'>"
            f"ID: <code>{escape_html(item.finding_id)}</code> · "
            f"Rule: <code>{escape_html(item.rule_id)}</code> · "
            f"Source role: {escape_html(item.source_role)}"
            + (f" · Path: <code>{escape_html(item.path)}</code>" if item.path else "")
            + "</p>"
            "</article>"
            for item in test_obs.findings
        )
        test_block = (
            f"<h4>{escape_html(test_obs.title)}</h4>"
            f"<p>{escape_html(test_obs.summary)}</p>"
            f"<p class='muted'>Test/fixture findings: {test_obs.finding_count}</p>"
            f"{test_findings}"
        )
    else:
        test_block = ""
    hotspots = "".join(
        "<tr>"
        f"<td>{item.presentation_order}</td>"
        f"<td><code>{escape_html(item.path)}</code></td>"
        f"<td>{escape_html(item.source_role)}</td>"
        f"<td>{escape_html(item.ecosystem)}</td>"
        f"<td>{escape_html(item.manifest_type)}</td>"
        f"<td>{item.active_declaration_count}</td>"
        f"<td>{item.dependency_management_count}</td>"
        f"<td>{item.plugin_count}</td>"
        f"<td>{item.hygiene_finding_count}</td>"
        f"<td>{item.distinct_rule_count}</td>"
        f"<td>{escape_html(item.highest_severity)}</td>"
        f"<td>{item.diagnostics_count}</td>"
        "</tr>"
        for item in section.manifest_hotspots
    )
    hotspots_table = (
        "<table><thead><tr>"
        "<th>#</th><th>Path</th><th>Source role</th><th>Ecosystem</th>"
        "<th>Manifest type</th><th>Active</th><th>Management</th><th>Plugins</th>"
        "<th>Findings</th><th>Rules</th><th>Highest severity</th><th>Diagnostics</th>"
        "</tr></thead><tbody>"
        f"{hotspots}</tbody></table>"
        if hotspots
        else ""
    )
    conclusions = "".join(
        "<article class='card'>"
        f"<h4>{escape_html(item.title)}</h4>"
        f"<p>{escape_html(item.summary)}</p>"
        "<p class='muted'>"
        f"ID: <code>{escape_html(item.conclusion_id)}</code> · "
        f"Kind: {escape_html(item.kind)} · "
        f"Audience: {escape_html(item.audience)} · "
        f"Confidence: {escape_html(item.confidence)} · "
        f"Findings: {item.finding_count}"
        "</p>"
        "</article>"
        for item in section.conclusions
    )
    recommendations = "".join(
        "<article class='card'>"
        f"<h4>{escape_html(item.title)}</h4>"
        f"<p><strong>Action:</strong> {escape_html(item.action)}</p>"
        f"<p>{escape_html(item.rationale)}</p>"
        f"<p class='muted'>"
        f"ID: <code>{escape_html(item.recommendation_id)}</code> · "
        f"{'Conditional' if item.conditional else 'Direct'} · "
        f"Audience: {escape_html(item.audience)}"
        "</p>"
        "</article>"
        for item in section.recommendations
    )
    coverage = section.coverage
    coverage_rows = (
        "<tr><td>Evidence schema</td>"
        f"<td>{escape_html(coverage.evidence_schema_version or '—')}</td></tr>"
        "<tr><td>Evidence fingerprint</td>"
        f"<td><code>{escape_html(coverage.evidence_fingerprint or '—')}</code></td></tr>"
        "<tr><td>Manifests discovered / supported / parsed / failed</td>"
        f"<td>{coverage.manifests_discovered} / {coverage.manifests_supported} / "
        f"{coverage.manifests_parsed} / {coverage.manifests_failed}</td></tr>"
        "<tr><td>Production parse failures</td>"
        f"<td>{coverage.production_parse_failures}</td></tr>"
        "<tr><td>Test/fixture parse failures</td>"
        f"<td>{coverage.test_fixture_parse_failures}</td></tr>"
        "<tr><td>Unsupported constructs</td>"
        f"<td>{coverage.unsupported_construct_count}</td></tr>"
        "<tr><td>Proven unresolved</td>"
        f"<td>{coverage.proven_unresolved_count}</td></tr>"
        "<tr><td>Unsupported resolution</td>"
        f"<td>{coverage.unsupported_resolution_count}</td></tr>"
        "<tr><td>Diagnostics (samples / total)</td>"
        f"<td>{len(coverage.diagnostic_samples)} / {coverage.diagnostic_total}</td></tr>"
    )
    coverage_table = (
        "<table><thead><tr><th>Coverage</th><th>Detail</th></tr></thead>"
        f"<tbody>{coverage_rows}</tbody></table>"
        f"<p class='muted'>{escape_html(coverage.note)}</p>"
    )
    diagnostic_samples = "".join(
        "<li>"
        f"<code>{escape_html(item.diagnostic_code)}</code> — "
        f"{escape_html(item.message)}"
        + (f" (<code>{escape_html(item.path)}</code>)" if item.path else "")
        + f" · source role: {escape_html(item.source_role)}"
        "</li>"
        for item in coverage.diagnostic_samples
    )
    diagnostics_block = (
        f"<details><summary>Diagnostic samples "
        f"({len(coverage.diagnostic_samples)} of {coverage.diagnostic_total})"
        "</summary><ul>"
        f"{diagnostic_samples or '<li>None</li>'}"
        "</ul></details>"
        if coverage.diagnostic_total
        else ""
    )
    limitations = "".join(
        f"<li><strong>{escape_html(item.category)}</strong> — {escape_html(item.summary)}</li>"
        for item in section.limitations
    )
    limitations_block = f"<ul>{limitations}</ul>" if limitations else ""
    trace = (
        f"<p>{escape_html(section.traceability.summary)}</p>"
        "<details><summary>Sample relationships</summary><ul>"
        + "".join(
            "<li>"
            f"{escape_html(edge.relation)}: "
            f"<code>{escape_html(edge.source_id)}</code> → "
            f"<code>{escape_html(edge.target_id)}</code>"
            "</li>"
            for edge in section.traceability.sample_edges
        )
        + "</ul></details>"
        if section.traceability.sample_edges or section.traceability.summary
        else ""
    )
    pack = (
        f"{escape_html(section.dependency_pack_id or '—')}@"
        f"{escape_html(section.dependency_pack_version or '—')}"
    )
    parts = [
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>",
        f"<p><strong>Pack:</strong> {pack}</p>",
        "<h3>Executive Summary</h3>",
        f"<p>{escape_html(section.executive_summary)}</p>",
    ]
    if landscape_table:
        parts.extend(["<h3>Dependency Landscape</h3>", landscape_table])
    parts.extend(["<h3>Production Dependency Hygiene</h3>", production_block])
    if test_block:
        parts.extend(
            [
                "<h3>Test and Fixture Observations</h3>",
                "<p class='muted'>Test/fixture findings are not production health signals.</p>",
                test_block,
            ]
        )
    if hotspots_table:
        parts.extend(
            [
                "<h3>Manifest Hotspots</h3>",
                f"<p class='muted'>{escape_html(section.hotspot_presentation_note)}</p>",
                hotspots_table,
            ]
        )
    if conclusions:
        parts.extend(["<h3>Conclusions</h3>", conclusions])
    if recommendations:
        parts.extend(["<h3>Recommendations</h3>", recommendations])
    parts.extend(["<h3>Coverage and Limitations</h3>", coverage_table])
    if diagnostics_block:
        parts.append(diagnostics_block)
    if limitations_block:
        parts.append(limitations_block)
    if trace:
        parts.extend(["<h3>Traceability</h3>", trace])
    return "\n".join(parts)


def _render_security(section: SecurityReportSection) -> str:
    coverage = section.coverage_summary
    finding = section.finding_summary
    coverage_rows = (
        "<tr><td>Evidence status</td>"
        f"<td>{escape_html(coverage.evidence_status or '—')}</td></tr>"
        "<tr><td>Evidence schema</td>"
        f"<td>{escape_html(coverage.evidence_schema_name or '—')}@"
        f"{escape_html(coverage.evidence_schema_version or '—')}</td></tr>"
        "<tr><td>Candidate artifacts discovered / inspected</td>"
        f"<td>{coverage.candidate_artifacts_discovered} / "
        f"{coverage.artifacts_inspected}</td></tr>"
        "<tr><td>Structured files parsed / configuration facts</td>"
        f"<td>{coverage.structured_files_parsed} / "
        f"{coverage.configuration_facts_collected}</td></tr>"
        "<tr><td>Rules registered / executed</td>"
        f"<td>{coverage.rules_registered} / {coverage.rules_executed}</td></tr>"
        "<tr><td>Malformed / unsupported / skipped files</td>"
        f"<td>{coverage.malformed_files} / {coverage.unsupported_binaries} / "
        f"{coverage.skipped_files}</td></tr>"
        "<tr><td>Source roles represented</td>"
        f"<td>{escape_html(', '.join(coverage.source_roles_represented) or '—')}</td></tr>"
        "<tr><td>Formats represented</td>"
        f"<td>{escape_html(', '.join(coverage.formats_represented) or '—')}</td></tr>"
    )
    coverage_table = (
        "<table><thead><tr><th>Coverage</th><th>Detail</th></tr></thead>"
        f"<tbody>{coverage_rows}</tbody></table>"
        f"<p class='muted'>{escape_html(coverage.note)}</p>"
    )
    status_block = (
        f"<p><strong>Assessment status:</strong> "
        f"{escape_html(section.assessment_status)}</p>"
        f"<p><strong>Synthesis status:</strong> "
        f"{escape_html(section.synthesis_status)}</p>"
        f"{coverage_table}"
    )
    if finding.production_finding_count == 0 and finding.none_detected_statement:
        production_findings = f"<p>{escape_html(finding.none_detected_statement)}</p>"
    else:
        production_findings = (
            "".join(
                "<article class='card'>"
                f"<h4>{escape_html(item.title)}</h4>"
                f"<p>{escape_html(item.explanation or '')}</p>"
                + (
                    f"<p><strong>Remediation:</strong> {escape_html(item.remediation)}</p>"
                    if item.remediation
                    else ""
                )
                + "<p class='muted'>"
                f"ID: <code>{escape_html(item.finding_id)}</code> · "
                f"Rule: <code>{escape_html(item.rule_id)}</code> · "
                f"Severity: {escape_html(item.severity)} · "
                f"Category: {escape_html(item.category)} · "
                f"Source role: {escape_html(item.source_role)}"
                + (f" · Path: <code>{escape_html(item.path)}</code>" if item.path else "")
                + "</p></article>"
                for item in finding.production_findings
            )
            or "<p class='muted'>No production-role findings displayed.</p>"
        )
    production_block = (
        f"<p class='muted'>Production findings: "
        f"{finding.production_finding_count} "
        f"(showing {finding.production_findings_displayed})</p>"
        f"{production_findings}"
    )
    if finding.additional_observations:
        additional_block = (
            "<p class='muted'>Test, fixture, and unknown-role observations "
            f"({finding.test_finding_count} test/fixture, "
            f"{finding.unknown_finding_count} unknown). These do not contribute "
            "to the production-primary view.</p>"
            + "".join(
                "<article class='card'>"
                f"<h4>{escape_html(item.title)}</h4>"
                f"<p>{escape_html(item.explanation or '')}</p>"
                "<p class='muted'>"
                f"ID: <code>{escape_html(item.finding_id)}</code> · "
                f"Rule: <code>{escape_html(item.rule_id)}</code> · "
                f"Source role: {escape_html(item.source_role)}"
                + (f" · Path: <code>{escape_html(item.path)}</code>" if item.path else "")
                + "</p></article>"
                for item in finding.additional_observations
            )
        )
    else:
        additional_block = ""
    themes = "".join(
        "<article class='card'>"
        f"<h4>{escape_html(item.title)}</h4>"
        f"<p>{escape_html(item.summary)}</p>"
        "<p class='muted'>"
        f"ID: <code>{escape_html(item.theme_id)}</code> · "
        f"Kind: {escape_html(item.kind)} · "
        f"Scope: {escape_html(item.scope)} · "
        f"Source role: {escape_html(item.source_role)} · "
        f"Findings: {item.finding_count}"
        "</p></article>"
        for item in section.themes
    )
    hotspots = "".join(
        "<tr>"
        f"<td>{item.presentation_order}</td>"
        f"<td><code>{escape_html(item.path)}</code></td>"
        f"<td>{item.production_finding_count}</td>"
        f"<td>{item.test_finding_count}</td>"
        f"<td>{item.unknown_finding_count}</td>"
        f"<td>{item.total_finding_count}</td>"
        f"<td>{escape_html(item.highest_severity)}</td>"
        f"<td>{escape_html(', '.join(item.rule_ids) or '—')}</td>"
        f"<td>{escape_html(', '.join(item.categories) or '—')}</td>"
        "</tr>"
        for item in section.hotspots
    )
    hotspots_table = (
        "<table><thead><tr>"
        "<th>#</th><th>Location</th><th>Production</th><th>Test/fixture</th>"
        "<th>Unknown</th><th>Total</th><th>Highest severity</th>"
        "<th>Rules</th><th>Categories</th>"
        "</tr></thead><tbody>"
        f"{hotspots}</tbody></table>"
        if hotspots
        else ""
    )
    conclusions = "".join(
        "<article class='card'>"
        f"<h4>{escape_html(item.title)}</h4>"
        f"<p>{escape_html(item.summary)}</p>"
        "<p class='muted'>"
        f"ID: <code>{escape_html(item.conclusion_id)}</code> · "
        f"Kind: {escape_html(item.kind)} · "
        f"Audience: {escape_html(item.audience)} · "
        f"Confidence: {escape_html(item.confidence)} · "
        f"Findings: {item.finding_count}"
        "</p></article>"
        for item in section.conclusions
    )
    if section.recommendation_groups:
        recommendations = "".join(
            f"<h4>{escape_html(group.group)}</h4>"
            + "".join(
                "<article class='card'>"
                f"<h5>{escape_html(item.title)}</h5>"
                f"<p><strong>Action:</strong> {escape_html(item.action)}</p>"
                f"<p>{escape_html(item.rationale)}</p>"
                f"<p class='muted'>"
                f"ID: <code>{escape_html(item.recommendation_id)}</code> · "
                f"{'Conditional' if item.conditional else 'Direct'} · "
                f"Audience: {escape_html(item.audience)}"
                "</p></article>"
                for item in group.recommendations
            )
            for group in section.recommendation_groups
        )
    else:
        recommendations = "".join(
            "<article class='card'>"
            f"<h4>{escape_html(item.title)}</h4>"
            f"<p><strong>Action:</strong> {escape_html(item.action)}</p>"
            f"<p>{escape_html(item.rationale)}</p>"
            f"<p class='muted'>"
            f"ID: <code>{escape_html(item.recommendation_id)}</code> · "
            f"{'Conditional' if item.conditional else 'Direct'} · "
            f"Audience: {escape_html(item.audience)}"
            "</p></article>"
            for item in section.recommendations
        )
    diagnostics = "".join(
        "<li>"
        f"<code>{escape_html(item.origin)}</code> · "
        f"<code>{escape_html(item.diagnostic_code)}</code> — "
        f"{escape_html(item.message)}"
        + (f" (<code>{escape_html(item.path)}</code>)" if item.path else "")
        + "</li>"
        for item in section.diagnostics
    )
    diagnostics_block = (
        f"<details><summary>Coverage diagnostics "
        f"({section.diagnostics_displayed} of {section.diagnostics_total})"
        "</summary><ul>"
        f"{diagnostics}"
        "</ul></details>"
        if section.diagnostics
        else ""
    )
    limitations = "".join(
        f"<li><strong>{escape_html(item.category)}</strong> — {escape_html(item.summary)}</li>"
        for item in section.limitations
    )
    limitations_block = f"<ul>{limitations}</ul>" if limitations else ""
    trace = (
        f"<p>{escape_html(section.traceability.summary)}</p>"
        "<details><summary>Sample relationships</summary><ul>"
        + "".join(
            "<li>"
            f"{escape_html(edge.relation)}: "
            f"<code>{escape_html(edge.source_id)}</code> → "
            f"<code>{escape_html(edge.target_id)}</code>"
            "</li>"
            for edge in section.traceability.sample_edges
        )
        + "</ul></details>"
        if section.traceability.sample_edges or section.traceability.summary
        else ""
    )
    pack = (
        f"{escape_html(section.security_pack_id or '—')}@"
        f"{escape_html(section.security_pack_version or '—')}"
    )
    parts = [
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>",
        f"<p><strong>Pack:</strong> {pack}</p>",
        "<h3>Executive Summary</h3>",
        f"<p>{escape_html(section.executive_summary)}</p>",
        "<h3>Assessment and Coverage Status</h3>",
        status_block,
        "<h3>Production-Primary Findings</h3>",
        production_block,
    ]
    if additional_block:
        parts.extend(
            [
                "<h3>Additional Test/Fixture/Unknown Observations</h3>",
                additional_block,
            ]
        )
    if themes:
        parts.extend(
            [
                "<h3>Security Themes</h3>",
                f"<p class='muted'>Showing {section.themes_displayed} of "
                f"{section.themes_total}</p>",
                themes,
            ]
        )
    if hotspots_table:
        parts.extend(
            [
                "<h3>Finding Hotspots</h3>",
                f"<p class='muted'>{escape_html(section.hotspot_presentation_note)}</p>",
                hotspots_table,
            ]
        )
    if conclusions:
        parts.extend(
            [
                "<h3>Conclusions</h3>",
                f"<p class='muted'>Showing {section.conclusions_displayed} of "
                f"{section.conclusions_total}</p>",
                conclusions,
            ]
        )
    if recommendations:
        parts.extend(
            [
                "<h3>Recommendations</h3>",
                f"<p class='muted'>Showing {section.recommendations_displayed} of "
                f"{section.recommendations_total}</p>",
                recommendations,
            ]
        )
    if diagnostics_block:
        parts.extend(["<h3>Coverage Diagnostics</h3>", diagnostics_block])
    if limitations_block:
        parts.extend(["<h3>Limitations</h3>", limitations_block])
    if trace:
        parts.extend(["<h3>Traceability</h3>", trace])
    return "\n".join(parts)


def _render_testing(section: TestingReportSection) -> str:
    coverage = section.coverage_summary
    execution = section.execution_summary
    inventory = section.inventory_summary
    coverage_rows = "".join(
        "<tr>"
        f"<td><code>{escape_html(area.area_id)}</code></td>"
        f"<td>{escape_html(area.status)}</td>"
        f"<td>{area.numerator if area.numerator is not None else '—'}"
        f" / {area.denominator if area.denominator is not None else '—'}</td>"
        f"<td>{escape_html(area.maturity)}</td>"
        "</tr>"
        for area in coverage.areas
    )
    coverage_table = (
        "<table><thead><tr><th>Area</th><th>Status</th>"
        "<th>Numerator / Denominator</th><th>Maturity</th></tr></thead>"
        f"<tbody>{coverage_rows or '<tr><td colspan="4">—</td></tr>'}"
        "</tbody></table>"
        f"<p class='muted'>{escape_html(coverage.note)}</p>"
    )
    execution_rows = (
        "<tr><td>Rules planned / executed</td>"
        f"<td>{execution.rules_planned} / {execution.rules_executed}</td></tr>"
        "<tr><td>Matched / not matched / not applicable / failed</td>"
        f"<td>{execution.rules_matched} / {execution.rules_not_matched} / "
        f"{execution.rules_not_applicable} / {execution.rules_failed}</td></tr>"
        "<tr><td>Findings / themes / conclusions / recommendations</td>"
        f"<td>{execution.total_finding_count} / {execution.theme_count} / "
        f"{execution.conclusion_count} / {execution.recommendation_count}</td></tr>"
    )
    rule_rows = "".join(
        "<tr>"
        f"<td><code>{escape_html(item.rule_id)}</code></td>"
        f"<td>{'yes' if item.executed else 'no'}</td>"
        f"<td>{escape_html(item.evaluation_status)}</td>"
        f"<td>{item.finding_count}</td>"
        "</tr>"
        for item in execution.entries
    )
    execution_table = (
        "<table><thead><tr><th>Metric</th><th>Value</th></tr></thead>"
        f"<tbody>{execution_rows}</tbody></table>"
        + (
            "<table><thead><tr><th>Rule</th><th>Executed</th>"
            "<th>Status</th><th>Findings</th></tr></thead>"
            f"<tbody>{rule_rows}</tbody></table>"
            if rule_rows
            else ""
        )
        + f"<p class='muted'>{escape_html(execution.note)}</p>"
    )
    bucket_block = (
        "<p class='muted'>By rule: "
        + escape_html(", ".join(f"{item.key}={item.count}" for item in inventory.by_rule) or "—")
        + "</p><p class='muted'>By severity: "
        + escape_html(
            ", ".join(f"{item.key}={item.count}" for item in inventory.by_severity) or "—"
        )
        + "</p><p class='muted'>By confidence: "
        + escape_html(
            ", ".join(f"{item.key}={item.count}" for item in inventory.by_confidence) or "—"
        )
        + "</p>"
    )
    if inventory.finding_count == 0 and inventory.none_detected_statement:
        inventory_body = f"<p>{escape_html(inventory.none_detected_statement)}</p>"
    else:
        inventory_body = (
            "<p class='muted'>Finding IDs "
            f"(showing {inventory.finding_ids_displayed} of "
            f"{inventory.finding_count}):</p><ul>"
            + "".join(
                f"<li><code>{escape_html(finding_id)}</code></li>"
                for finding_id in inventory.finding_ids
            )
            + "</ul>"
        )
    themes = "".join(
        "<article class='card'>"
        f"<h4>{escape_html(item.title)}</h4>"
        f"<p>{escape_html(item.summary)}</p>"
        "<p class='muted'>"
        f"ID: <code>{escape_html(item.theme_id)}</code> · "
        f"Kind: {escape_html(item.kind)} · "
        f"Scope: {escape_html(item.scope)} · "
        f"Findings: {item.finding_count}"
        "</p></article>"
        for item in section.themes
    )
    conclusions = "".join(
        "<article class='card'>"
        f"<h4>{escape_html(item.title)}</h4>"
        f"<p>{escape_html(item.summary)}</p>"
        "<p class='muted'>"
        f"ID: <code>{escape_html(item.conclusion_id)}</code> · "
        f"Kind: {escape_html(item.kind)} · "
        f"Audience: {escape_html(item.audience)} · "
        f"Confidence: {escape_html(item.confidence)} · "
        f"Findings: {item.finding_count}"
        "</p></article>"
        for item in section.conclusions
    )
    if section.recommendation_groups:
        recommendations = "".join(
            f"<h4>{escape_html(group.group)}</h4>"
            + "".join(
                "<article class='card'>"
                f"<h5>{escape_html(item.title)}</h5>"
                f"<p><strong>Action:</strong> {escape_html(item.action)}</p>"
                f"<p>{escape_html(item.rationale)}</p>"
                f"<p class='muted'>"
                f"ID: <code>{escape_html(item.recommendation_id)}</code> · "
                f"{'Conditional' if item.conditional else 'Direct'} · "
                f"Audience: {escape_html(item.audience)}"
                + (
                    " · Findings: "
                    + ", ".join(f"<code>{escape_html(fid)}</code>" for fid in item.finding_ids)
                    if item.finding_ids
                    else ""
                )
                + "</p></article>"
                for item in group.recommendations
            )
            for group in section.recommendation_groups
        )
    else:
        recommendations = "".join(
            "<article class='card'>"
            f"<h4>{escape_html(item.title)}</h4>"
            f"<p><strong>Action:</strong> {escape_html(item.action)}</p>"
            f"<p>{escape_html(item.rationale)}</p>"
            f"<p class='muted'>"
            f"ID: <code>{escape_html(item.recommendation_id)}</code>"
            "</p></article>"
            for item in section.recommendations
        )
    diagnostics = "".join(
        "<li>"
        f"<code>{escape_html(item.origin)}</code> · "
        f"<code>{escape_html(item.diagnostic_code)}</code> — "
        f"{escape_html(item.message)}"
        "</li>"
        for item in section.diagnostics
    )
    diagnostics_block = (
        f"<details><summary>Diagnostics "
        f"({section.diagnostics_displayed} of {section.diagnostics_total})"
        "</summary><ul>"
        f"{diagnostics}"
        "</ul></details>"
        if section.diagnostics
        else ""
    )
    limitations = "".join(
        f"<li><strong>{escape_html(item.category)}</strong> — {escape_html(item.summary)}</li>"
        for item in section.limitations
    )
    limitations_block = f"<ul>{limitations}</ul>" if limitations else ""
    trace = (
        f"<p>{escape_html(section.traceability.summary)}</p>"
        "<details><summary>Sample relationships</summary><ul>"
        + "".join(
            "<li>"
            f"{escape_html(edge.relation)}: "
            f"<code>{escape_html(edge.source_id)}</code> → "
            f"<code>{escape_html(edge.target_id)}</code>"
            "</li>"
            for edge in section.traceability.sample_edges
        )
        + "</ul></details>"
        if section.traceability.sample_edges or section.traceability.summary
        else ""
    )
    pack = (
        f"{escape_html(section.testing_pack_id or '—')}@"
        f"{escape_html(section.testing_pack_version or '—')}"
    )
    parts = [
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>",
        f"<p><strong>Pack:</strong> {pack}</p>",
        "<h3>Overall Test Posture</h3>",
        f"<p>{escape_html(section.overall_posture_summary or section.executive_summary)}</p>",
        "<h3>Executive Summary</h3>",
        f"<p>{escape_html(section.executive_summary)}</p>",
        "<h3>Assessment and Coverage Status</h3>",
        f"<p><strong>Assessment status:</strong> {escape_html(section.assessment_status)}</p>",
        f"<p><strong>Synthesis status:</strong> {escape_html(section.synthesis_status)}</p>",
        f"<p class='muted'>Evidence pipeline: "
        f"{escape_html(coverage.evidence_pipeline or '—')} · "
        f"Evidence status: {escape_html(coverage.evidence_status or '—')}</p>",
        coverage_table,
        "<h3>Rule Execution Summary</h3>",
        execution_table,
        "<h3>Inventory Summary</h3>",
        bucket_block,
        inventory_body,
    ]
    if themes:
        parts.extend(
            [
                "<h3>Themes</h3>",
                f"<p class='muted'>Showing {section.themes_displayed} of "
                f"{section.themes_total}</p>",
                themes,
            ]
        )
    if conclusions:
        parts.extend(
            [
                "<h3>Conclusions</h3>",
                f"<p class='muted'>Showing {section.conclusions_displayed} of "
                f"{section.conclusions_total}</p>",
                conclusions,
            ]
        )
    if recommendations:
        parts.extend(
            [
                "<h3>Recommendations</h3>",
                f"<p class='muted'>Showing {section.recommendations_displayed} of "
                f"{section.recommendations_total}</p>",
                recommendations,
            ]
        )
    if diagnostics_block:
        parts.extend(["<h3>Diagnostics</h3>", diagnostics_block])
    if limitations_block:
        parts.extend(["<h3>Limitations</h3>", limitations_block])
    if trace:
        parts.extend(["<h3>Traceability</h3>", trace])
    return "\n".join(parts)


def _render_cloud(section: CloudReportSection) -> str:
    coverage = section.coverage_summary
    execution = section.execution_summary
    inventory = section.inventory_summary
    families = section.technology_family_summary
    coverage_rows = "".join(
        "<tr>"
        f"<td><code>{escape_html(area.area_id)}</code></td>"
        f"<td>{escape_html(area.status)}</td>"
        f"<td>{area.numerator if area.numerator is not None else '—'}"
        f" / {area.denominator if area.denominator is not None else '—'}</td>"
        f"<td>{escape_html(area.maturity)}</td>"
        "</tr>"
        for area in coverage.areas
    )
    coverage_table = (
        "<table><thead><tr><th>Area</th><th>Status</th>"
        "<th>Numerator / Denominator</th><th>Maturity</th></tr></thead>"
        f"<tbody>{coverage_rows or '<tr><td colspan="4">—</td></tr>'}"
        "</tbody></table>"
        f"<p class='muted'>{escape_html(coverage.note)}</p>"
    )
    execution_rows = (
        "<tr><td>Rules planned / executed</td>"
        f"<td>{execution.rules_planned} / {execution.rules_executed}</td></tr>"
        "<tr><td>Matched / not matched / not applicable / failed</td>"
        f"<td>{execution.rules_matched} / {execution.rules_not_matched} / "
        f"{execution.rules_not_applicable} / {execution.rules_failed}</td></tr>"
        "<tr><td>Findings / themes / conclusions / recommendations</td>"
        f"<td>{execution.total_finding_count} / {execution.theme_count} / "
        f"{execution.conclusion_count} / {execution.recommendation_count}</td></tr>"
    )
    rule_rows = "".join(
        "<tr>"
        f"<td><code>{escape_html(item.rule_id)}</code></td>"
        f"<td>{'yes' if item.executed else 'no'}</td>"
        f"<td>{escape_html(item.evaluation_status)}</td>"
        f"<td>{item.finding_count}</td>"
        "</tr>"
        for item in execution.entries
    )
    execution_table = (
        "<table><thead><tr><th>Metric</th><th>Value</th></tr></thead>"
        f"<tbody>{execution_rows}</tbody></table>"
        + (
            "<table><thead><tr><th>Rule</th><th>Executed</th>"
            "<th>Status</th><th>Findings</th></tr></thead>"
            f"<tbody>{rule_rows}</tbody></table>"
            if rule_rows
            else ""
        )
        + f"<p class='muted'>{escape_html(execution.note)}</p>"
    )
    family_rows = "".join(
        "<tr>"
        f"<td><code>{escape_html(item.family_id)}</code></td>"
        f"<td>{'yes' if item.observed else 'no'}</td>"
        f"<td>{item.finding_count}</td>"
        f"<td>{escape_html(', '.join(item.technologies) or '—')}</td>"
        "</tr>"
        for item in families.entries
    )
    family_table = (
        f"<p class='muted'>Observed {families.families_observed} of "
        f"{families.families_total} technology families.</p>"
        "<table><thead><tr><th>Family</th><th>Observed</th>"
        "<th>Findings</th><th>Technologies</th></tr></thead>"
        f"<tbody>{family_rows or '<tr><td colspan="4">—</td></tr>'}"
        "</tbody></table>"
        f"<p class='muted'>{escape_html(families.note)}</p>"
    )
    bucket_block = (
        "<p class='muted'>By rule: "
        + escape_html(", ".join(f"{item.key}={item.count}" for item in inventory.by_rule) or "—")
        + "</p><p class='muted'>By severity: "
        + escape_html(
            ", ".join(f"{item.key}={item.count}" for item in inventory.by_severity) or "—"
        )
        + "</p><p class='muted'>By confidence: "
        + escape_html(
            ", ".join(f"{item.key}={item.count}" for item in inventory.by_confidence) or "—"
        )
        + "</p>"
    )
    if inventory.finding_count == 0 and inventory.none_detected_statement:
        inventory_body = f"<p>{escape_html(inventory.none_detected_statement)}</p>"
    else:
        inventory_body = (
            "<p class='muted'>Finding IDs "
            f"(showing {inventory.finding_ids_displayed} of "
            f"{inventory.finding_count}):</p><ul>"
            + "".join(
                f"<li><code>{escape_html(finding_id)}</code></li>"
                for finding_id in inventory.finding_ids
            )
            + "</ul>"
        )
    themes = "".join(
        "<article class='card'>"
        f"<h4>{escape_html(item.title)}</h4>"
        f"<p>{escape_html(item.summary)}</p>"
        "<p class='muted'>"
        f"ID: <code>{escape_html(item.theme_id)}</code> · "
        f"Kind: {escape_html(item.kind)} · "
        f"Scope: {escape_html(item.scope)} · "
        f"Findings: {item.finding_count}"
        "</p></article>"
        for item in section.themes
    )
    conclusions = "".join(
        "<article class='card'>"
        f"<h4>{escape_html(item.title)}</h4>"
        f"<p>{escape_html(item.summary)}</p>"
        "<p class='muted'>"
        f"ID: <code>{escape_html(item.conclusion_id)}</code> · "
        f"Kind: {escape_html(item.kind)} · "
        f"Audience: {escape_html(item.audience)} · "
        f"Confidence: {escape_html(item.confidence)} · "
        f"Findings: {item.finding_count}"
        "</p></article>"
        for item in section.conclusions
    )
    if section.recommendation_groups:
        recommendations = "".join(
            f"<h4>{escape_html(group.group)}</h4>"
            + "".join(
                "<article class='card'>"
                f"<h5>{escape_html(item.title)}</h5>"
                f"<p><strong>Action:</strong> {escape_html(item.action)}</p>"
                f"<p>{escape_html(item.rationale)}</p>"
                f"<p class='muted'>"
                f"ID: <code>{escape_html(item.recommendation_id)}</code> · "
                f"{'Conditional' if item.conditional else 'Direct'} · "
                f"Audience: {escape_html(item.audience)}"
                + (
                    " · Findings: "
                    + ", ".join(f"<code>{escape_html(fid)}</code>" for fid in item.finding_ids)
                    if item.finding_ids
                    else ""
                )
                + "</p></article>"
                for item in group.recommendations
            )
            for group in section.recommendation_groups
        )
    else:
        recommendations = "".join(
            "<article class='card'>"
            f"<h4>{escape_html(item.title)}</h4>"
            f"<p><strong>Action:</strong> {escape_html(item.action)}</p>"
            f"<p>{escape_html(item.rationale)}</p>"
            f"<p class='muted'>"
            f"ID: <code>{escape_html(item.recommendation_id)}</code>"
            "</p></article>"
            for item in section.recommendations
        )
    diagnostics = "".join(
        "<li>"
        f"<code>{escape_html(item.origin)}</code> · "
        f"<code>{escape_html(item.diagnostic_code)}</code> — "
        f"{escape_html(item.message)}"
        "</li>"
        for item in section.diagnostics
    )
    diagnostics_block = (
        f"<details><summary>Diagnostics "
        f"({section.diagnostics_displayed} of {section.diagnostics_total})"
        "</summary><ul>"
        f"{diagnostics}"
        "</ul></details>"
        if section.diagnostics
        else ""
    )
    limitations = "".join(
        f"<li><strong>{escape_html(item.category)}</strong> — {escape_html(item.summary)}</li>"
        for item in section.limitations
    )
    limitations_block = f"<ul>{limitations}</ul>" if limitations else ""
    finding_trace = (
        "<p class='muted'>Finding IDs: "
        + (
            ", ".join(
                f"<code>{escape_html(finding_id)}</code>"
                for finding_id in section.traceability.finding_ids
            )
            or "—"
        )
        + "</p>"
    )
    trace = (
        f"<p>{escape_html(section.traceability.summary)}</p>"
        f"{finding_trace}"
        "<details><summary>Sample relationships</summary><ul>"
        + "".join(
            "<li>"
            f"{escape_html(edge.relation)}: "
            f"<code>{escape_html(edge.source_id)}</code> → "
            f"<code>{escape_html(edge.target_id)}</code>"
            "</li>"
            for edge in section.traceability.sample_edges
        )
        + "</ul></details>"
        if section.traceability.sample_edges
        or section.traceability.summary
        or section.traceability.finding_ids
        else ""
    )
    pack = (
        f"{escape_html(section.cloud_pack_id or '—')}@"
        f"{escape_html(section.cloud_pack_version or '—')}"
    )
    parts = [
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>",
        f"<p><strong>Pack:</strong> {pack}</p>",
        "<h3>Overall Cloud Posture</h3>",
        f"<p>{escape_html(section.overall_posture_summary or section.executive_summary)}</p>",
        "<h3>Executive Summary</h3>",
        f"<p>{escape_html(section.executive_summary)}</p>",
        "<h3>Assessment and Coverage Status</h3>",
        f"<p><strong>Assessment status:</strong> {escape_html(section.assessment_status)}</p>",
        f"<p><strong>Synthesis status:</strong> {escape_html(section.synthesis_status)}</p>",
        f"<p class='muted'>Evidence pipeline: "
        f"{escape_html(coverage.evidence_pipeline or '—')} · "
        f"Evidence status: {escape_html(coverage.evidence_status or '—')}</p>",
        coverage_table,
        "<h3>Rule Execution Summary</h3>",
        execution_table,
        "<h3>Technology Family Inventory</h3>",
        family_table,
        "<h3>Finding Inventory Summary</h3>",
        bucket_block,
        inventory_body,
    ]
    if themes:
        parts.extend(
            [
                "<h3>Themes</h3>",
                f"<p class='muted'>Showing {section.themes_displayed} of "
                f"{section.themes_total}</p>",
                themes,
            ]
        )
    if conclusions:
        parts.extend(
            [
                "<h3>Conclusions</h3>",
                f"<p class='muted'>Showing {section.conclusions_displayed} of "
                f"{section.conclusions_total}</p>",
                conclusions,
            ]
        )
    if recommendations:
        parts.extend(
            [
                "<h3>Recommendations</h3>",
                f"<p class='muted'>Showing {section.recommendations_displayed} of "
                f"{section.recommendations_total}</p>",
                recommendations,
            ]
        )
    if diagnostics_block:
        parts.extend(["<h3>Diagnostics</h3>", diagnostics_block])
    if limitations_block:
        parts.extend(["<h3>Limitations</h3>", limitations_block])
    if trace:
        parts.extend(["<h3>Traceability</h3>", trace])
    return "\n".join(parts)


def _render_ai_readiness(section: AiReadinessReportSection) -> str:
    coverage = section.coverage_summary
    execution = section.execution_summary
    inventory = section.inventory_summary
    families = section.capability_family_summary
    coverage_rows = "".join(
        "<tr>"
        f"<td><code>{escape_html(area.area_id)}</code></td>"
        f"<td>{escape_html(area.status)}</td>"
        f"<td>{area.numerator if area.numerator is not None else '—'}"
        f" / {area.denominator if area.denominator is not None else '—'}</td>"
        f"<td>{escape_html(area.maturity)}</td>"
        "</tr>"
        for area in coverage.areas
    )
    coverage_table = (
        "<table><thead><tr><th>Area</th><th>Status</th>"
        "<th>Numerator / Denominator</th><th>Maturity</th></tr></thead>"
        f"<tbody>{coverage_rows or '<tr><td colspan="4">—</td></tr>'}"
        "</tbody></table>"
        f"<p class='muted'>{escape_html(coverage.note)}</p>"
    )
    execution_rows = (
        "<tr><td>Rules planned / executed</td>"
        f"<td>{execution.rules_planned} / {execution.rules_executed}</td></tr>"
        "<tr><td>Matched / not matched / not applicable / failed</td>"
        f"<td>{execution.rules_matched} / {execution.rules_not_matched} / "
        f"{execution.rules_not_applicable} / {execution.rules_failed}</td></tr>"
        "<tr><td>Findings / themes / conclusions / recommendations</td>"
        f"<td>{execution.total_finding_count} / {execution.theme_count} / "
        f"{execution.conclusion_count} / {execution.recommendation_count}</td></tr>"
    )
    rule_rows = "".join(
        "<tr>"
        f"<td><code>{escape_html(item.rule_id)}</code></td>"
        f"<td>{'yes' if item.executed else 'no'}</td>"
        f"<td>{escape_html(item.evaluation_status)}</td>"
        f"<td>{item.finding_count}</td>"
        "</tr>"
        for item in execution.entries
    )
    execution_table = (
        "<table><thead><tr><th>Metric</th><th>Value</th></tr></thead>"
        f"<tbody>{execution_rows}</tbody></table>"
        + (
            "<table><thead><tr><th>Rule</th><th>Executed</th>"
            "<th>Status</th><th>Findings</th></tr></thead>"
            f"<tbody>{rule_rows}</tbody></table>"
            if rule_rows
            else ""
        )
        + f"<p class='muted'>{escape_html(execution.note)}</p>"
    )
    family_rows = "".join(
        "<tr>"
        f"<td><code>{escape_html(item.family_id)}</code></td>"
        f"<td>{'yes' if item.observed else 'no'}</td>"
        f"<td>{item.finding_count}</td>"
        f"<td>{escape_html(', '.join(item.signals) or '—')}</td>"
        "</tr>"
        for item in families.entries
    )
    family_table = (
        f"<p class='muted'>Observed {families.families_observed} of "
        f"{families.families_total} capability families.</p>"
        "<table><thead><tr><th>Family</th><th>Observed</th>"
        "<th>Findings</th><th>Signals</th></tr></thead>"
        f"<tbody>{family_rows or '<tr><td colspan="4">—</td></tr>'}"
        "</tbody></table>"
        f"<p class='muted'>{escape_html(families.note)}</p>"
    )
    bucket_block = (
        "<p class='muted'>By rule: "
        + escape_html(", ".join(f"{item.key}={item.count}" for item in inventory.by_rule) or "—")
        + "</p><p class='muted'>By severity: "
        + escape_html(
            ", ".join(f"{item.key}={item.count}" for item in inventory.by_severity) or "—"
        )
        + "</p><p class='muted'>By confidence: "
        + escape_html(
            ", ".join(f"{item.key}={item.count}" for item in inventory.by_confidence) or "—"
        )
        + "</p>"
    )
    if inventory.finding_count == 0 and inventory.none_detected_statement:
        inventory_body = f"<p>{escape_html(inventory.none_detected_statement)}</p>"
    else:
        inventory_body = (
            "<p class='muted'>Finding IDs "
            f"(showing {inventory.finding_ids_displayed} of "
            f"{inventory.finding_count}):</p><ul>"
            + "".join(
                f"<li><code>{escape_html(finding_id)}</code></li>"
                for finding_id in inventory.finding_ids
            )
            + "</ul>"
        )
    themes = "".join(
        "<article class='card'>"
        f"<h4>{escape_html(item.title)}</h4>"
        f"<p>{escape_html(item.summary)}</p>"
        "<p class='muted'>"
        f"ID: <code>{escape_html(item.theme_id)}</code> · "
        f"Kind: {escape_html(item.kind)} · "
        f"Scope: {escape_html(item.scope)} · "
        f"Findings: {item.finding_count}"
        "</p></article>"
        for item in section.themes
    )
    conclusions = "".join(
        "<article class='card'>"
        f"<h4>{escape_html(item.title)}</h4>"
        f"<p>{escape_html(item.summary)}</p>"
        "<p class='muted'>"
        f"ID: <code>{escape_html(item.conclusion_id)}</code> · "
        f"Kind: {escape_html(item.kind)} · "
        f"Audience: {escape_html(item.audience)} · "
        f"Confidence: {escape_html(item.confidence)} · "
        f"Findings: {item.finding_count}"
        "</p></article>"
        for item in section.conclusions
    )
    if section.recommendation_groups:
        recommendations = "".join(
            f"<h4>{escape_html(group.group)}</h4>"
            + "".join(
                "<article class='card'>"
                f"<h5>{escape_html(item.title)}</h5>"
                f"<p><strong>Action:</strong> {escape_html(item.action)}</p>"
                f"<p>{escape_html(item.rationale)}</p>"
                f"<p class='muted'>"
                f"ID: <code>{escape_html(item.recommendation_id)}</code> · "
                f"{'Conditional' if item.conditional else 'Direct'} · "
                f"Audience: {escape_html(item.audience)}"
                + (
                    " · Findings: "
                    + ", ".join(f"<code>{escape_html(fid)}</code>" for fid in item.finding_ids)
                    if item.finding_ids
                    else ""
                )
                + "</p></article>"
                for item in group.recommendations
            )
            for group in section.recommendation_groups
        )
    else:
        recommendations = "".join(
            "<article class='card'>"
            f"<h4>{escape_html(item.title)}</h4>"
            f"<p><strong>Action:</strong> {escape_html(item.action)}</p>"
            f"<p>{escape_html(item.rationale)}</p>"
            f"<p class='muted'>"
            f"ID: <code>{escape_html(item.recommendation_id)}</code>"
            "</p></article>"
            for item in section.recommendations
        )
    diagnostics = "".join(
        "<li>"
        f"<code>{escape_html(item.origin)}</code> · "
        f"<code>{escape_html(item.diagnostic_code)}</code> — "
        f"{escape_html(item.message)}"
        "</li>"
        for item in section.diagnostics
    )
    diagnostics_block = (
        f"<details><summary>Diagnostics "
        f"({section.diagnostics_displayed} of {section.diagnostics_total})"
        "</summary><ul>"
        f"{diagnostics}"
        "</ul></details>"
        if section.diagnostics
        else ""
    )
    limitations = "".join(
        f"<li><strong>{escape_html(item.category)}</strong> — {escape_html(item.summary)}</li>"
        for item in section.limitations
    )
    limitations_block = f"<ul>{limitations}</ul>" if limitations else ""
    finding_trace = (
        "<p class='muted'>Finding IDs: "
        + (
            ", ".join(
                f"<code>{escape_html(finding_id)}</code>"
                for finding_id in section.traceability.finding_ids
            )
            or "—"
        )
        + "</p>"
    )
    trace = (
        f"<p>{escape_html(section.traceability.summary)}</p>"
        f"{finding_trace}"
        "<details><summary>Sample relationships</summary><ul>"
        + "".join(
            "<li>"
            f"{escape_html(edge.relation)}: "
            f"<code>{escape_html(edge.source_id)}</code> → "
            f"<code>{escape_html(edge.target_id)}</code>"
            "</li>"
            for edge in section.traceability.sample_edges
        )
        + "</ul></details>"
        if section.traceability.sample_edges
        or section.traceability.summary
        or section.traceability.finding_ids
        else ""
    )
    pack = (
        f"{escape_html(section.ai_readiness_pack_id or '—')}@"
        f"{escape_html(section.ai_readiness_pack_version or '—')}"
    )
    parts = [
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>",
        f"<p><strong>Pack:</strong> {pack}</p>",
        "<h3>Overall AI Readiness Posture</h3>",
        f"<p>{escape_html(section.overall_posture_summary or section.executive_summary)}</p>",
        "<h3>Executive Summary</h3>",
        f"<p>{escape_html(section.executive_summary)}</p>",
        "<h3>Assessment and Coverage Status</h3>",
        f"<p><strong>Assessment status:</strong> {escape_html(section.assessment_status)}</p>",
        f"<p><strong>Synthesis status:</strong> {escape_html(section.synthesis_status)}</p>",
        f"<p class='muted'>Evidence pipeline: "
        f"{escape_html(coverage.evidence_pipeline or '—')} · "
        f"Evidence status: {escape_html(coverage.evidence_status or '—')}</p>",
        coverage_table,
        "<h3>Rule Execution Summary</h3>",
        execution_table,
        "<h3>Capability Family Inventory</h3>",
        family_table,
        "<h3>Finding Inventory Summary</h3>",
        bucket_block,
        inventory_body,
    ]
    if themes:
        parts.extend(
            [
                "<h3>Themes</h3>",
                f"<p class='muted'>Showing {section.themes_displayed} of "
                f"{section.themes_total}</p>",
                themes,
            ]
        )
    if conclusions:
        parts.extend(
            [
                "<h3>Conclusions</h3>",
                f"<p class='muted'>Showing {section.conclusions_displayed} of "
                f"{section.conclusions_total}</p>",
                conclusions,
            ]
        )
    if recommendations:
        parts.extend(
            [
                "<h3>Recommendations</h3>",
                f"<p class='muted'>Showing {section.recommendations_displayed} of "
                f"{section.recommendations_total}</p>",
                recommendations,
            ]
        )
    if diagnostics_block:
        parts.extend(["<h3>Diagnostics</h3>", diagnostics_block])
    if limitations_block:
        parts.extend(["<h3>Limitations</h3>", limitations_block])
    if trace:
        parts.extend(["<h3>Traceability</h3>", trace])
    return "\n".join(parts)


def _render_phased_roadmap(section: RoadmapReportSection) -> str:
    phase_blocks: list[str] = []
    for phase in section.phases:
        cards = (
            "".join(
                (
                    "<article class='card'>"
                    f"<h4>{escape_html(item.title)}</h4>"
                    f"<p>{escape_html(item.summary)}</p>"
                    '<div class="chip-row">'
                    f'<span class="chip"><em>Priority</em> {escape_html(item.priority)}</span>'
                    f'<span class="chip"><em>Effort</em> {escape_html(item.effort)}</span>'
                    f'<span class="chip"><em>Risk</em> {escape_html(item.risk)}</span>'
                    f'<span class="chip"><em>Confidence</em> {escape_html(item.confidence)}</span>'
                    "</div>"
                    f"<p><strong>Expected outcome:</strong> "
                    f"{escape_html(item.expected_outcome)}</p>"
                    "<p class='ids'><strong>Recommendations:</strong> "
                    f"{_id_list(item.supporting_recommendation_ids) or '—'}</p>"
                    "<p class='ids'><strong>Findings:</strong> "
                    f"{_id_list(item.supporting_finding_ids) or '—'}</p>"
                    "<p class='ids'><strong>Depends on:</strong> "
                    f"{_id_list(item.depends_on_initiative_ids) or '—'}</p>"
                    "</article>"
                )
                for item in phase.initiatives
            )
            or "<p class='muted'>No initiatives in this phase.</p>"
        )
        phase_blocks.append(
            "<div class='roadmap-lane'>"
            f"<h3>{escape_html(phase.title)} "
            f"<span class='count-pill'>{len(phase.initiatives)}</span></h3>"
            f"<p class='muted'>{escape_html(phase.objective)}</p>"
            f"<div class='card-stack'>{cards}</div>"
            "</div>"
        )
    assumptions = "".join(f"<li>{escape_html(item)}</li>" for item in section.assumptions)
    limitations = "".join(f"<li>{escape_html(item)}</li>" for item in section.limitations)
    body = (
        "".join(phase_blocks)
        if phase_blocks
        else "<p class='muted'>No phased modernization initiatives were derived.</p>"
    )
    truncated = ""
    if section.initiatives_displayed < section.initiatives_total:
        truncated = (
            f"<p class='muted'>Showing {section.initiatives_displayed} of "
            f"{section.initiatives_total} initiatives.</p>"
        )
    return "\n".join(
        [
            f"<p><strong>Status:</strong> {escape_html(section.status_label)}</p>",
            f"<p>{escape_html(section.summary)}</p>",
            f"<p><strong>Confidence:</strong> {escape_html(section.confidence)}</p>",
            truncated,
            f"<div class='roadmap'>{body}</div>",
            ("<h3>Assumptions</h3><ul>" + assumptions + "</ul>") if assumptions else "",
            ("<h3>Limitations</h3><ul>" + limitations + "</ul>") if limitations else "",
        ]
    )


def _render_performance(section: PerformanceReportSection) -> str:
    coverage = section.coverage_summary
    execution = section.execution_summary
    inventory = section.inventory_summary
    families = section.performance_family_summary
    coverage_rows = "".join(
        "<tr>"
        f"<td><code>{escape_html(area.area_id)}</code></td>"
        f"<td>{escape_html(area.status)}</td>"
        f"<td>{area.numerator if area.numerator is not None else '—'}"
        f" / {area.denominator if area.denominator is not None else '—'}</td>"
        f"<td>{escape_html(area.maturity)}</td>"
        "</tr>"
        for area in coverage.areas
    )
    coverage_table = (
        "<table><thead><tr><th>Area</th><th>Status</th>"
        "<th>Numerator / Denominator</th><th>Maturity</th></tr></thead>"
        f"<tbody>{coverage_rows or '<tr><td colspan="4">—</td></tr>'}"
        "</tbody></table>"
        f"<p class='muted'>{escape_html(coverage.note)}</p>"
    )
    execution_rows = (
        "<tr><td>Rules planned / executed</td>"
        f"<td>{execution.rules_planned} / {execution.rules_executed}</td></tr>"
        "<tr><td>Matched / not matched / not applicable / failed</td>"
        f"<td>{execution.rules_matched} / {execution.rules_not_matched} / "
        f"{execution.rules_not_applicable} / {execution.rules_failed}</td></tr>"
        "<tr><td>Findings / themes / conclusions / recommendations</td>"
        f"<td>{execution.total_finding_count} / {execution.theme_count} / "
        f"{execution.conclusion_count} / {execution.recommendation_count}</td></tr>"
    )
    rule_rows = "".join(
        "<tr>"
        f"<td><code>{escape_html(item.rule_id)}</code></td>"
        f"<td>{'yes' if item.executed else 'no'}</td>"
        f"<td>{escape_html(item.evaluation_status)}</td>"
        f"<td>{item.finding_count}</td>"
        "</tr>"
        for item in execution.entries
    )
    execution_table = (
        "<table><thead><tr><th>Metric</th><th>Value</th></tr></thead>"
        f"<tbody>{execution_rows}</tbody></table>"
        + (
            "<table><thead><tr><th>Rule</th><th>Executed</th>"
            "<th>Status</th><th>Findings</th></tr></thead>"
            f"<tbody>{rule_rows}</tbody></table>"
            if rule_rows
            else ""
        )
        + f"<p class='muted'>{escape_html(execution.note)}</p>"
    )
    family_rows = "".join(
        "<tr>"
        f"<td><code>{escape_html(item.family_id)}</code></td>"
        f"<td>{'yes' if item.observed else 'no'}</td>"
        f"<td>{item.finding_count}</td>"
        f"<td>{escape_html(', '.join(item.signals) or '—')}</td>"
        "</tr>"
        for item in families.entries
    )
    family_table = (
        f"<p class='muted'>Observed {families.families_observed} of "
        f"{families.families_total} performance families.</p>"
        "<table><thead><tr><th>Family</th><th>Observed</th>"
        "<th>Findings</th><th>Signals</th></tr></thead>"
        f"<tbody>{family_rows or '<tr><td colspan="4">—</td></tr>'}"
        "</tbody></table>"
        f"<p class='muted'>{escape_html(families.note)}</p>"
    )
    bucket_block = (
        "<p class='muted'>By rule: "
        + escape_html(", ".join(f"{item.key}={item.count}" for item in inventory.by_rule) or "—")
        + "</p><p class='muted'>By severity: "
        + escape_html(
            ", ".join(f"{item.key}={item.count}" for item in inventory.by_severity) or "—"
        )
        + "</p><p class='muted'>By confidence: "
        + escape_html(
            ", ".join(f"{item.key}={item.count}" for item in inventory.by_confidence) or "—"
        )
        + "</p>"
    )
    if inventory.finding_count == 0 and inventory.none_detected_statement:
        inventory_body = f"<p>{escape_html(inventory.none_detected_statement)}</p>"
    else:
        inventory_body = (
            "<p class='muted'>Finding IDs "
            f"(showing {inventory.finding_ids_displayed} of "
            f"{inventory.finding_count}):</p><ul>"
            + "".join(
                f"<li><code>{escape_html(finding_id)}</code></li>"
                for finding_id in inventory.finding_ids
            )
            + "</ul>"
        )
    themes = "".join(
        "<article class='card'>"
        f"<h4>{escape_html(item.title)}</h4>"
        f"<p>{escape_html(item.summary)}</p>"
        "<p class='muted'>"
        f"ID: <code>{escape_html(item.theme_id)}</code> · "
        f"Kind: {escape_html(item.kind)} · "
        f"Scope: {escape_html(item.scope)} · "
        f"Findings: {item.finding_count}"
        "</p></article>"
        for item in section.themes
    )
    conclusions = "".join(
        "<article class='card'>"
        f"<h4>{escape_html(item.title)}</h4>"
        f"<p>{escape_html(item.summary)}</p>"
        "<p class='muted'>"
        f"ID: <code>{escape_html(item.conclusion_id)}</code> · "
        f"Kind: {escape_html(item.kind)} · "
        f"Audience: {escape_html(item.audience)} · "
        f"Confidence: {escape_html(item.confidence)} · "
        f"Findings: {item.finding_count}"
        "</p></article>"
        for item in section.conclusions
    )
    if section.recommendation_groups:
        recommendations = "".join(
            f"<h4>{escape_html(group.group)}</h4>"
            + "".join(
                "<article class='card'>"
                f"<h5>{escape_html(item.title)}</h5>"
                f"<p><strong>Action:</strong> {escape_html(item.action)}</p>"
                f"<p>{escape_html(item.rationale)}</p>"
                f"<p class='muted'>"
                f"ID: <code>{escape_html(item.recommendation_id)}</code> · "
                f"{'Conditional' if item.conditional else 'Direct'} · "
                f"Audience: {escape_html(item.audience)}"
                + (
                    " · Findings: "
                    + ", ".join(f"<code>{escape_html(fid)}</code>" for fid in item.finding_ids)
                    if item.finding_ids
                    else ""
                )
                + "</p></article>"
                for item in group.recommendations
            )
            for group in section.recommendation_groups
        )
    else:
        recommendations = "".join(
            "<article class='card'>"
            f"<h4>{escape_html(item.title)}</h4>"
            f"<p><strong>Action:</strong> {escape_html(item.action)}</p>"
            f"<p>{escape_html(item.rationale)}</p>"
            f"<p class='muted'>"
            f"ID: <code>{escape_html(item.recommendation_id)}</code>"
            "</p></article>"
            for item in section.recommendations
        )
    diagnostics = "".join(
        "<li>"
        f"<code>{escape_html(item.origin)}</code> · "
        f"<code>{escape_html(item.diagnostic_code)}</code> — "
        f"{escape_html(item.message)}"
        "</li>"
        for item in section.diagnostics
    )
    diagnostics_block = (
        f"<details><summary>Diagnostics "
        f"({section.diagnostics_displayed} of {section.diagnostics_total})"
        "</summary><ul>"
        f"{diagnostics}"
        "</ul></details>"
        if section.diagnostics
        else ""
    )
    limitations = "".join(
        f"<li><strong>{escape_html(item.category)}</strong> — {escape_html(item.summary)}</li>"
        for item in section.limitations
    )
    limitations_block = f"<ul>{limitations}</ul>" if limitations else ""
    finding_trace = (
        "<p class='muted'>Finding IDs: "
        + (
            ", ".join(
                f"<code>{escape_html(finding_id)}</code>"
                for finding_id in section.traceability.finding_ids
            )
            or "—"
        )
        + "</p>"
    )
    trace = (
        f"<p>{escape_html(section.traceability.summary)}</p>"
        f"{finding_trace}"
        "<details><summary>Sample relationships</summary><ul>"
        + "".join(
            "<li>"
            f"{escape_html(edge.relation)}: "
            f"<code>{escape_html(edge.source_id)}</code> → "
            f"<code>{escape_html(edge.target_id)}</code>"
            "</li>"
            for edge in section.traceability.sample_edges
        )
        + "</ul></details>"
        if section.traceability.sample_edges
        or section.traceability.summary
        or section.traceability.finding_ids
        else ""
    )
    pack = (
        f"{escape_html(section.performance_pack_id or '—')}@"
        f"{escape_html(section.performance_pack_version or '—')}"
    )
    parts = [
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>",
        f"<p><strong>Pack:</strong> {pack}</p>",
        "<h3>Overall Performance Posture</h3>",
        f"<p>{escape_html(section.overall_posture_summary or section.executive_summary)}</p>",
        "<h3>Executive Summary</h3>",
        f"<p>{escape_html(section.executive_summary)}</p>",
        "<h3>Assessment and Coverage Status</h3>",
        f"<p><strong>Assessment status:</strong> {escape_html(section.assessment_status)}</p>",
        f"<p><strong>Synthesis status:</strong> {escape_html(section.synthesis_status)}</p>",
        f"<p class='muted'>Evidence pipeline: "
        f"{escape_html(coverage.evidence_pipeline or '—')} · "
        f"Evidence status: {escape_html(coverage.evidence_status or '—')}</p>",
        coverage_table,
        "<h3>Rule Execution Summary</h3>",
        execution_table,
        "<h3>Performance Family Inventory</h3>",
        family_table,
        "<h3>Finding Inventory Summary</h3>",
        bucket_block,
        inventory_body,
    ]
    if themes:
        parts.extend(
            [
                "<h3>Themes</h3>",
                f"<p class='muted'>Showing {section.themes_displayed} of "
                f"{section.themes_total}</p>",
                themes,
            ]
        )
    if conclusions:
        parts.extend(
            [
                "<h3>Conclusions</h3>",
                f"<p class='muted'>Showing {section.conclusions_displayed} of "
                f"{section.conclusions_total}</p>",
                conclusions,
            ]
        )
    if recommendations:
        parts.extend(
            [
                "<h3>Recommendations</h3>",
                f"<p class='muted'>Showing {section.recommendations_displayed} of "
                f"{section.recommendations_total}</p>",
                recommendations,
            ]
        )
    if diagnostics_block:
        parts.extend(["<h3>Diagnostics</h3>", diagnostics_block])
    if limitations_block:
        parts.extend(["<h3>Limitations</h3>", limitations_block])
    if trace:
        parts.extend(["<h3>Traceability</h3>", trace])
    return "\n".join(parts)


def _render_ai(ai: AiEnrichmentView) -> str:
    themes = (
        "".join(
            "<li>"
            f"<strong>{escape_html(theme.title)}</strong> — {escape_html(theme.summary)}"
            f"<div class='ids'>Findings: {_id_list(theme.related_finding_ids) or '—'}"
            f" · Recommendations: {_id_list(theme.related_recommendation_ids) or '—'}</div>"
            "</li>"
            for theme in ai.themes
        )
        or "<li>None</li>"
    )
    priorities = (
        "".join(
            "<li>"
            f'<span class="badge priority-{escape_html(item.priority)}">'
            f"{escape_html(item.priority)}</span> "
            f"<strong>{escape_html(item.title)}</strong> — {escape_html(item.rationale)}"
            f"<div class='ids'>Findings: {_id_list(item.related_finding_ids) or '—'}"
            f" · Recommendations: {_id_list(item.related_recommendation_ids) or '—'}</div>"
            "</li>"
            for item in ai.priorities
        )
        or "<li>None</li>"
    )
    risks = (
        "".join(
            "<li>"
            f'<span class="badge severity-{escape_html(item.severity)}">'
            f"{escape_html(item.severity)}</span> "
            f"<strong>{escape_html(item.title)}</strong> — {escape_html(item.summary)}"
            "</li>"
            for item in ai.risks
        )
        or "<li>None</li>"
    )
    steps = (
        "".join(
            f"<li><strong>{step.order}. {escape_html(step.title)}</strong> — "
            f"{escape_html(step.summary)}</li>"
            for step in ai.suggested_next_steps
        )
        or "<li>None</li>"
    )
    limitations = "".join(f"<li>{escape_html(item)}</li>" for item in ai.limitations) or (
        "<li>None</li>"
    )
    posture = f"<p><strong>Posture:</strong> {escape_html(ai.posture)}</p>" if ai.posture else ""
    return (
        '<div class="ai-panel">\n'
        f'<p class="ai-banner">{escape_html(ai.disclaimer)}</p>\n'
        f'<h3 class="ai-headline">{escape_html(ai.headline)}</h3>\n'
        f"<p>{escape_html(ai.narrative)}</p>\n"
        f"{posture}"
        "<h4>Modernization themes</h4>\n"
        f"<ul>{themes}</ul>\n"
        "<h4>Top priorities</h4>\n"
        f"<ul>{priorities}</ul>\n"
        "<h4>Major risks</h4>\n"
        f"<ul>{risks}</ul>\n"
        "<h4>Suggested next steps</h4>\n"
        f"<ol>{steps}</ol>\n"
        "<h4>Referenced IDs</h4>\n"
        f"<p>Findings: {_id_list(ai.referenced_finding_ids) or '—'}</p>\n"
        f"<p>Recommendations: {_id_list(ai.referenced_recommendation_ids) or '—'}</p>\n"
        "<h4>Provider metadata</h4>\n"
        '<dl class="meta">\n'
        f"<div><dt>Provider</dt><dd>{escape_html(ai.provider)}</dd></div>\n"
        f"<div><dt>Model</dt><dd>{escape_html(ai.model_id)}</dd></div>\n"
        f"<div><dt>Request ID</dt><dd>{escape_html(ai.request_id or '—')}</dd></div>\n"
        "<div><dt>Latency (ms)</dt><dd>"
        f"{ai.latency_ms if ai.latency_ms is not None else '—'}"
        "</dd></div>\n"
        f"<div><dt>Tokens in/out</dt><dd>"
        f"{ai.input_tokens if ai.input_tokens is not None else '—'} / "
        f"{ai.output_tokens if ai.output_tokens is not None else '—'}</dd></div>\n"
        "</dl>\n"
        "<h4>Limitations</h4>\n"
        f"<ul>{limitations}</ul>\n"
        "</div>"
    )


def _render_technical_details(view: HtmlReportViewModel) -> str:
    findings_body = (
        "\n".join(_render_finding_card(item, compact=False) for item in view.findings)
        if view.findings
        else (
            '<p class="muted">No deterministic findings were produced for this run. '
            "This does not certify that the repository is free of issues.</p>"
        )
    )
    recommendations_body = (
        "\n".join(_render_recommendation_card(item, compact=False) for item in view.recommendations)
        if view.recommendations
        else ('<p class="muted">No deterministic recommendations were produced for this run.</p>')
    )
    return (
        '<details class="tech-block" id="repository" open>\n'
        "<summary>Repository Profile</summary>\n"
        f"{_render_repository(view)}\n"
        "</details>\n"
        '<details class="tech-block" id="assessment-summary">\n'
        "<summary>Assessment Summary</summary>\n"
        f"{_render_assessment_summary(view)}\n"
        "</details>\n"
        '<details class="tech-block" id="findings-full">\n'
        "<summary>All Findings (with evidence)</summary>\n"
        f"{findings_body}\n"
        "</details>\n"
        '<details class="tech-block" id="recommendations-full">\n'
        "<summary>All Recommendations (with actions)</summary>\n"
        f"{recommendations_body}\n"
        "</details>\n"
        '<details class="tech-block" id="artifacts">\n'
        "<summary>Graph and Artifact References</summary>\n"
        f"{_render_artifacts(view)}\n"
        "</details>\n"
        '<details class="tech-block" id="metadata">\n'
        "<summary>Assessment Metadata</summary>\n"
        f"{_render_metadata(view)}\n"
        "</details>\n"
        f'<p class="provenance">{escape_html(view.provenance_note)}</p>'
    )


def _render_repository(view: HtmlReportViewModel) -> str:
    repo = view.repository
    rows = [
        ("Name", escape_and_wrap(repo.name)),
        ("Source", escape_html(repo.source_type)),
        ("Files", str(repo.file_count)),
    ]
    if repo.reference:
        rows.append(("Reference", escape_and_wrap(repo.reference)))
    if repo.default_branch:
        rows.append(("Default branch", escape_html(repo.default_branch)))
    return _definition_list(rows)


def _render_assessment_summary(view: HtmlReportViewModel) -> str:
    summary = view.assessment_summary
    sev = (
        "".join(
            f"<li>{escape_html(name)}: {count}</li>" for name, count in summary.findings_by_severity
        )
        or "<li>None</li>"
    )
    pri = (
        "".join(
            f"<li>{escape_html(name)}: {count}</li>"
            for name, count in summary.recommendations_by_priority
        )
        or "<li>None</li>"
    )
    return (
        f"<p>{escape_html(summary.summary_text)}</p>\n"
        '<div class="split">\n'
        "<div>\n"
        f"<p><strong>Rules evaluated:</strong> {summary.rules_evaluated}</p>\n"
        f"<p><strong>Findings:</strong> {summary.findings_count}</p>\n"
        f"<p><strong>Recommendations:</strong> {summary.recommendations_count}</p>\n"
        "</div>\n"
        "<div>\n<h3>By severity</h3>\n"
        f'<ul class="plain">{sev}</ul>\n'
        "<h3>By priority</h3>\n"
        f'<ul class="plain">{pri}</ul>\n</div>\n'
        "</div>"
    )


def _render_artifacts(view: HtmlReportViewModel) -> str:
    if not view.artifacts:
        return '<p class="muted">No artifact references recorded.</p>'
    rows = "".join(
        "<tr>"
        f"<td>{escape_html(item.label)}</td>"
        f"<td><code>{escape_and_wrap(item.relative_path)}</code></td>"
        "</tr>"
        for item in view.artifacts
    )
    return (
        '<div class="table-wrap"><table>\n'
        "<thead><tr><th>Artifact</th><th>Relative path</th></tr></thead>\n"
        f"<tbody>{rows}</tbody>\n</table></div>"
    )


def _render_metadata(view: HtmlReportViewModel) -> str:
    meta = view.metadata
    warnings = "".join(f"<li>{escape_html(item)}</li>" for item in meta.warnings) or (
        "<li>None</li>"
    )
    rows = [
        ("Generated at (UTC)", escape_html(meta.generated_at_utc)),
        ("Report title", escape_html(BRAND_REPORT_NAME)),
        ("Report version", escape_html(meta.report_version)),
        ("AI status", escape_html(meta.ai_status)),
        ("Model ID", escape_html(meta.model_id or "—")),
        ("Total ms", _fmt_ms(meta.timing_total_ms)),
        ("Scan ms", _fmt_ms(meta.timing_scan_ms)),
        ("Analysis ms", _fmt_ms(meta.timing_analysis_ms)),
        ("AI ms", _fmt_ms(meta.timing_ai_ms)),
        ("Report ms", _fmt_ms(meta.timing_report_ms)),
    ]
    if meta.organization_name:
        rows.insert(2, ("Organization", escape_html(meta.organization_name)))
    if meta.confidentiality_notice:
        rows.append(("Confidentiality", escape_html(meta.confidentiality_notice)))
    return _definition_list(rows) + f"\n<h3>Warnings</h3>\n<ul>{warnings}</ul>"


def _render_footer() -> str:
    return (
        '<footer class="site-footer">\n'
        f"<p>{escape_html(BRAND_FOOTER_LINE)}</p>\n"
        f"<p>Version {escape_html(BRAND_VERSION)}</p>\n"
        f'<p class="copyright">© {escape_html(BRAND_NAME)}</p>\n'
        "</footer>"
    )


def _render_evidence_details(evidence: tuple[object, ...]) -> str:
    if not evidence:
        return (
            '<details class="evidence"><summary>Evidence</summary>'
            '<p class="muted">None</p></details>'
        )
    items = []
    for ev in evidence:
        path = getattr(ev, "path", None)
        excerpt = getattr(ev, "excerpt", None)
        node_id = getattr(ev, "node_id", None)
        bits = [
            f"<strong>{escape_html(getattr(ev, 'evidence_type', 'evidence'))}</strong>",
            f"<code>{escape_and_wrap(str(getattr(ev, 'source_id', '')))}</code>",
        ]
        if path:
            bits.append(f"path <code>{escape_and_wrap(path)}</code>")
        if node_id:
            bits.append(f"node <code>{escape_and_wrap(node_id)}</code>")
        if excerpt:
            bits.append(escape_html(excerpt))
        items.append(f"<li>{' — '.join(bits)}</li>")
    return (
        f'<details class="evidence"><summary>Evidence</summary><ul>{"".join(items)}</ul></details>'
    )


def _id_list(values: tuple[str, ...]) -> str:
    if not values:
        return ""
    return " ".join(f"<code>{escape_and_wrap(item)}</code>" for item in values)


def _finding_id_links(values: tuple[str, ...]) -> str:
    """Render related finding IDs as in-page links for leadership traceability."""

    if not values:
        return ""
    return " ".join(
        f'<a class="id-link" href="#finding-{escape_html(item)}">'
        f"<code>{escape_and_wrap(item)}</code></a>"
        for item in values
    )


def _definition_list(rows: list[tuple[str, str]]) -> str:
    body = "".join(
        f"<div><dt>{escape_html(label)}</dt><dd>{value}</dd></div>" for label, value in rows
    )
    return f'<dl class="meta">{body}</dl>'


def _fmt_ms(value: float | None) -> str:
    if value is None:
        return "—"
    return str(value)


_CSS = """
:root {
  --bg: #f4f6f8;
  --surface: #ffffff;
  --ink: #1a1f24;
  --muted: #5b6773;
  --border: #e2e8ee;
  --accent: #b57b48;
  --accent-soft: #f6efe8;
  --teal: #68a691;
  --shadow: 0 10px 30px rgba(26, 31, 36, 0.06);
  --radius: 14px;
  --critical: #b42318;
  --high: #c4320a;
  --medium: #a15c07;
  --low: #0f7b6c;
  --info: #3e4c59;
  --ai: #0b6e99;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background:
    radial-gradient(1200px 500px at 10% -10%, #efe6dc 0%, transparent 55%),
    radial-gradient(900px 400px at 100% 0%, #e7eef2 0%, transparent 50%),
    var(--bg);
  color: var(--ink);
  font: 15px/1.55 "Source Sans 3", "IBM Plex Sans", "Segoe UI", sans-serif;
}
.page { max-width: 1120px; margin: 0 auto; padding: 1.75rem 1.25rem 3rem; }
.hero {
  background: linear-gradient(180deg, #fff 0%, #fbfcfd 100%);
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) + 4px);
  box-shadow: var(--shadow);
  padding: 1.5rem 1.6rem 1.35rem;
  margin-bottom: 1.25rem;
}
.hero-brand { margin-bottom: 1.1rem; }
.brand-logo {
  display: block;
  width: 140px;
  height: 40px;
  max-width: 140px;
  object-fit: contain;
  margin-bottom: 0.85rem;
}
.brand-name {
  margin: 0;
  font-size: 0.95rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--muted);
  font-weight: 650;
}
.report-title {
  margin: 0.2rem 0 0;
  font-size: clamp(1.55rem, 2.4vw, 2.05rem);
  line-height: 1.15;
  letter-spacing: -0.02em;
  color: var(--ink);
  font-family: "Fraunces", "Iowan Old Style", Georgia, serif;
  font-weight: 650;
}
.hero-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.1rem;
  padding: 0.85rem 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}
.meta-item { display: flex; flex-direction: column; gap: 0.15rem; }
.meta-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
  font-weight: 650;
}
.meta-value { font-weight: 650; word-break: break-word; }
.hero-kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
}
.kpi {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.9rem 1rem;
}
.kpi-label {
  margin: 0;
  color: var(--muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 650;
}
.kpi-value {
  margin: 0.35rem 0 0;
  font-size: 1.55rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.kpi-hint { color: var(--muted); font-size: 0.85rem; }
.kpi-score .kpi-value { color: var(--teal); }
.kpi-severity-critical .kpi-value { color: var(--critical); }
.kpi-severity-high .kpi-value { color: var(--high); }
.kpi-severity-medium .kpi-value { color: var(--medium); }
.kpi-severity-low .kpi-value { color: var(--low); }
.kpi-severity-informational .kpi-value,
.kpi-severity-none-detected .kpi-value,
.kpi-severity-unknown .kpi-value { color: var(--info); }
.stat-hint {
  margin: 0.2rem 0 0;
  color: var(--muted);
  font-size: 0.82rem;
}
.section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 1.2rem 1.3rem 1.35rem;
  margin: 0 0 1rem;
}
.section-head h2 {
  margin: 0;
  font-size: 1.15rem;
  letter-spacing: -0.01em;
}
.section-note, .muted, .provenance { color: var(--muted); }
.section-note { margin: 0.35rem 0 0.9rem; font-size: 0.9rem; }
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.75rem;
}
.stat-card {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.9rem 0.95rem;
  background: linear-gradient(180deg, #fff, #fafbfc);
}
.stat-label {
  margin: 0;
  color: var(--muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 650;
}
.stat-value {
  margin: 0.35rem 0 0;
  font-size: 1.45rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.tech-badges { display: flex; flex-wrap: wrap; gap: 0.55rem; margin-bottom: 1rem; }
.tech-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.75rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: #f8fafb;
  font-weight: 650;
}
.tech-badge em {
  font-style: normal;
  color: var(--muted);
  font-weight: 550;
  font-size: 0.85em;
}
.table-card { margin-top: 0.5rem; }
.severity-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.65rem;
  margin-bottom: 1rem;
}
.severity-card {
  border-radius: 12px;
  border: 1px solid var(--border);
  padding: 0.85rem 0.7rem;
  text-align: center;
  background: #fafbfc;
}
.severity-label {
  margin: 0;
  text-transform: uppercase;
  font-size: 0.7rem;
  letter-spacing: 0.06em;
  color: var(--muted);
  font-weight: 700;
}
.severity-count {
  margin: 0.35rem 0 0;
  font-size: 1.6rem;
  font-weight: 750;
}
.severity-critical { background: #fef3f2; }
.severity-critical .severity-count { color: var(--critical); }
.severity-high { background: #fff4ed; }
.severity-high .severity-count { color: var(--high); }
.severity-medium { background: #fffaeb; }
.severity-medium .severity-count { color: var(--medium); }
.severity-low { background: #edfcf7; }
.severity-low .severity-count { color: var(--low); }
.severity-informational { background: #f4f6f8; }
.card-stack { display: grid; gap: 0.7rem; }
.item-card {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.9rem 1rem;
  background: #fff;
}
.item-header { margin-bottom: 0.45rem; }
.card-desc { margin: 0.35rem 0 0.55rem; }
.chip-row { display: flex; flex-wrap: wrap; gap: 0.45rem; margin: 0.35rem 0 0.55rem; }
.chip {
  display: inline-flex;
  gap: 0.35rem;
  align-items: baseline;
  padding: 0.28rem 0.55rem;
  border-radius: 999px;
  background: var(--accent-soft);
  border: 1px solid #ead9c8;
  font-size: 0.82rem;
}
.chip em {
  font-style: normal;
  color: var(--muted);
  font-size: 0.72rem;
  text-transform: uppercase;
}
.outcome { margin: 0; color: var(--ink); }
.outcome em {
  font-style: normal;
  color: var(--muted);
  margin-right: 0.35rem;
  text-transform: uppercase;
  font-size: 0.72rem;
  letter-spacing: 0.04em;
}
.roadmap { display: grid; gap: 1rem; }
.roadmap-lane h3 { margin: 0 0 0.55rem; font-size: 1rem; }
.count-pill {
  display: inline-block;
  margin-left: 0.35rem;
  padding: 0.05rem 0.45rem;
  border-radius: 999px;
  background: #eef2f6;
  color: var(--muted);
  font-size: 0.78rem;
}
.section-ai {
  border-color: #9cc5d9;
  background: linear-gradient(180deg, #f4fafc, #fff);
}
.td-test-observation {
  border-left: 3px solid #9aa7b5;
  background: #f7f8fa;
}
.ai-panel { padding: 0.15rem; }
.ai-banner {
  background: #e6f4f8;
  color: var(--ai);
  border: 1px solid #9cc5d9;
  border-radius: 10px;
  padding: 0.7rem 0.85rem;
  margin: 0 0 0.9rem;
  font-weight: 600;
}
.ai-headline { margin: 0 0 0.45rem; font-size: 1.2rem; }
.badge {
  display: inline-block;
  padding: 0.12rem 0.5rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 750;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.severity-critical,
.priority-immediate,
.priority-critical { background: #fde8e8; color: var(--critical); }
.severity-high, .priority-high { background: #feecdc; color: var(--high); }
.severity-medium, .priority-medium { background: #fbf1de; color: var(--medium); }
.severity-low,
.priority-low,
.severity-informational,
.severity-info { background: #e1f5f0; color: var(--low); }
.meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.35rem 1rem;
  margin: 0.5rem 0;
}
.meta dt {
  font-size: 0.72rem;
  color: var(--muted);
  text-transform: uppercase;
  margin: 0;
  letter-spacing: 0.04em;
}
.meta dd { margin: 0.1rem 0 0; }
code, .cmd {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.85em;
  word-break: break-word;
}
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
th, td {
  border-bottom: 1px solid var(--border);
  text-align: left;
  padding: 0.5rem 0.35rem;
  vertical-align: top;
}
th { color: var(--muted); font-weight: 650; }
.evidence { margin-top: 0.45rem; }
.evidence summary, .tech-block summary {
  cursor: pointer;
  color: var(--ink);
  font-weight: 650;
}
.tech-block {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.75rem 0.9rem;
  margin: 0 0 0.7rem;
  background: #fbfcfd;
}
.tech-block summary { list-style: none; }
.tech-block summary::-webkit-details-marker { display: none; }
.ids { color: var(--muted); font-size: 0.85rem; margin-top: 0.2rem; }
.actions { padding-left: 1.2rem; }
.split { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.plain { margin: 0; padding-left: 1.1rem; }
.more-note { margin-top: 0.75rem; }
.site-footer {
  margin-top: 1.5rem;
  padding: 1.25rem 0.25rem 0.5rem;
  text-align: center;
  color: var(--muted);
  border-top: 1px solid var(--border);
}
.site-footer p { margin: 0.15rem 0; font-size: 0.9rem; }
.site-footer strong { color: var(--ink); }
.copyright { margin-top: 0.45rem !important; opacity: 0.85; }
@media (max-width: 820px) {
  .severity-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .split { grid-template-columns: 1fr; }
}
@media (max-width: 560px) {
  .page { padding: 1rem 0.85rem 2rem; }
}
@media print {
  body { background: #fff; }
  .page { max-width: none; padding: 0; }
  .section, .hero, .item-card { break-inside: avoid; box-shadow: none; }
}
"""
