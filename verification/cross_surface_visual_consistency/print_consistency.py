"""Print consistency checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_print_consistency(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    add(
        checks,
        "print_consistency:assessment_print_media",
        "@media print" in inv.assessment_styles,
        "assessment_print",
        "print_consistency",
    )
    add(
        checks,
        "print_consistency:eir_print_media",
        "@media print" in inv.eir_styles,
        "eir_print",
        "print_consistency",
    )
    add(
        checks,
        "print_consistency:assessment_hides_chrome",
        "product-bar" in inv.assessment_styles and "@media print" in inv.assessment_styles,
        "assessment_chrome",
        "print_consistency",
    )
    return checks
