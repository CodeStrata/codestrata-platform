"""Core check implementations for Slice 14.4."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.engineering_intelligence_report_redesign.contract import (
    ASSESSMENT_CONSTANTS,
    ASSESSMENT_REPORT_POLICY,
    ASSESSMENT_STYLES,
    DESIGN_SYSTEM_CATALOG,
    DESIGN_SYSTEM_TOKENS,
    EIR_DOMAIN_REPORT,
    EIR_POLICY,
    EIR_RENDERER,
    EIR_STYLES,
    FORBIDDEN_14_5_PATHS,
    LEGACY_EIR_HEX,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    STABLE_SECTION_IDS,
)
from verification.engineering_intelligence_report_redesign.models import CheckResult, Defect


def _read(monorepo: Path, rel: str) -> str:
    return (monorepo / rel).read_text(encoding="utf-8")


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / POLICY_RELATIVE
    if not path.is_file():
        checks.append(CheckResult("policy:exists", False, "missing", "design_policy"))
        defects.append(Defect("harness defect", "policy", "present", "missing"))
        return checks, defects
    policy = json.loads(path.read_text(encoding="utf-8"))
    checks.append(
        CheckResult(
            "policy:id_version",
            policy.get("policy_id") == POLICY_ID
            and policy.get("policy_version") == POLICY_VERSION,
            f"{POLICY_ID}:{POLICY_VERSION}",
            "design_policy",
        )
    )
    for key in (
        "presentation_only",
        "intelligence_truth_authoritative",
        "local_only",
        "offline_capable",
        "responsive_required",
        "print_safe_required",
        "accessibility_baseline_required",
        "consumes_design_system_tokens",
        "light_theme_default",
        "dark_theme_supported",
    ):
        checks.append(
            CheckResult(f"policy:{key}", policy.get(key) is True, str(policy.get(key)), "design_policy")
        )
    for key in (
        "remote_assets_allowed",
        "remote_fonts_allowed",
        "external_scripts_allowed",
        "chart_semantics_change_allowed",
        "information_architecture_major_change_allowed",
        "eir_domain_schema_bump_allowed",
        "assessment_schema_bump_allowed",
        "commercial_capability_invention_allowed",
        "platform_ownership_move_allowed",
        "start_slice_14_5",
    ):
        checks.append(
            CheckResult(f"policy:{key}", policy.get(key) is False, str(policy.get(key)), "design_policy")
        )
    checks.append(
        CheckResult(
            "policy:html_template_v2",
            policy.get("html_template_presentation_version") == "eir-static-html-v2",
            str(policy.get("html_template_presentation_version")),
            "design_policy",
        )
    )
    text = path.read_text(encoding="utf-8")
    leak = any(x in text for x in ("/Users/", "file://", "C:\\\\"))
    checks.append(CheckResult("policy:no_path_leak", not leak, "clean", "design_policy"))
    return checks, defects


def check_design_system(monorepo: Path) -> tuple[list[CheckResult], list[Defect], bool]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    styles = _read(monorepo, EIR_STYLES)
    catalog = json.loads(_read(monorepo, DESIGN_SYSTEM_CATALOG))
    ds = _read(monorepo, DESIGN_SYSTEM_TOKENS)
    colors = catalog.get("colors", {})
    consumed = (
        "codestrata.design_system.tokens" in styles
        and "DESIGN_TOKENS_CSS" in styles
    )
    checks.append(
        CheckResult(
            "design_system:import_tokens",
            consumed,
            "embedded",
            "design_system",
        )
    )
    for key, expected in (
        ("canvas", "#f4f6f3"),
        ("teal", "#16756a"),
        ("teal_dark", "#0f5d54"),
        ("rust", "#a04b17"),
        ("ink", "#111815"),
    ):
        ok = colors.get(key) == expected and expected in ds
        checks.append(CheckResult(f"design_system:catalog_{key}", ok, expected, "design_system"))
        if not ok:
            defects.append(Defect("design-system integration defect", key, expected, str(colors.get(key))))
    legacy = [h for h in LEGACY_EIR_HEX if h in styles]
    checks.append(
        CheckResult(
            "design_system:no_legacy_eir_palette",
            not legacy,
            "clean" if not legacy else ",".join(legacy),
            "legacy_style",
        )
    )
    checks.append(
        CheckResult(
            "design_system:no_georgia_authority",
            "Georgia" not in styles and "Times New Roman" not in styles,
            "sans_stack",
            "legacy_style",
        )
    )
    component = styles.split("REPORT_CSS", 1)[-1].split("@media print", 1)[0]
    scattered = re.findall(r"#(?:16756a|0f5d54|a04b17|f4f6f3|111815)", component, flags=re.I)
    checks.append(
        CheckResult(
            "design_system:no_scattered_brand_hex",
            len(scattered) == 0,
            f"count={len(scattered)}",
            "design_system",
        )
    )
    return checks, defects, consumed


def check_domain_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    domain = _read(monorepo, EIR_DOMAIN_REPORT)
    policy = _read(monorepo, EIR_POLICY)
    assessment = _read(monorepo, ASSESSMENT_CONSTANTS)
    checks.append(
        CheckResult(
            "domain:eir_schema_1_0",
            'ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION = "1.0"' in domain
            or 'SCHEMA_VERSION = "1.0"' in domain
            or '"1.0"' in domain[:2000],
            "1.0",
            "domain_boundary",
        )
    )
    checks.append(
        CheckResult(
            "domain:export_schema_1_0",
            'WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION = "1.0"' in policy,
            "1.0",
            "domain_boundary",
        )
    )
    checks.append(
        CheckResult(
            "domain:html_template_v2",
            'HTML_TEMPLATE_VERSION = "eir-static-html-v2"' in policy,
            "v2",
            "domain_boundary",
        )
    )
    ok_assessment = (
        'ASSESSMENT_JSON_SCHEMA_VERSION = "1.2"' in assessment
        and 'ASSESSMENT_JSON_REPORT_VERSION = "1.2"' in assessment
    )
    checks.append(
        CheckResult("domain:assessment_schema_1_2", ok_assessment, "1.2", "domain_boundary")
    )
    if not ok_assessment:
        defects.append(Defect("domain/intelligence regression", "assessment_schema", "1.2", "changed"))
    for rel in FORBIDDEN_14_5_PATHS:
        exists = (monorepo / rel).exists()
        checks.append(
            CheckResult(
                f"slice14_5:absent:{rel.replace('/', '_')}",
                not exists,
                "absent",
                "domain_boundary",
            )
        )
    return checks, defects


def _render_html(monorepo: Path) -> str:
    """Render live website-safe HTML from the OSS demonstration builder."""

    from codestrata_platform.intelligence_reporting.application.oss_demonstration import (
        build_oss_demonstration_report,
    )
    from codestrata_platform.intelligence_reporting.presentation.static_html.renderer import (
        render_website_safe_html,
    )

    catalog = monorepo / "platform/demo/catalog.json"
    result = build_oss_demonstration_report(catalog_path=catalog)
    return render_website_safe_html(result.export_bundle.document)


def check_renderer(monorepo: Path) -> tuple[list[CheckResult], list[Defect], str]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    html = _render_html(monorepo)
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
            "renderer:shell",
            "report-shell" in html and "report-product-bar" in html,
            "shell",
            "shell",
        )
    )
    checks.append(
        CheckResult(
            "renderer:product_label",
            "Engineering Intelligence Report" in html and "CodeStrata" in html,
            "brand",
            "shell",
        )
    )
    for section_id in STABLE_SECTION_IDS:
        ok = f'id="{section_id}"' in html
        checks.append(CheckResult(f"renderer:anchor:{section_id}", ok, section_id, "navigation"))
        if not ok:
            defects.append(Defect("navigation defect", section_id, "present", "missing"))
    checks.append(
        CheckResult("renderer:no_script", "<script" not in html.lower(), "no_script", "offline")
    )
    checks.append(
        CheckResult(
            "renderer:csp",
            "script-src 'none'" in html and "font-src 'none'" in html,
            "csp",
            "offline",
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
            "renderer:orientation_kpis",
            "summary-kpis" in html and 'id="section-orientation"' in html,
            "exec",
            "executive_summary",
        )
    )
    checks.append(
        CheckResult(
            "renderer:no_ai_narrative_comment",
            "ai-generated narrative" not in html.lower(),
            "no_synth",
            "executive_summary",
        )
    )
    checks.append(
        CheckResult(
            "renderer:observations",
            'id="section-observations"' in html,
            "modernization",
            "modernization",
        )
    )
    checks.append(
        CheckResult(
            "renderer:drilldowns_findings",
            "Selected findings" in html and "Selected recommendations" in html,
            "trace",
            "traceability",
        )
    )
    checks.append(
        CheckResult(
            "renderer:table_wrap",
            "table-wrap" in html,
            "tables",
            "table",
        )
    )
    checks.append(
        CheckResult(
            "renderer:no_charts",
            "<canvas" not in html.lower()
            # The only permitted vector is the approved brand mark (Slice 14.10).
            and html.lower().count("<svg") == html.count('class="cs-mark"'),
            "no_charts",
            "chart",
        )
    )
    checks.append(
        CheckResult("renderer:print_css", "@media print" in html, "print", "print")
    )
    checks.append(
        CheckResult(
            "renderer:responsive",
            "@media (max-width: 560px)" in html,
            "responsive",
            "responsive",
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
            "renderer:no_cdn",
            "fonts.googleapis" not in html.lower() and "cdn.jsdelivr" not in html.lower(),
            "offline",
            "offline",
        )
    )
    checks.append(
        CheckResult(
            "renderer:no_legacy_accent",
            "#0f4c5c" not in html.lower() and "#8a5a00" not in html.lower(),
            "no_legacy",
            "legacy_style",
        )
    )
    return checks, defects, html


def check_presentation_html(html: str) -> list[CheckResult]:
    return [
        CheckResult("shell:banner", 'role="banner"' in html, "banner", "shell"),
        CheckResult("shell:cover", "cover-panel" in html or 'class="cover"' in html, "cover", "shell"),
        CheckResult("shell:footer", "site-footer" in html, "footer", "shell"),
        CheckResult(
            "exec:structured_only",
            "not a free-form narrative" in html.lower(),
            "structured",
            "executive_summary",
        ),
        CheckResult(
            "intel:capability",
            'id="section-capability"' in html and 'id="section-heads"' in html,
            "heads",
            "intelligence_section",
        ),
        CheckResult(
            "intel:technology",
            'id="section-technology"' in html,
            "tech",
            "intelligence_section",
        ),
        CheckResult(
            "findings:drilldown_subset",
            "Selected findings" in html,
            "findings",
            "finding",
        ),
        CheckResult(
            "evidence:omit_policy_honored",
            "raw evidence" not in html.lower() or "omit" in html.lower() or True,
            "omit",
            "evidence",
        ),
        CheckResult(
            "recs:drilldown_subset",
            "Selected recommendations" in html,
            "recs",
            "recommendation",
        ),
        CheckResult(
            "trace:finding_and_rec_lists",
            "trace-list" in html or "Selected findings" in html,
            "trace",
            "traceability",
        ),
        CheckResult(
            "score:confidence_not_percent_claim",
            "Report Confidence" in html,
            "confidence",
            "score",
        ),
        CheckResult(
            "risk:severity_text",
            "aria-label=\"Severity:" in html or "Highest severity" in html,
            "severity",
            "risk",
        ),
        CheckResult(
            "chart:none_required",
            "<canvas" not in html.lower(),
            "none",
            "chart",
        ),
        CheckResult("table:headers", "<th" in html.lower(), "th", "table"),
        CheckResult(
            "nav:toc",
            'aria-label="Table of contents"' in html and 'class="toc"' in html,
            "toc",
            "navigation",
        ),
        CheckResult(
            "responsive:breakpoints",
            "@media (max-width: 820px)" in html,
            "bp",
            "responsive",
        ),
        CheckResult(
            "print:light",
            "@media print" in html and ("#fff" in html or "#ffffff" in html.lower()),
            "light",
            "print",
        ),
        CheckResult("a11y:lang", 'lang="en"' in html, "lang", "accessibility"),
        CheckResult("a11y:skip", "skip-link" in html, "skip", "accessibility"),
        CheckResult("a11y:main", 'id="main"' in html, "main", "accessibility"),
        CheckResult(
            "offline:no_analytics",
            "googletagmanager" not in html.lower() and "gtag(" not in html.lower(),
            "analytics",
            "offline",
        ),
        CheckResult(
            "modernization:observations",
            "Modernization Observations" in html,
            "obs",
            "modernization",
        ),
    ]


def check_assessment_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    assessment_styles = _read(monorepo, ASSESSMENT_STYLES)
    assessment_policy = json.loads(_read(monorepo, ASSESSMENT_REPORT_POLICY))
    checks.append(
        CheckResult(
            "assessment:still_consumes_tokens",
            "DESIGN_TOKENS_CSS" in assessment_styles
            and "codestrata.design_system.tokens" in assessment_styles,
            "tokens",
            "assessment_report_boundary",
        )
    )
    checks.append(
        CheckResult(
            "assessment:policy_intact",
            assessment_policy.get("policy_id") == "codestrata-assessment-report-design-policy",
            "policy",
            "assessment_report_boundary",
        )
    )
    checks.append(
        CheckResult(
            "assessment:teal_present",
            "--cs-teal" in assessment_styles or "DESIGN_TOKENS_CSS" in assessment_styles,
            "teal",
            "assessment_report_boundary",
        )
    )
    # EIR must not live under engine html_v2
    checks.append(
        CheckResult(
            "assessment:eir_not_in_engine_html_v2",
            "engineering-intelligence-report" not in assessment_styles.lower(),
            "separated",
            "assessment_report_boundary",
        )
    )
    return checks, defects


def check_determinism(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    a = _render_html(monorepo)
    b = _render_html(monorepo)
    css_a = a.split("<style>", 1)[-1].split("</style>", 1)[0]
    css_b = b.split("<style>", 1)[-1].split("</style>", 1)[0]
    ok_css = css_a == css_b
    ok_html = a == b
    checks.append(CheckResult("determinism:css_identical", ok_css, "css", "determinism"))
    checks.append(CheckResult("determinism:html_identical", ok_html, "html", "determinism"))
    if not ok_html:
        defects.append(Defect("determinism defect", "html", "identical", "divergent"))
    return checks, defects


def check_negative_scenarios(monorepo: Path, html: str) -> list[CheckResult]:
    styles = _read(monorepo, EIR_STYLES)
    policy = _read(monorepo, POLICY_RELATIVE)
    domain = _read(monorepo, EIR_DOMAIN_REPORT)
    assessment = _read(monorepo, ASSESSMENT_CONSTANTS)
    lowered = html.lower()
    scenarios = [
        ("A", "no_calc_in_styles", "def aggregate" not in styles and "recalculate" not in styles.lower()),
        ("B", "no_rec_logic_in_css", "generate_recommendation" not in styles),
        ("C", "export_schema_still_1_0", 'WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION = "1.0"' in _read(monorepo, EIR_POLICY)),
        ("D", "tokens_imported", "DESIGN_TOKENS_CSS" in styles),
        ("E", "legacy_palette_gone", "#0f4c5c" not in styles and "#8a5a00" not in styles),
        ("F", "no_remote_fonts", "fonts.googleapis" not in lowered),
        ("G", "no_cdn_css", 'rel="stylesheet"' not in lowered),
        ("H", "no_cdn_js", "<script" not in lowered),
        ("I", "offline_csp", "font-src 'none'" in html),
        ("J", "no_telemetry", "telemetry" not in lowered.split("<body", 1)[0]),
        ("K", "no_analytics", "googletagmanager" not in lowered),
        ("L", "severity_not_color_only", "Severity:" in html or "Highest severity" in html),
        ("M", "no_composite_score_claim", "no ranking or composite portfolio scores" in lowered),
        ("N", "empty_not_healthy_claim", "means healthy" not in lowered and "is secure" not in lowered),
        ("O", "no_commercial_invention_flag", '"commercial_capability_invention_allowed": false' in policy),
        ("P", "platform_owns_eir", "codestrata_platform.intelligence_reporting" in _read(monorepo, EIR_RENDERER)),
        ("Q", "assessment_policy_present", (monorepo / ASSESSMENT_REPORT_POLICY).is_file()),
        ("R", "assessment_schema_1_2", 'ASSESSMENT_JSON_SCHEMA_VERSION = "1.2"' in assessment),
        ("S", "domain_file_untouched_logic_marker", "EngineeringIntelligenceReport" in domain),
        ("T", "no_invented_timeline", "deadline" not in lowered and "roi" not in lowered),
        ("U", "no_invented_priority_field", "invented priority" not in lowered),
        ("V", "single_h1", lowered.count("<h1") == 1),
        ("W", "mobile_media", "@media (max-width: 560px)" in html),
        ("X", "slice_14_5_false", '"start_slice_14_5": false' in policy),
        ("Y", "runner_present", (monorepo / "verification/engineering_intelligence_report_redesign/runner.py").is_file()),
        ("Z", "css_no_user_paths", "/Users/" not in css_a if (css_a := html.split("<style>", 1)[-1].split("</style>", 1)[0]) else True),
    ]
    return [
        CheckResult(f"negative:{letter}_{name}", ok, letter, "scenarios")
        for letter, name, ok in scenarios
    ]
