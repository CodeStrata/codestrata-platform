"""Responsive regression spot checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_responsive_regression(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    add(
        checks,
        "responsive_regression:docs_media_queries",
        "@media" in inv.docs_custom_css or "@media" in inv.docs_components_css,
        "docs_mq",
        "responsive_regression",
    )
    add(
        checks,
        "responsive_regression:assessment_media_queries",
        "@media" in inv.assessment_styles,
        "assessment_mq",
        "responsive_regression",
    )
    add(
        checks,
        "responsive_regression:eir_media_queries",
        "@media" in inv.eir_styles,
        "eir_mq",
        "responsive_regression",
    )
    add(
        checks,
        "responsive_regression:assessment_table_overflow",
        "table-wrap" in inv.assessment_styles or "overflow-x" in inv.assessment_styles,
        "assessment_overflow",
        "responsive_regression",
    )
    return checks
