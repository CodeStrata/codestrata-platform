"""Accessibility regression spot checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_accessibility_regression(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    combined_reports = inv.assessment_styles + inv.eir_styles + inv.assessment_html

    add(
        checks,
        "accessibility_regression:skip_link",
        "skip" in inv.docs_custom_css.lower()
        or "skip" in inv.assessment_styles.lower(),
        "skip_link",
        "accessibility_regression",
    )
    add(
        checks,
        "accessibility_regression:focus_visible",
        "focus-visible" in inv.docs_custom_css
        or ":focus-visible" in inv.assessment_styles,
        "focus_visible",
        "accessibility_regression",
    )
    add(
        checks,
        "accessibility_regression:forced_colors",
        "forced-colors" in inv.docs_custom_css
        or "forced-colors" in inv.assessment_styles,
        "forced_colors",
        "accessibility_regression",
    )
    add(
        checks,
        "accessibility_regression:lang_en",
        'lang="en"' in inv.assessment_html or 'lang="en"' in inv.eir_html,
        "lang_en",
        "accessibility_regression",
    )
    add(
        checks,
        "accessibility_regression:reports_landmarks",
        "<main" in combined_reports or "role=\"main\"" in combined_reports,
        "landmarks",
        "accessibility_regression",
    )
    return checks
