"""Product naming consistency checks for Slice 14.13."""

from __future__ import annotations

import json

from verification.cross_surface_visual_consistency._helpers import add, scan_forbidden
from verification.cross_surface_visual_consistency.contract import FORBIDDEN_ACTIVE_IDENTITY
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_naming(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    pkg = inv.vscode_package
    display = pkg.get("displayName", "")

    add(
        checks,
        "naming:codestrata_capitalization",
        display.startswith("CodeStrata"),
        display or "missing",
        "naming",
    )
    add(
        checks,
        "naming:marketplace_display_name",
        "Engineering Intelligence" in display,
        display,
        "naming",
    )
    active_pkg = json.dumps(
        {
            "displayName": pkg.get("displayName"),
            "description": pkg.get("description"),
            "name": pkg.get("name"),
        }
    )
    forbidden = scan_forbidden(active_pkg, ("AIMF", "Codestrata"))
    add(
        checks,
        "naming:no_forbidden_identity",
        not forbidden,
        "clean" if not forbidden else ",".join(forbidden),
        "naming",
    )
    add(
        checks,
        "naming:policy_authoritative_name",
        inv.policy.get("authoritative_product_name") == "CodeStrata",
        "CodeStrata",
        "naming",
    )
    return checks
