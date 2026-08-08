"""EIR consumer checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_eir_consumer(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    add(
        checks,
        "eir_consumer:design_system_tokens",
        "--cs-" in inv.eir_styles,
        "token_usage",
        "eir_consumer",
    )
    add(
        checks,
        "eir_consumer:product_bar_mark",
        "report-product-mark" in inv.eir_renderer,
        "mark_present",
        "eir_consumer",
    )
    add(
        checks,
        "eir_consumer:html_renders",
        bool(inv.eir_html),
        "html_ok" if inv.eir_html else "render_failed",
        "eir_consumer",
    )
    return checks
