"""Thin presentation check modules (shell through statuses)."""

from __future__ import annotations

from verification.assessment_report_redesign.models import CheckResult


def check_shell(html: str) -> list[CheckResult]:
    return [
        CheckResult(
            "shell:product_bar",
            "report-product-bar" in html and "report-product-name" in html,
            "bar",
            "report_shell",
        ),
        CheckResult(
            "shell:cover",
            'id="cover"' in html and "report-title" in html,
            "cover",
            "report_shell",
        ),
        CheckResult(
            "shell:footer",
            "site-footer" in html,
            "footer",
            "report_shell",
        ),
    ]


def check_executive_summary(html: str) -> list[CheckResult]:
    return [
        CheckResult(
            "exec:section",
            'id="executive-summary"' in html,
            "present",
            "executive_summary",
        ),
        CheckResult(
            "exec:leadership_verdict",
            'id="leadership-verdict"' in html,
            "verdict",
            "executive_summary",
        ),
        CheckResult(
            "exec:no_ai_narrative_injection",
            "<!-- AI-generated narrative -->" not in html,
            "no_synth",
            "executive_summary",
        ),
    ]


def check_assessment_heads(html: str) -> list[CheckResult]:
    return [
        CheckResult(
            "heads:results",
            'id="assessment-results"' in html or "assessment-head" in html,
            "heads",
            "assessment_head",
        ),
        CheckResult(
            "heads:eis_section",
            'id="engineering-intelligence-summary"' in html,
            "eis",
            "assessment_head",
        ),
    ]


def check_findings(html: str) -> list[CheckResult]:
    return [
        CheckResult(
            "findings:card_class",
            "item-card finding" in html or 'class="item-card finding"' in html,
            "cards",
            "finding",
        ),
        CheckResult(
            "findings:severity_not_color_only",
            "aria-label=\"Severity:" in html or "badge severity-" in html,
            "label",
            "finding",
        ),
        CheckResult(
            "findings:shape_marker",
            "severity-critical::before" in html or ".badge.severity-critical::before" in html,
            "shape",
            "risk",
        ),
    ]


def check_evidence(html: str) -> list[CheckResult]:
    return [
        CheckResult(
            "evidence:mono_role",
            "--cs-font-mono" in html and ("evidence" in html.lower()),
            "mono",
            "evidence",
        ),
        CheckResult(
            "evidence:overflow_safe",
            "overflow-x: auto" in html or "overflow-wrap: anywhere" in html,
            "overflow",
            "evidence",
        ),
    ]


def check_recommendations(html: str) -> list[CheckResult]:
    return [
        CheckResult(
            "recs:present",
            "recommendation" in html.lower() or "priority-actions" in html,
            "present",
            "recommendation",
        ),
        CheckResult(
            "recs:card_style",
            "recommendation-card" in html or "item-card recommendation" in html,
            "cards",
            "recommendation",
        ),
    ]


def check_scores(html: str) -> list[CheckResult]:
    return [
        CheckResult(
            "scores:kpi_or_metric",
            "kpi-value" in html or "metric-card" in html or "stat-value" in html,
            "metrics",
            "score",
        ),
        CheckResult(
            "scores:semantic_tokens",
            "--cs-score-excellent" in html or "--cs-teal" in html,
            "tokens",
            "score",
        ),
    ]


def check_statuses(html: str) -> list[CheckResult]:
    return [
        CheckResult(
            "status:risk_tokens",
            "--cs-risk-critical" in html and "--cs-risk-low" in html,
            "risk_tokens",
            "risk",
        ),
        CheckResult(
            "status:badge",
            "status-badge" in html or "badge severity-" in html,
            "badge",
            "risk",
        ),
    ]


def check_navigation(html: str) -> list[CheckResult]:
    return [
        CheckResult(
            "nav:toc",
            'id="contents"' in html and 'class="toc"' in html,
            "toc",
            "navigation",
        ),
        CheckResult(
            "nav:sticky_or_responsive",
            "position: sticky" in html or "@media (max-width:" in html,
            "sticky",
            "navigation",
        ),
        CheckResult(
            "nav:aria_label",
            'aria-label="Table of contents"' in html,
            "aria",
            "navigation",
        ),
    ]


def check_responsive(html: str) -> list[CheckResult]:
    return [
        CheckResult(
            "responsive:breakpoints",
            "@media (max-width: 560px)" in html and "@media (max-width: 820px)" in html,
            "bp",
            "responsive",
        ),
        CheckResult(
            "responsive:table_wrap",
            "table-wrap" in html or "responsive-table" in html,
            "tables",
            "responsive",
        ),
        CheckResult(
            "responsive:viewport_meta",
            "width=device-width" in html,
            "viewport",
            "responsive",
        ),
    ]


def check_print(html: str) -> list[CheckResult]:
    return [
        CheckResult(
            "print:media",
            "@media print" in html,
            "present",
            "print",
        ),
        CheckResult(
            "print:light_bg",
            "background: #fff" in html or "background: #ffffff" in html.lower(),
            "light",
            "print",
        ),
        CheckResult(
            "print:hide_chrome",
            "report-product-bar" in html and "display: none" in html,
            "chrome",
            "print",
        ),
        CheckResult(
            "print:break_inside",
            "break-inside: avoid" in html,
            "breaks",
            "print",
        ),
    ]


def check_accessibility(html: str) -> list[CheckResult]:
    return [
        CheckResult(
            "a11y:lang",
            'lang="en"' in html,
            "lang",
            "accessibility",
        ),
        CheckResult(
            "a11y:skip_link",
            "skip-link" in html,
            "skip",
            "accessibility",
        ),
        CheckResult(
            "a11y:banner",
            'role="banner"' in html,
            "banner",
            "accessibility",
        ),
        CheckResult(
            "a11y:focus_visible",
            ":focus-visible" in html,
            "focus",
            "accessibility",
        ),
    ]


def check_offline(html: str) -> list[CheckResult]:
    lowered = html.lower()
    return [
        CheckResult(
            "offline:no_http_assets",
            "https://" not in lowered.split("<body", 1)[0]
            or "content-security-policy" in lowered,
            # CSP + no link/script is the real gate; title may mention https docs.
            "csp_gate",
            "offline",
        ),
        CheckResult(
            "offline:no_google_fonts",
            "fonts.googleapis" not in lowered and "fonts.gstatic" not in lowered,
            "fonts",
            "offline",
        ),
        CheckResult(
            "offline:no_cdn_js",
            "cdn.jsdelivr" not in lowered and "unpkg.com" not in lowered,
            "cdn",
            "offline",
        ),
        CheckResult(
            "offline:no_analytics",
            "gtag(" not in lowered and "googletagmanager" not in lowered,
            "analytics",
            "offline",
        ),
    ]
