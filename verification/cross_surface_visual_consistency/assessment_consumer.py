"""Assessment report consumer checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_assessment_consumer(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    add(
        checks,
        "assessment_consumer:design_system_tokens",
        "design_system" in inv.assessment_styles or "--cs-" in inv.assessment_styles,
        "token_usage",
        "assessment_consumer",
    )
    add(
        checks,
        "assessment_consumer:product_bar_mark",
        "report-product-mark" in inv.assessment_renderer,
        "mark_present",
        "assessment_consumer",
    )
    add(
        checks,
        "assessment_consumer:html_renders",
        bool(inv.assessment_html),
        "html_ok" if inv.assessment_html else "render_failed",
        "assessment_consumer",
    )
    return checks
