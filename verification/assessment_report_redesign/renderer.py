"""Renderer / HTML generation checks (synthetic fixture)."""

from __future__ import annotations

import re
from pathlib import Path

from verification.assessment_report_redesign.contract import STABLE_SECTION_IDS
from verification.assessment_report_redesign.models import CheckResult, Defect


def _render_sample(tmp_path: Path) -> str:
    from codestrata.reporting.html_v2 import HtmlReportRenderer, build_html_report_view_model
    from verification.assessment_report_redesign.fixtures import synthetic_report_input

    return HtmlReportRenderer().render(
        build_html_report_view_model(synthetic_report_input(tmp_path))
    )


def check_renderer(monorepo: Path, tmp_path: Path) -> tuple[list[CheckResult], list[Defect], str]:
    del monorepo  # generation uses installed package path
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    html = _render_sample(tmp_path)

    checks.append(
        CheckResult(
            "renderer:doctype",
            html.lstrip().lower().startswith("<!doctype html>"),
            "doctype",
            "renderer",
        )
    )
    checks.append(
        CheckResult(
            "renderer:embeds_tokens",
            "--cs-teal: #16756a" in html and "--cs-canvas: #f4f6f3" in html,
            "tokens",
            "design_system",
        )
    )
    checks.append(
        CheckResult(
            "renderer:no_script",
            "<script" not in html.lower(),
            "no_script",
            "offline",
        )
    )
    checks.append(
        CheckResult(
            "renderer:no_stylesheet_link",
            'rel="stylesheet"' not in html.lower(),
            "no_link",
            "offline",
        )
    )
    checks.append(
        CheckResult(
            "renderer:csp",
            "script-src 'none'" in html and "font-src 'none'" in html,
            "csp",
            "offline",
        )
    )
    for section_id in STABLE_SECTION_IDS:
        ok = f'id="{section_id}"' in html
        checks.append(
            CheckResult(
                f"renderer:anchor:{section_id}",
                ok,
                section_id,
                "navigation",
            )
        )
        if not ok:
            defects.append(
                Defect("navigation defect", section_id, "present", "missing")
            )
    checks.append(
        CheckResult(
            "renderer:report_shell",
            'class="report-shell"' in html and "report-product-bar" in html,
            "shell",
            "report_shell",
        )
    )
    checks.append(
        CheckResult(
            "renderer:main_landmark",
            'role="main"' in html and 'id="main-content"' in html,
            "main",
            "accessibility",
        )
    )
    checks.append(
        CheckResult(
            "renderer:single_h1",
            len(re.findall(r"<h1\b", html, flags=re.I)) == 1,
            "h1",
            "accessibility",
        )
    )
    checks.append(
        CheckResult(
            "renderer:exec_summary",
            'id="executive-summary"' in html,
            "exec",
            "executive_summary",
        )
    )
    checks.append(
        CheckResult(
            "renderer:findings_severity_text",
            "aria-label=\"Severity:" in html or "severity-" in html,
            "severity_text",
            "finding",
        )
    )
    checks.append(
        CheckResult(
            "renderer:evidence_present",
            "evidence" in html.lower(),
            "evidence",
            "evidence",
        )
    )
    checks.append(
        CheckResult(
            "renderer:recommendation_cards",
            "recommendation" in html.lower(),
            "recs",
            "recommendation",
        )
    )
    checks.append(
        CheckResult(
            "renderer:print_css",
            "@media print" in html,
            "print",
            "print",
        )
    )
    checks.append(
        CheckResult(
            "renderer:responsive_media",
            "@media (max-width:" in html,
            "responsive",
            "responsive",
        )
    )
    checks.append(
        CheckResult(
            "renderer:prefers_color_scheme",
            "prefers-color-scheme: dark" in html,
            "dark",
            "design_system",
        )
    )
    checks.append(
        CheckResult(
            "renderer:focus_visible",
            ":focus-visible" in html,
            "focus",
            "accessibility",
        )
    )
    checks.append(
        CheckResult(
            "renderer:reduced_motion",
            "prefers-reduced-motion" in html,
            "motion",
            "accessibility",
        )
    )
    checks.append(
        CheckResult(
            "renderer:no_fonts_googleapis",
            "fonts.googleapis.com" not in html.lower()
            and "cdn." not in html.lower(),
            "offline_fonts",
            "offline",
        )
    )
    checks.append(
        CheckResult(
            "renderer:no_legacy_amber",
            "#b06a24" not in html.lower() and "#d98a3d" not in html.lower(),
            "no_amber",
            "legacy_style",
        )
    )
    return checks, defects, html
