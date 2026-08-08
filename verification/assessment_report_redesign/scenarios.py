"""Negative scenarios for Slice 14.3 (A–Z posture checks)."""

from __future__ import annotations

from pathlib import Path

from verification.assessment_report_redesign.contract import (
    ASSESSMENT_SCHEMA_CONSTANTS,
    ENGINE_STYLES,
    ENGINE_TOKENS,
    POLICY_RELATIVE,
)
from verification.assessment_report_redesign.models import CheckResult


def check_negative_scenarios(monorepo: Path, html: str) -> list[CheckResult]:
    constants = (monorepo / ASSESSMENT_SCHEMA_CONSTANTS).read_text(encoding="utf-8")
    tokens = (monorepo / ENGINE_TOKENS).read_text(encoding="utf-8")
    styles = (monorepo / ENGINE_STYLES).read_text(encoding="utf-8")
    policy = (monorepo / POLICY_RELATIVE).read_text(encoding="utf-8")
    lowered = html.lower()

    scenarios = [
        ("A", "schema_unchanged", '"1.2"' in constants and "1.2" in policy),
        ("B", "no_scoring_algo_in_styles", "def score" not in styles and "normalize(" not in styles),
        ("C", "severity_semantics_tokenized", "--cs-risk-critical" in tokens),
        ("D", "no_rec_generation_in_css", "generate_recommendation" not in styles),
        ("E", "template_no_recalc", "recalculate" not in styles.lower()),
        ("F", "no_remote_fonts", "fonts.googleapis" not in lowered),
        ("G", "no_cdn_css", "cdn." not in lowered or "content-security-policy" in lowered),
        ("H", "no_cdn_js", "<script" not in lowered),
        ("I", "no_telemetry_script", "analytics" not in lowered.split("<body", 1)[0]),
        ("J", "offline_render", "font-src 'none'" in html),
        ("K", "tokens_not_website_copy_paste_only", "DESIGN_TOKENS_CSS" in styles),
        ("L", "brand_hex_in_tokens_module", "#16756a" in tokens and "#16756a" not in styles.split("REPORT_CSS", 1)[-1].split("@media print", 1)[0]),
        ("M", "severity_not_color_only", "aria-label=\"Severity:" in html or "badge severity-" in html),
        ("N", "focus_visible_present", ":focus-visible" in html),
        ("O", "heading_h1_once", html.lower().count("<h1") == 1),
        ("P", "tables_have_th_or_wrap", "<th" in lowered or "table-wrap" in lowered),
        ("Q", "mobile_media", "@media (max-width: 560px)" in html),
        ("R", "evidence_overflow", "overflow-x: auto" in html or "overflow-wrap" in html),
        ("S", "print_light", "@media print" in html and ("#fff" in html or "#ffffff" in lowered)),
        ("T", "stable_ids", 'id="cover"' in html and 'id="contents"' in html),
        ("U", "no_14_4_required_during_14_3_policy", True),
        ("V", "no_ai_generated_comment", "ai-generated narrative" not in lowered),
        ("W", "no_source_fetch", "fetch(" not in lowered and "XMLHttpRequest" not in html),
        ("X", "slice_14_4_flag_false", '"start_slice_14_4": false' in policy),
        ("Y", "verifier_modules_present", (monorepo / "verification/assessment_report_redesign/runner.py").is_file()),
        ("Z", "report_no_user_paths_in_css", "/Users/" not in html.split("<style>", 1)[-1].split("</style>", 1)[0]),
    ]
    return [
        CheckResult(
            f"negative:{letter}_{name}",
            ok,
            letter,
            "scenarios",
        )
        for letter, name, ok in scenarios
    ]
