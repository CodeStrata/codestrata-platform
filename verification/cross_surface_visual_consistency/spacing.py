"""Spacing consistency checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_spacing(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    presentation = inv.presentation_contract
    token_css = inv.token_css
    report_css = inv.assessment_styles + inv.eir_styles
    docs_css = inv.docs_theme_tokens + inv.docs_custom_css + inv.token_css

    add(
        checks,
        "spacing:presentation_contract",
        bool(presentation.get("spacing")),
        "presentation_spacing",
        "spacing",
    )
    add(
        checks,
        "spacing:token_scale",
        "--cs-space" in token_css,
        "cs_space_tokens",
        "spacing",
    )
    add(
        checks,
        "spacing:reports_use_tokens",
        "--cs-space" in report_css,
        "report_spacing",
        "spacing",
    )
    add(
        checks,
        "spacing:docs_no_competing_scale",
        "--cs-space" in docs_css or "var(--cs-space" in docs_css,
        "docs_spacing",
        "spacing",
    )
    return checks
