"""Documentation consumer checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add, scan_hex
from verification.cross_surface_visual_consistency.contract import LEGACY_AMBER_HEX
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_docs_consumer(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    add(
        checks,
        "docs_consumer:tokens_bridge",
        "--cs-teal" in inv.docs_theme_tokens,
        "theme_tokens",
        "docs_consumer",
    )
    add(
        checks,
        "docs_consumer:public_mirror",
        not scan_hex(inv.public_tokens, LEGACY_AMBER_HEX),
        "public_clean",
        "docs_consumer",
    )
    add(
        checks,
        "docs_consumer:brand_assets",
        (inv.monorepo / "docs/public/favicon.svg").is_file(),
        "favicon",
        "docs_consumer",
    )
    return checks
