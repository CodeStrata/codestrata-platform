"""Community vs commercial scope checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_community_scope(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []

    add(
        checks,
        "community_scope:docs_src_exclude",
        "srcExclude" in inv.docs_config,
        "srcExclude_present",
        "community_scope",
    )
    add(
        checks,
        "community_scope:platform_not_in_nav",
        "Platform" not in inv.docs_config or "srcExclude" in inv.docs_config,
        "community_nav",
        "community_scope",
    )
    add(
        checks,
        "community_scope:vscode_not_promoting_platform",
        "Platform API" not in str(inv.vscode_package.get("description", "")),
        "vscode_scope",
        "community_scope",
    )
    add(
        checks,
        "community_scope:marketplace_community_claims",
        "Community" in str(inv.vscode_package.get("description", ""))
        or "community" in inv.marketplace_mapping.lower(),
        "marketplace_scope",
        "community_scope",
    )
    return checks
