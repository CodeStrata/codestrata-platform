"""API portal (Swagger) consumer checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add, scan_hex
from verification.cross_surface_visual_consistency.contract import LEGACY_AMBER_HEX
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_api_portal_consumer(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    add(
        checks,
        "api_portal_consumer:token_bridge",
        "--cs-teal" in inv.swagger_tokens,
        "swagger_tokens",
        "api_portal_consumer",
    )
    add(
        checks,
        "api_portal_consumer:no_amber_css",
        not scan_hex(inv.swagger_css, LEGACY_AMBER_HEX),
        "css_clean",
        "api_portal_consumer",
    )
    add(
        checks,
        "api_portal_consumer:teal_opblock",
        "var(--cs-teal" in inv.swagger_css,
        "teal_vars",
        "api_portal_consumer",
    )
    add(
        checks,
        "api_portal_consumer:brand_derivative",
        (inv.monorepo / "platform/api/openapi/swagger/brand/icon.svg").is_file(),
        "brand_icon",
        "api_portal_consumer",
    )
    return checks
