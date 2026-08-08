"""Negative scenario posture checks (A–Z)."""

from __future__ import annotations

from verification.responsive_accessibility.contrast import contrast_ratio
from verification.responsive_accessibility.contract import FORBIDDEN_15_7_PATHS
from verification.responsive_accessibility.determinism import check_determinism
from verification.responsive_accessibility.inventory import SurfaceInventory, token_colors
from verification.responsive_accessibility.models import CheckResult

_CATEGORY = "scenarios"


def run_negative_scenarios(inv: SurfaceInventory) -> list[CheckResult]:
    colors = token_colors(inv)
    assessment_styles = inv.assessment_styles
    eir_styles = inv.eir_styles
    docs_css = inv.docs_css
    policy = inv.policy

    ink = colors.get("ink", "#111815")
    canvas = colors.get("canvas", "#f4f6f3")
    normal_ratio = contrast_ratio(ink, canvas)

    large_fg = colors.get("teal_dark", colors.get("teal", ink))
    large_ratio = contrast_ratio(large_fg, canvas)

    focus_fg = colors.get("teal_light", "#35b3a4")
    focus_bg = colors.get("night", "#101a17")
    focus_ratio = contrast_ratio(focus_fg, focus_bg)

    determinism_ok = all(c.ok for c in check_determinism(inv)[0])

    # Outputs must never embed host paths. Verifier source may mention the
    # forbidden prefixes only inside negative assertions.
    leak_haystack = "\n".join(
        (
            inv.assessment_html,
            inv.eir_html,
            inv.assessment_partial_html,
            inv.eir_empty_html,
            inv.marketplace_readme,
        )
    )
    home_prefix = "/Users" + "/"
    linux_home_prefix = "/home" + "/"
    output_leaks = home_prefix in leak_haystack or linux_home_prefix in leak_haystack

    scenarios: list[tuple[str, str, bool]] = [
        (
            "A",
            "contrast_below_normal",
            normal_ratio >= 4.5,
        ),
        (
            "B",
            "large_text_below_3",
            large_ratio >= 3.0,
        ),
        (
            "C",
            "graphical_below_3",
            focus_ratio >= 3.0,
        ),
        (
            "D",
            "focus_outline_removed",
            not (
                ("outline: none" in assessment_styles or "outline:none" in assessment_styles)
                and ":focus-visible" not in assessment_styles
            ),
        ),
        (
            "E",
            "skip_link_target_missing",
            'id="main-content"' in inv.assessment_html and 'id="main"' in inv.eir_html,
        ),
        (
            "F",
            "heading_hierarchy_broken",
            inv.assessment_html.lower().count("<h1") == 1
            and inv.eir_html.lower().count("<h1") == 1,
        ),
        (
            "G",
            "nav_lacks_label",
            'aria-label="Table of contents"' in inv.assessment_html
            and 'aria-label="Table of contents"' in inv.eir_html,
        ),
        (
            "H",
            "table_lacks_headers",
            "<th" in inv.assessment_html.lower() or "<th" in inv.eir_html.lower(),
        ),
        (
            "I",
            "informative_image_missing_alt",
            inv.marketplace_readme.count("![") >= 5,
        ),
        (
            "J",
            "decorative_logo_announced",
            'aria-hidden="true"' in inv.assessment_html and "cs-mark" in inv.assessment_html,
        ),
        (
            "K",
            "status_color_only",
            "severity-" in assessment_styles and "::before" in assessment_styles,
        ),
        (
            "L",
            "risk_label_disappears_in_print",
            "@media print" in assessment_styles
            and (".badge" in assessment_styles or ".status-badge" in assessment_styles),
        ),
        (
            "M",
            "confidence_color_only",
            "confidence-badge" in inv.eir_html or "confidence" not in inv.eir_html.lower(),
        ),
        (
            "N",
            "mobile_overflow_docs",
            ".VPDoc table" in inv.docs_components_css
            and "overflow-x: auto" in inv.docs_components_css,
        ),
        (
            "O",
            "mobile_overflow_assessment",
            "overflow-x: auto" in assessment_styles,
        ),
        (
            "P",
            "mobile_overflow_eir",
            "overflow-x: auto" in eir_styles or "table-wrap" in eir_styles,
        ),
        (
            "Q",
            "code_clips",
            "overflow-wrap: anywhere" in assessment_styles,
        ),
        (
            "R",
            "table_page_overflow",
            "table-wrap" in assessment_styles and "overflow-x: auto" in assessment_styles,
        ),
        (
            "S",
            "mobile_nav_target_too_small",
            "min-height: 44px" in inv.docs_custom_css,
        ),
        (
            "T",
            "reduced_motion_ignored",
            "prefers-reduced-motion" in assessment_styles
            and "@keyframes" not in assessment_styles,
        ),
        (
            "U",
            "dark_focus_invisible",
            "--cs-teal-light" in inv.engine_tokens and "--cs-focus" in inv.engine_tokens,
        ),
        (
            "V",
            "svg_mark_loses_contrast",
            "currentColor" in inv.vscode_activity_icon,
        ),
        (
            "W",
            "verifier_changes_domain_semantics",
            policy.get("expected_unchanged", {}).get("assessment_schema_version") == "1.2",
        ),
        (
            "X",
            "slice_14_14_starts",
            not any((inv.monorepo / path).exists() for path in FORBIDDEN_15_7_PATHS),
        ),
        (
            "Y",
            "verifier_nondeterministic",
            determinism_ok,
        ),
        (
            "Z",
            "verification_leaks_paths",
            not output_leaks,
        ),
    ]

    return [
        CheckResult(
            f"negative:{letter}_{name}",
            ok,
            letter,
            _CATEGORY,
        )
        for letter, name, ok in scenarios
    ]
