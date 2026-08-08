"""Report shell consistency checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_report_shells(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []

    add(
        checks,
        "report_shells:assessment_product_bar",
        "report-product-mark" in inv.assessment_html,
        "assessment_mark_in_html",
        "report_shells",
    )
    add(
        checks,
        "report_shells:eir_product_bar",
        "report-product-mark" in inv.eir_html,
        "eir_mark_in_html",
        "report_shells",
    )
    add(
        checks,
        "report_shells:assessment_footer",
        "footer" in inv.assessment_styles.lower(),
        "assessment_footer",
        "report_shells",
    )
    add(
        checks,
        "report_shells:eir_footer",
        "footer" in inv.eir_styles.lower(),
        "eir_footer",
        "report_shells",
    )
    add(
        checks,
        "report_shells:shared_language",
        "CodeStrata" in inv.assessment_html and "CodeStrata" in inv.eir_html,
        "codestrata_both",
        "report_shells",
    )
    return checks
