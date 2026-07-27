"""Self-contained CodeStrata Engineering Assessment HTML report renderer.

Presentation only — no analysis or enrichment business logic.
"""

from __future__ import annotations

from codestrata.reporters.html_rendering import escape_and_wrap, escape_html
from codestrata.reporting.ai_readiness.models import AiReadinessReportSection
from codestrata.reporting.architecture.models import ArchitectureReportSection
from codestrata.reporting.branding import (
    BRAND_FOOTER_LINE,
    BRAND_NAME,
    BRAND_REPORT_NAME,
    BRAND_VERSION,
    logo_data_uri,
)
from codestrata.reporting.cloud.models import CloudReportSection
from codestrata.reporting.dependency.models import DependencyReportSection
from codestrata.reporting.html_v2.models import (
    AiEnrichmentView,
    FindingView,
    HtmlReportViewModel,
    RecommendationView,
)
from codestrata.reporting.performance.models import PerformanceReportSection
from codestrata.reporting.security.models import SecurityReportSection
from codestrata.reporting.technical_debt.models import TechnicalDebtReportSection
from codestrata.reporting.testing.models import TestingReportSection

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
            _render_leadership_verdict(view),
            _render_toc(view),
            _section(
                "Key Takeaways",
                _render_key_takeaways(view),
                section_id="key-takeaways",
                note="Concise leadership bullets for scanning and handoff.",
            ),
            _section(
                "Executive Summary",
                _render_executive_summary(view),
                section_id="executive-summary",
                note="Should I care, why now, and what the team should do next.",
            ),
            _section(
                "Engineering Risks",
                _render_engineering_risks(view),
                section_id="engineering-risks",
                note="Meaningful risks grouped by theme.",
            ),
            _section(
                "Modernization Opportunities",
                _render_modernization_opportunities(view),
                section_id="modernization-opportunities",
                note=(
                    "Improvement opportunities distinct from Priority Actions. "
                    "Priority Actions remain the authoritative action list."
                ),
            ),
            _section(
                "Priority Actions",
                _render_roadmap(
                    view.priority_actions if view.priority_actions else view.recommendations
                ),
                section_id="priority-actions",
                note=(
                    "Priority-ordered actions linked to findings. "
                    "Order matches the Phased Modernization Plan below."
                ),
            ),
            _section(
                "Findings",
                _render_findings_overview(view),
                section_id="findings",
                note=(
                    "Highest-severity findings first. "
                    "Full evidence is in the Technical Appendix."
                ),
            ),
        ]
        capability_parts: list[str] = []
        if view.architecture_report is not None:
            capability_parts.append(
                _subsection(
                    "Architecture Assessment",
                    _render_architecture(view.architecture_report),
                    section_id="architecture-assessment",
                    note="Structural findings and conclusions from repository evidence.",
                )
            )
        if view.technical_debt_report is not None:
            capability_parts.append(
                _subsection(
                    "Technical Debt Assessment",
                    _render_technical_debt(view.technical_debt_report),
                    section_id="technical-debt-assessment",
                    note="Maintainability hotspots and debt themes from repository evidence.",
                )
            )
        if view.dependency_report is not None:
            capability_parts.append(
                _subsection(
                    "Dependency Assessment",
                    _render_dependency(view.dependency_report),
                    section_id="dependency-assessment",
                    note="Declared dependency posture from repository manifests.",
                )
            )
        if view.security_report is not None:
            capability_parts.append(
                _subsection(
                    "Security Assessment",
                    _render_security(view.security_report),
                    section_id="security-assessment",
                    note=(
                        "Repository security signals from available evidence. "
                        "Absence of findings is not a security certification."
                    ),
                )
            )
        if view.testing_report is not None:
            capability_parts.append(
                _subsection(
                    "Testing Assessment",
                    _render_testing(view.testing_report),
                    section_id="testing-assessment",
                    note="Test presence and hygiene signals from repository evidence.",
                )
            )
        if view.cloud_report is not None:
            capability_parts.append(
                _subsection(
                    "Cloud Assessment",
                    _render_cloud(view.cloud_report),
                    section_id="cloud-assessment",
                    note="Cloud and deployment readiness signals from repository evidence.",
                )
            )
        if view.ai_readiness_report is not None:
            capability_parts.append(
                _subsection(
                    "AI Readiness Assessment",
                    _render_ai_readiness(view.ai_readiness_report),
                    section_id="ai-readiness-assessment",
                    note="AI/agent readiness signals from repository evidence.",
                )
            )
        if view.performance_report is not None:
            capability_parts.append(
                _subsection(
                    "Performance Assessment",
                    _render_performance(view.performance_report),
                    section_id="performance-assessment",
                    note="Performance hygiene signals from repository evidence.",
                )
            )
        if capability_parts:
            parts.append(
                '<section class="section section-capability" id="capability-assessments">\n'
                '<div class="section-head"><h2>Capability Assessments</h2></div>\n'
                '<p class="section-note">Detailed assessment packs for engineering follow-up.</p>\n'
                f"{''.join(capability_parts)}\n"
                "</section>"
            )
        if view.roadmap_report is not None:
            parts.append(
                _section(
                    "Phased Modernization Plan",
                    _render_phased_roadmap(view),
                    section_id="phased-modernization-plan",
                    note=(
                        "Same Priority Actions, sequenced Stabilize → Secure → "
                        "Modernize → Optimize."
                    ),
                )
            )
        if view.ai_enrichment is not None:
            parts.append(
                _section(
                    "Modernization Advisor",
                    _render_ai(view.ai_enrichment),
                    section_id="modernization-advisor",
                    note=(
                        "AI-generated interpretation. Not merged into findings or recommendations."
                    ),
                    css_class="section section-ai",
                )
            )
        parts.append(
            _section(
                "Technical Appendix",
                _render_technical_details(view),
                section_id="technical-appendix",
                note="Engineering reference: evidence, graphs, artifacts, and metadata.",
            )
        )
        parts.extend(
            [
                _render_footer(view),
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


def _subsection(
    title: str,
    body: str,
    *,
    section_id: str,
    note: str | None = None,
) -> str:
    note_html = f'<p class="section-note">{escape_html(note)}</p>' if note else ""
    return (
        f'<section class="subsection" id="{escape_html(section_id)}">\n'
        f'<div class="section-head"><h3>{escape_html(title)}</h3></div>\n'
        f"{note_html}"
        f"{body}\n"
        "</section>"
    )


def _render_toc(view: HtmlReportViewModel) -> str:
    if not view.outline:
        return ""
    items = "".join(
        f'<li><a href="#{escape_html(entry.section_id)}">{escape_html(entry.title)}</a></li>\n'
        for entry in view.outline
    )
    return (
        '<nav class="toc" id="contents" aria-label="Table of contents">\n'
        '<div class="section-head"><h2>Contents</h2></div>\n'
        f"<ol>\n{items}</ol>\n"
        "</nav>"
    )


def _render_leadership_verdict(view: HtmlReportViewModel) -> str:
    text = (view.leadership_verdict or "").strip()
    if not text:
        return ""
    return (
        '<section class="section section-verdict" id="leadership-verdict">\n'
        '<div class="section-head"><h2>Leadership Verdict</h2></div>\n'
        f'<p class="verdict-body">{escape_html(text)}</p>\n'
        "</section>"
    )


def _render_executive_summary(view: HtmlReportViewModel) -> str:
    narrative = view.executive_summary
    if narrative is None:
        return (
            '<p class="muted">No executive summary was produced for this assessment.</p>\n'
            f"{_render_technology(view)}"
        )
    return (
        '<div class="exec-narrative">\n'
        "<h3>Should I care?</h3>\n"
        f"<p>{escape_html(narrative.should_i_care)}</p>\n"
        "<h3>Why now?</h3>\n"
        f"<p>{escape_html(narrative.why_now)}</p>\n"
        "<h3>What should my team do next?</h3>\n"
        f"<p>{escape_html(narrative.what_next)}</p>\n"
        "</div>\n"
        "<h3>Technology Overview</h3>\n"
        f"{_render_technology(view)}"
    )


def _render_key_takeaways(view: HtmlReportViewModel) -> str:
    if not view.key_takeaways:
        return '<p class="muted">No key takeaways were available for this assessment.</p>'
    items = "".join(f"<li>{escape_html(item)}</li>\n" for item in view.key_takeaways)
    return f'<ul class="takeaways">\n{items}</ul>'


def _render_engineering_risks(view: HtmlReportViewModel) -> str:
    if not view.engineering_risks:
        return (
            '<p class="muted">No significant engineering risks were identified '
            "under the activated assessment checks.</p>"
        )
    blocks: list[str] = []
    for theme in view.engineering_risks:
        items = "".join(f"<li>{escape_html(item)}</li>" for item in theme.items)
        blocks.append(
            f'<div class="risk-theme"><h3>{escape_html(theme.theme)}</h3>'
            f'<ul class="plain">{items}</ul></div>'
        )
    return "\n".join(blocks)


def _render_modernization_opportunities(view: HtmlReportViewModel) -> str:
    if not view.modernization_opportunities:
        return (
            '<p class="muted">No additional modernization opportunities were '
            "identified beyond Priority Actions and capability assessments.</p>"
        )
    items = "".join(
        f"<li>{escape_html(item)}</li>" for item in view.modernization_opportunities
    )
    return f'<ul class="plain">{items}</ul>'


def _render_assessment_scope(view: HtmlReportViewModel) -> str:
    scope = view.assessment_scope
    if scope is None:
        return '<p class="muted">Assessment scope was not recorded for this run.</p>'
    assessed = (
        "".join(f"<li>{escape_html(label)}</li>" for label in scope.assessed_packs)
        or "<li>None</li>"
    )
    skipped_rows = "".join(
        "<tr>"
        f"<td>{escape_html(label)}</td>"
        f"<td>{escape_html(reason)}</td>"
        "</tr>"
        for label, reason in scope.not_assessed_packs
    ) or '<tr><td colspan="2">None</td></tr>'
    return (
        "<p>Packs included in this assessment and packs intentionally not assessed.</p>\n"
        '<div class="split">\n'
        "<div>\n<h3>Assessed</h3>\n"
        f'<ul class="plain">{assessed}</ul>\n'
        "</div>\n"
        "<div>\n<h3>Not assessed</h3>\n"
        '<div class="table-wrap"><table>\n'
        "<thead><tr><th>Area</th><th>Reason</th></tr></thead>\n"
        f"<tbody>{skipped_rows}</tbody>\n</table></div>\n"
        "</div>\n"
        "</div>"
    )


def _render_engineering_modernization_assessment(view: HtmlReportViewModel) -> str:
    summary_text = escape_html(view.assessment_summary.summary_text)
    return (
        f'<p class="ema-lede">{summary_text}</p>\n'
        f"{_render_executive_cards(view)}\n"
        "<h3>Technology Overview</h3>\n"
        f"{_render_technology(view)}"
    )


def _render_hero(view: HtmlReportViewModel) -> str:
    summary = view.summary
    meta = view.metadata
    severity_tone = _severity_tone(summary.highest_finding_severity)
    generated = _humanize_timestamp(meta.generated_at_utc)
    meta_items = [
        ("Repository", meta.repository_name or summary.repository_name),
        ("Generated", generated),
        ("Report version", meta.report_version),
    ]
    meta_html = "".join(
        '<div class="meta-item"><span class="meta-label">'
        f"{escape_html(label)}</span>"
        f'<span class="meta-value">{escape_and_wrap(value)}</span></div>\n'
        for label, value in meta_items
        if value and str(value).strip() not in {"—", "-", "Unknown"}
    )
    return (
        '<header class="hero" id="cover">\n'
        '<div class="hero-brand">\n'
        f'<img class="brand-logo" src="{logo_data_uri()}" '
        f'alt="{escape_html(BRAND_NAME)}" width="140" height="40">\n'
        f'<p class="brand-name">{escape_html(BRAND_NAME)}</p>\n'
        f'<h1 class="report-title">{escape_html(BRAND_REPORT_NAME)}</h1>\n'
        "</div>\n"
        f'<div class="hero-meta report-identity">\n{meta_html}</div>\n'
        '<div class="hero-kpis">\n'
        f"{_kpi('Highest Finding Severity', summary.highest_finding_severity, '', severity_tone)}"
        f"{_kpi('Cloud Enablement Signals', _cloud_primary(view), _cloud_status(view), 'cloud')}"
        f"{_kpi('CI/CD', _cicd_value(view), '', 'cicd')}"
        "</div>\n"
        "</header>"
    )


def _humanize_timestamp(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return "—"
    # Prefer date + time without fractional seconds / Z clutter.
    if "T" in text:
        date_part, _, time_part = text.partition("T")
        time_part = time_part.rstrip("Z")
        if "." in time_part:
            time_part = time_part.split(".", 1)[0]
        if len(time_part) >= 5:
            return f"{date_part} {time_part[:5]} UTC"
        return date_part
    return text


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
    tests = metrics.test_files_label if metrics else ""
    cicd = metrics.cicd_label if metrics else ""
    cloud_primary = metrics.cloud_signals_primary if metrics else ""
    cloud_status = (
        metrics.cloud_signals_status
        if metrics and metrics.cloud_signals_primary not in {"", "Unknown"}
        else ""
    )
    size = metrics.repository_size_label if metrics else f"{file_count} files"
    highest = view.summary.highest_finding_severity
    cards = [
        _stat_card("Files", str(file_count)),
        _stat_card("Technologies", str(tech_count)),
        _stat_card("Findings", str(findings)),
        _stat_card("Recommendations", str(recommendations)),
    ]
    if tests and tests != "Unknown":
        cards.append(_stat_card("Test Files Detected", tests))
    if cicd and cicd != "Unknown":
        cards.append(_stat_card("CI/CD", cicd))
    if cloud_primary and cloud_primary != "Unknown":
        cards.append(_stat_card("Cloud Enablement Signals", cloud_primary, cloud_status))
    if size and size != "Unknown":
        cards.append(_stat_card("Repository Size", size))
    if highest and highest != "Unknown":
        cards.append(_stat_card("Highest Finding Severity", highest))
    return '<div class="stat-grid">\n' + "".join(cards) + "</div>"


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
            '<p class="muted">No findings were produced for this run. '
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


def _roadmap_bucket(item: RecommendationView) -> str:
    from codestrata.reporting.prioritization import BUCKET_LABELS

    bucket = (item.presentation_bucket or "").strip().lower()
    if bucket in BUCKET_LABELS:
        return BUCKET_LABELS[bucket]
    # Fallback for older views without presentation_bucket.
    key = item.priority.lower()
    if key in {"immediate", "critical"}:
        return "Immediate"
    if key in {"high", "medium"}:
        return "Near Term"
    return "Future"


def _render_roadmap(items: tuple[RecommendationView, ...]) -> str:
    # Leadership display requires finding-backed actions only.
    display = tuple(item for item in items if item.related_finding_ids)
    if not display:
        return (
            '<p class="muted">No Priority Actions were produced for this assessment. '
            "Findings may still appear above when present.</p>"
        )
    buckets: dict[str, list[RecommendationView]] = {
        "Immediate": [],
        "Near Term": [],
        "Future": [],
    }
    for item in display:
        buckets[_roadmap_bucket(item)].append(item)
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


def _business_value(item: RecommendationView) -> str:
    risk = (item.risk or "").lower()
    if risk == "high" or item.priority.lower() in {"immediate", "critical", "high"}:
        return "High"
    if risk == "medium" or item.priority.lower() == "medium":
        return "Medium"
    return "Incremental"


def _effort_label(item: RecommendationView) -> str:
    effort = (item.effort or "").lower()
    labels = {
        "small": "Small",
        "xs": "Small",
        "s": "Small",
        "medium": "Medium",
        "m": "Medium",
        "large": "Larger",
        "l": "Larger",
        "extra_large": "Larger",
        "xl": "Larger",
    }
    if effort in labels:
        return labels[effort]
    actions = len(item.actions)
    if actions <= 1:
        return "Small"
    if actions <= 3:
        return "Medium"
    return "Larger"


def _render_recommendation_card(item: RecommendationView, *, compact: bool) -> str:
    related = _finding_id_links(item.related_finding_ids) or '<span class="muted">None</span>'
    nodes = _id_list(item.affected_nodes) or '<span class="muted">None</span>'
    related_titles = ""
    if item.related_finding_titles:
        related_titles = (
            '<p class="related-findings"><em>Related findings</em> '
            + escape_html("; ".join(item.related_finding_titles[:3]))
            + (
                f" (+{len(item.related_finding_titles) - 3} more)"
                if len(item.related_finding_titles) > 3
                else ""
            )
            + "</p>\n"
        )
    chips = (
        '<div class="chip-row">\n'
        f'<span class="chip"><em>Horizon</em> {escape_html(_roadmap_bucket(item))}</span>\n'
        f'<span class="chip"><em>Business impact</em> '
        f"{escape_html(_business_value(item))}</span>\n"
        f'<span class="chip"><em>Effort</em> {escape_html(_effort_label(item))}</span>\n'
        "</div>\n"
        f'<p class="outcome"><em>Business outcome</em> {escape_html(item.summary)}</p>\n'
        f"{related_titles}"
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
        f'<span class="badge priority-{escape_html(item.presentation_bucket or item.priority)}">'
        f"{escape_html(_roadmap_bucket(item))}</span> "
        f"<strong>{escape_html(item.title)}</strong>"
        f"</header>\n"
        f"{chips}"
        f"{detail}"
        "</article>"
    )


def _is_blank_or_unknown(value: object) -> bool:
    text = str(value or "").strip().lower()
    return text in {"", "unavailable", "unknown", "not_assessed", "—", "-"}


def _limitation_items(limitations: object) -> str:
    """Render limitation rows; omit diagnostic unavailable/unknown category noise."""

    rows: tuple[object, ...]
    if limitations is None:
        rows = ()
    elif isinstance(limitations, tuple):
        rows = limitations
    else:
        rows = tuple(limitations)  # type: ignore[arg-type]
    items = []
    for item in rows:
        category = str(getattr(item, "category", "") or "")
        summary = str(getattr(item, "summary", "") or "")
        cat_l = category.lower()
        if "unavailable" in cat_l or cat_l in {"unknown", "not_assessed"}:
            continue
        if _is_blank_or_unknown(summary):
            continue
        summary_l = summary.lower()
        if "business impact remains unknown" in summary_l or "business impact unknown" in cat_l:
            continue
        if "phase " in summary_l and ("collector" in summary_l or "unsupported" in summary_l):
            continue
        if "deterministic" in summary_l or "phase 4" in summary_l or "phase 5" in summary_l:
            continue
        if "inventory does not re-run rules" in summary_l:
            continue
        label = category.replace("-", " ").replace("_", " ").strip().title() or "Note"
        items.append(
            f"<li><strong>{escape_html(label)}</strong> — {escape_html(summary)}</li>"
        )
    return "".join(items)


def _architecture_conclusion_meta(item: object) -> str:
    bits: list[str] = []
    confidence = getattr(item, "confidence", None)
    business_impact = getattr(item, "business_impact", None)
    if not _is_blank_or_unknown(confidence):
        bits.append(f"Confidence: {confidence}")
    if not _is_blank_or_unknown(business_impact) and str(business_impact).lower() not in {
        "unknown",
        "not assessed",
        "not_assessed",
    }:
        bits.append(f"Business impact: {business_impact}")
    return escape_html(" · ".join(bits)) if bits else ""


def _architecture_conclusion_card(item: object) -> str:
    meta = _architecture_conclusion_meta(item)
    meta_html = f"<p class='muted'>{meta}</p>" if meta else ""
    scope_values = tuple(getattr(item, "affected_scope", ()) or ())
    # Prefer package/module roots over exhaustive file lists for leadership readability.
    scope = ", ".join(scope_values[:4]) or "—"
    if len(scope_values) > 4:
        scope = f"{scope} (+{len(scope_values) - 4} more)"
    return (
        "<article class='card'>"
        f"<h4>{escape_html(getattr(item, 'title', ''))}</h4>"
        f"<p>{escape_html(getattr(item, 'summary', ''))}</p>"
        f"{meta_html}"
        f"<p class='muted'>{escape_html(getattr(item, 'severity_summary', ''))}</p>"
        f"<p class='muted'>Scope: {escape_html(scope)}</p>"
        "</article>"
    )


def _dedupe_architecture_conclusions(items: tuple[object, ...]) -> tuple[object, ...]:
    seen: set[str] = set()
    out: list[object] = []
    for item in items:
        title = str(getattr(item, "title", "") or "").strip().lower()
        if not title or title in seen:
            continue
        seen.add(title)
        out.append(item)
    return tuple(out)


def _render_architecture(section: ArchitectureReportSection) -> str:
    metrics = "".join(
        "<div class='card'>"
        f"<div class='label'>{escape_html(item.label)}</div>"
        f"<div class='value'>{escape_html(item.value)}</div>"
        f"{f'<p class="muted">{escape_html(item.note)}</p>' if item.note else ''}"
        "</div>"
        for item in section.key_metrics
        if str(item.value).strip().lower() not in {"unavailable", "unknown", "—", "-"}
        and "coverage" not in item.label.lower()
    )
    conclusions = _dedupe_architecture_conclusions(tuple(section.conclusions))
    conclusions_body = "".join(_architecture_conclusion_card(item) for item in conclusions)
    recommendations_body = "".join(
        "<article class='card'>"
        f"<h4>{escape_html(item.title)}</h4>"
        f"<p><strong>Objective:</strong> {escape_html(item.objective)}</p>"
        f"<p>{escape_html(item.rationale)}</p>"
        "</article>"
        for item in section.recommendation_groups
    )
    # Collapse supporting findings by title for customer readability.
    finding_rows: list[str] = []
    seen_findings: set[str] = set()
    for item in section.findings:
        key = item.title.strip().lower()
        if key in seen_findings:
            continue
        seen_findings.add(key)
        finding_rows.append(
            "<tr>"
            f"<td>{escape_html(item.title)}</td>"
            f"<td>{escape_html(item.severity)}</td>"
            f"<td>{escape_html(', '.join(item.affected_scope[:3]) or '—')}</td>"
            "</tr>"
        )
    findings = "".join(finding_rows)
    limitations = _limitation_items(
        tuple(
            item
            for item in section.limitations
            if "business impact unknown" not in str(getattr(item, "summary", item)).lower()
            and "phase " not in str(getattr(item, "summary", item)).lower()
        )
    )
    has_substance = bool(conclusions_body or recommendations_body or findings or limitations)
    if not has_substance and not metrics:
        return (
            f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
            f"{escape_html(section.status_summary)}</p>"
            "<p class='muted'>Architecture was assessed; no significant architecture "
            "risks were identified for this repository.</p>"
        )
    parts = [
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>",
        f"<p>{escape_html(section.executive_summary)}</p>",
    ]
    if metrics:
        parts.append(f"<div class='grid'>{metrics}</div>")
    if conclusions_body:
        parts.extend(["<h3>Architecture conclusions</h3>", conclusions_body])
    if recommendations_body:
        parts.extend(["<h3>Recommended actions</h3>", recommendations_body])
    if findings:
        parts.extend(
            [
                "<h3>Supporting findings</h3>",
                "<table><thead><tr>"
                "<th>Finding</th><th>Severity</th>"
                "<th>Scope</th>"
                "</tr></thead><tbody>"
                f"{findings}</tbody></table>",
            ]
        )
    if limitations:
        parts.extend(["<h3>Limitations</h3>", f"<ul>{limitations}</ul>"])
    return "\n".join(parts)


def _render_technical_debt(section: TechnicalDebtReportSection) -> str:
    metrics = "".join(
        "<div class='card'>"
        f"<div class='label'>{escape_html(item.label)}</div>"
        f"<div class='value'>{escape_html(item.value)}</div>"
        f"{f'<p class="muted">{escape_html(item.note)}</p>' if item.note else ''}"
        "</div>"
        for item in section.key_metrics
        if str(item.value).strip().lower() not in {"unavailable", "unknown", "—", "-"}
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
    conclusions = "".join(
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
    recommendations = "".join(
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
    test_obs = section.test_observation
    test_block = (
        "<div class='card td-test-observation'>"
        f"<h4>{escape_html(test_obs.title)}</h4>"
        f"<p>{escape_html(test_obs.summary)}</p>"
        f"<p class='muted'>Test findings: {test_obs.finding_count}</p>"
        "</div>"
        if test_obs.present
        else ""
    )
    coverage = "".join(
        "<tr>"
        f"<td>{escape_html(item.label)}</td>"
        f"<td>{escape_html(item.status)}</td>"
        f"<td>{escape_html(item.display)}</td>"
        "</tr>"
        for item in section.coverage_summary
        if str(item.status).strip().lower() not in {"unavailable", "unknown"}
        and str(item.display).strip().lower() not in {"unavailable", "unknown"}
    )
    limitations = _limitation_items(section.limitations)
    has_substance = bool(
        themes
        or hotspots
        or conclusions
        or recommendations
        or test_block
        or coverage
        or limitations
    )
    if not has_substance and not metrics:
        return (
            f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
            f"{escape_html(section.status_summary)}</p>"
            "<p class='muted'>Technical debt was assessed; no significant "
            "production-facing debt signals were identified.</p>"
        )
    parts = [
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>",
        f"<p>{escape_html(section.executive_summary)}</p>",
    ]
    if metrics:
        parts.append(f"<div class='grid'>{metrics}</div>")
    if themes:
        parts.extend(
            [
                "<h3>Significant production themes</h3>",
                "<table><thead><tr>"
                "<th>Theme</th><th>Rule</th><th>Findings</th>"
                "<th>High</th><th>Medium</th>"
                "</tr></thead><tbody>"
                f"{themes}</tbody></table>",
            ]
        )
    if hotspots:
        parts.extend(
            [
                "<h3>Top production hotspots</h3>",
                "<table><thead><tr>"
                "<th>#</th><th>Path</th><th>Unit</th><th>Highest severity</th>"
                "<th>Findings</th><th>Rules</th><th>Metrics</th>"
                "</tr></thead><tbody>"
                f"{hotspots}</tbody></table>",
            ]
        )
    if conclusions:
        parts.extend(["<h3>Conclusions</h3>", conclusions])
    if recommendations:
        parts.extend(["<h3>Recommendations</h3>", recommendations])
    if test_block:
        parts.extend(["<h3>Test-maintainability observation</h3>", test_block])
        parts.append(
            "<p class='muted'>Test findings are not production health signals.</p>"
        )
    if coverage:
        parts.extend(
            [
                "<h3>Coverage</h3>",
                "<table><thead><tr><th>Area</th><th>Status</th><th>Detail</th></tr></thead>"
                f"<tbody>{coverage}</tbody></table>",
            ]
        )
    if limitations:
        parts.extend(["<h3>Limitations</h3>", f"<ul>{limitations}</ul>"])
    return "\n".join(parts)


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
    limitations = _limitation_items(section.limitations)
    limitations_block = f"<ul>{limitations}</ul>" if limitations else ""
    trace = ""
    parts = [
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>",
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
    diagnostics_block = ""
    limitations = _limitation_items(section.limitations)
    limitations_block = f"<ul>{limitations}</ul>" if limitations else ""
    trace = ""
    parts = [
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>",
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
    diagnostics_block = ""
    limitations = _limitation_items(section.limitations)
    limitations_block = f"<ul>{limitations}</ul>" if limitations else ""
    trace = ""
    parts = [
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>",
        "<h3>Overall Test Posture</h3>",
        f"<p>{escape_html(section.overall_posture_summary or section.executive_summary)}</p>",
        "<h3>Executive Summary</h3>",
        f"<p>{escape_html(section.executive_summary)}</p>",
        "<h3>Assessment and Coverage Status</h3>",
        f"<p><strong>Assessment status:</strong> {escape_html(section.assessment_status)}</p>",
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
    diagnostics_block = ""
    limitations = _limitation_items(section.limitations)
    limitations_block = f"<ul>{limitations}</ul>" if limitations else ""
    trace = ""
    parts = [
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>",
        "<h3>Overall Cloud Posture</h3>",
        f"<p>{escape_html(section.overall_posture_summary or section.executive_summary)}</p>",
        "<h3>Executive Summary</h3>",
        f"<p>{escape_html(section.executive_summary)}</p>",
        "<h3>Assessment and Coverage Status</h3>",
        f"<p><strong>Assessment status:</strong> {escape_html(section.assessment_status)}</p>",
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
    diagnostics_block = ""
    limitations = _limitation_items(section.limitations)
    limitations_block = f"<ul>{limitations}</ul>" if limitations else ""
    trace = ""
    parts = [
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>",
        "<h3>Overall AI Readiness Posture</h3>",
        f"<p>{escape_html(section.overall_posture_summary or section.executive_summary)}</p>",
        "<h3>Executive Summary</h3>",
        f"<p>{escape_html(section.executive_summary)}</p>",
        "<h3>Assessment and Coverage Status</h3>",
        f"<p><strong>Assessment status:</strong> {escape_html(section.assessment_status)}</p>",
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


def _render_phased_roadmap(view: HtmlReportViewModel) -> str:
    section = view.roadmap_report
    if section is None:
        return '<p class="muted">No phased modernization plan was produced.</p>'

    finding_titles = {item.finding_id: item.title for item in view.findings}
    action_pool = view.priority_actions or view.recommendations
    recommendation_titles = {
        item.recommendation_id: item.title for item in action_pool
    }

    phase_blocks: list[str] = []
    for phase in section.phases:
        initiatives = tuple(
            item for item in phase.initiatives if item.supporting_recommendation_ids
        )
        if not initiatives:
            continue
        cards = "".join(
            _roadmap_initiative_card(
                item,
                finding_titles=finding_titles,
                recommendation_titles=recommendation_titles,
            )
            for item in initiatives
        )
        phase_blocks.append(
            "<div class='roadmap-lane'>"
            f"<h3>{escape_html(phase.title)} "
            f"<span class='count-pill'>{len(initiatives)}</span></h3>"
            f"<p class='muted'>{escape_html(phase.objective)}</p>"
            f"<div class='card-stack'>{cards}</div>"
            "</div>"
        )
    body = (
        "".join(phase_blocks)
        if phase_blocks
        else "<p class='muted'>No phased modernization initiatives were derived.</p>"
    )
    return "\n".join(
        [
            f"<p>{escape_html(section.summary)}</p>",
            f"<div class='roadmap'>{body}</div>",
        ]
    )


def _roadmap_initiative_card(
    item: object,
    *,
    finding_titles: dict[str, str],
    recommendation_titles: dict[str, str],
) -> str:
    """Compact leadership card: short title, outcome, related titles (no raw IDs)."""

    title = str(getattr(item, "summary", "") or "").strip()
    rec_ids = tuple(getattr(item, "supporting_recommendation_ids", ()) or ())
    if rec_ids and rec_ids[0] in recommendation_titles:
        title = recommendation_titles[rec_ids[0]]
    elif not title:
        raw = str(getattr(item, "title", "")).strip()
        title = raw.split(" — ", 1)[-1].strip() if " — " in raw else raw
    if not title:
        title = "Modernization initiative"

    outcome = str(getattr(item, "expected_outcome", "") or "").strip()
    related_recs = [
        recommendation_titles[rid] for rid in rec_ids if rid in recommendation_titles
    ]
    related_findings = [
        finding_titles[fid]
        for fid in tuple(getattr(item, "supporting_finding_ids", ()) or ())
        if fid in finding_titles
    ]
    related_bits: list[str] = []
    if related_recs:
        related_bits.append(
            "Actions: "
            + "; ".join(related_recs[:3])
            + (f" (+{len(related_recs) - 3} more)" if len(related_recs) > 3 else "")
        )
    if related_findings:
        related_bits.append(
            "Findings: "
            + "; ".join(related_findings[:3])
            + (
                f" (+{len(related_findings) - 3} more)"
                if len(related_findings) > 3
                else ""
            )
        )
    related_html = (
        f"<p class='muted'>{escape_html(' · '.join(related_bits))}</p>"
        if related_bits
        else ""
    )
    return (
        "<article class='card'>"
        f"<h4>{escape_html(title)}</h4>"
        f"<p><strong>Business outcome:</strong> {escape_html(outcome)}</p>"
        f"{related_html}"
        "</article>"
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
    diagnostics_block = ""
    limitations = _limitation_items(section.limitations)
    limitations_block = f"<ul>{limitations}</ul>" if limitations else ""
    trace = ""
    parts = [
        f"<p><strong>Status:</strong> {escape_html(section.status_label)} — "
        f"{escape_html(section.status_summary)}</p>",
        "<h3>Overall Performance Posture</h3>",
        f"<p>{escape_html(section.overall_posture_summary or section.executive_summary)}</p>",
        "<h3>Executive Summary</h3>",
        f"<p>{escape_html(section.executive_summary)}</p>",
        "<h3>Assessment and Coverage Status</h3>",
        f"<p><strong>Assessment status:</strong> {escape_html(section.assessment_status)}</p>",
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
        "<h4>Advisor metadata</h4>\n"
        '<dl class="meta">\n'
        f"<div><dt>Provider</dt><dd>{escape_html(ai.provider)}</dd></div>\n"
        f"<div><dt>Model</dt><dd>{escape_html(ai.model_id)}</dd></div>\n"
        f"<div><dt>Advisor version</dt><dd>"
        f"{escape_html(ai.advisor_version or '—')}</dd></div>\n"
        f"<div><dt>Prompt version</dt><dd>"
        f"{escape_html(ai.prompt_version or '—')}</dd></div>\n"
        f"<div><dt>Generated</dt><dd>"
        f"{escape_html(ai.generated_at_utc or '—')}</dd></div>\n"
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
            '<p class="muted">No findings were produced for this run. '
            "This does not certify that the repository is free of issues.</p>"
        )
    )
    recommendations_body = (
        "\n".join(_render_recommendation_card(item, compact=False) for item in view.recommendations)
        if view.recommendations
        else ('<p class="muted">No Priority Actions were produced for this run.</p>')
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
        '<details class="tech-block" id="assessment-scope">\n'
        "<summary>Assessment Scope</summary>\n"
        f"{_render_assessment_scope(view)}\n"
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
        f"<p><strong>Hygiene and quality checks assessed:</strong> {summary.rules_evaluated}</p>\n"
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
        ("Engine version", escape_html(meta.engine_version)),
        ("Advisor version", escape_html(meta.advisor_version or "—")),
        ("Repository", escape_html(meta.repository_name or view.summary.repository_name)),
        ("Assessment mode", escape_html(view.summary.assessment_mode_label)),
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


def _render_footer(view: HtmlReportViewModel | None = None) -> str:
    engine = view.metadata.engine_version if view is not None else BRAND_VERSION
    report_version = view.metadata.report_version if view is not None else "3.0"
    return (
        '<footer class="site-footer">\n'
        f"<p>{escape_html(BRAND_FOOTER_LINE)}</p>\n"
        f"<p>Report {escape_html(report_version)} · Engine {escape_html(engine)}</p>\n"
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
.toc {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 1.1rem 1.35rem 1.2rem;
  margin-bottom: 1.25rem;
}
.toc ol {
  margin: 0.35rem 0 0;
  padding-left: 1.25rem;
  columns: 2;
  column-gap: 2rem;
}
.toc li { break-inside: avoid; margin: 0.25rem 0; }
.toc a {
  color: var(--ink);
  text-decoration: none;
  border-bottom: 1px solid transparent;
}
.toc a:hover { border-bottom-color: var(--accent); color: var(--accent); }
.takeaways {
  margin: 0.35rem 0 0;
  padding-left: 1.2rem;
}
.takeaways li {
  margin: 0.45rem 0;
  line-height: 1.5;
  max-width: 62rem;
}
.section-verdict {
  margin: 1.25rem 0 0;
}
.verdict-body {
  margin: 0.35rem 0 0;
  font-size: 1.12rem;
  line-height: 1.6;
  max-width: 46rem;
  color: var(--ink);
}
.exec-narrative h3 {
  margin: 1rem 0 0.35rem;
  font-size: 1rem;
}
.exec-narrative p {
  margin: 0;
  max-width: 46rem;
  line-height: 1.55;
}
.ema-lede {
  margin: 0 0 1rem;
  font-size: 1.05rem;
  line-height: 1.55;
  max-width: 46rem;
  color: var(--ink);
}
.subsection {
  margin: 1.1rem 0 0;
  padding: 1rem 0 0;
  border-top: 1px solid var(--border);
}
.subsection:first-of-type { border-top: 0; padding-top: 0; }
.section-capability > .section-head h2 { margin-bottom: 0.25rem; }
.report-identity { margin-bottom: 1rem; }
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
  @page { margin: 1.4cm; }
  body { background: #fff; color: #000; }
  .page { max-width: none; padding: 0; }
  .toc { box-shadow: none; columns: 1; break-after: page; }
  .toc a { text-decoration: none; color: #000; }
  .hero { box-shadow: none; break-after: page; }
  .section, .subsection, .item-card, .stat-card, .kpi {
    break-inside: avoid;
    box-shadow: none;
  }
  .hero-kpis { break-inside: avoid; }
  .site-footer { border-top: 1px solid #ccc; }
}
"""
