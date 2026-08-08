"""Brand identity checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_identity(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    master = inv.brand_masters.get("codestrata-mark.svg", "")

    add(
        checks,
        "identity:single_brand_authority",
        "codestrata-mark.svg" in inv.brand_masters
        and "codestrata-wordmark.svg" in inv.brand_masters,
        "masters_present",
        "identity",
    )
    add(
        checks,
        "identity:master_viewbox_22",
        'viewBox="0 0 22 22"' in master or "viewBox='0 0 22 22'" in master,
        "22x22_lineage",
        "identity",
    )
    add(
        checks,
        "identity:docs_derivative",
        (inv.monorepo / "docs/public/brand/icon.svg").is_file(),
        "docs_mark",
        "identity",
    )
    add(
        checks,
        "identity:swagger_derivative",
        (inv.monorepo / "platform/api/openapi/swagger/brand/icon.svg").is_file(),
        "swagger_mark",
        "identity",
    )
    add(
        checks,
        "identity:assessment_product_bar_mark",
        "report-product-mark" in inv.assessment_renderer
        and "report-product-mark" in inv.assessment_styles,
        "assessment_bar",
        "identity",
    )
    add(
        checks,
        "identity:eir_product_bar_mark",
        "report-product-mark" in inv.eir_renderer
        and "report-product-mark" in inv.eir_styles,
        "eir_bar",
        "identity",
    )
    add(
        checks,
        "identity:vscode_activity_derivative",
        (inv.monorepo / "vscode-plugin/media/codestrata-activity.svg").is_file(),
        "activity_icon",
        "identity",
    )
    return checks
