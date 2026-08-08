"""Marketplace consumer checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_marketplace_consumer(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    add(
        checks,
        "marketplace_consumer:mapping_present",
        bool(inv.marketplace_mapping),
        "mapping",
        "marketplace_consumer",
    )
    add(
        checks,
        "marketplace_consumer:raster_exception",
        "raster" in inv.marketplace_mapping.lower()
        or "128" in inv.marketplace_mapping,
        "raster",
        "marketplace_consumer",
    )
    add(
        checks,
        "marketplace_consumer:icon_exists",
        (inv.monorepo / "vscode-plugin/media/codestrata-icon.png").is_file(),
        "icon_png",
        "marketplace_consumer",
    )
    return checks
