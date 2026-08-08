"""Shared component family checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_components(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []

    add(
        checks,
        "components:assessment_product_bar",
        "report-product-bar" in inv.assessment_styles,
        "assessment_bar",
        "components",
    )
    add(
        checks,
        "components:eir_product_bar",
        "report-product-bar" in inv.eir_styles,
        "eir_bar",
        "components",
    )
    add(
        checks,
        "components:assessment_table_wrap",
        "table-wrap" in inv.assessment_styles,
        "assessment_tables",
        "components",
    )
    add(
        checks,
        "components:eir_table_wrap",
        "table-wrap" in inv.eir_styles,
        "eir_tables",
        "components",
    )
    add(
        checks,
        "components:assessment_badges",
        "status-badge" in inv.assessment_styles or "risk-badge" in inv.assessment_styles,
        "assessment_badges",
        "components",
    )
    add(
        checks,
        "components:eir_badges",
        "status-badge" in inv.eir_styles or "risk-badge" in inv.eir_styles,
        "eir_badges",
        "components",
    )
    return checks
