"""Deployment built-output checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add, scan_hex
from verification.cross_surface_visual_consistency.contract import LEGACY_AMBER_HEX
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult, Defect


def check_deployment_output(
    inv: ConsistencyInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    add(
        checks,
        "deployment_output:dist_exists",
        inv.dist_exists,
        "present" if inv.dist_exists else "missing_run_build",
        "deployment_output",
    )
    if inv.dist_tokens:
        add(
            checks,
            "deployment_output:dist_tokens_no_amber",
            not scan_hex(inv.dist_tokens, LEGACY_AMBER_HEX),
            "clean",
            "deployment_output",
        )
    add(
        checks,
        "deployment_output:favicon_present",
        any("favicon" in f for f in inv.dist_files),
        "favicon",
        "deployment_output",
    )
    add(
        checks,
        "deployment_output:brand_present",
        any("brand/" in f for f in inv.dist_files),
        "brand_assets",
        "deployment_output",
    )
    platform_routes = [f for f in inv.dist_files if "platform/" in f.lower()]
    add(
        checks,
        "deployment_output:no_platform_routes",
        not platform_routes,
        "clean" if not platform_routes else f"{len(platform_routes)}_hits",
        "deployment_output",
    )
    if platform_routes:
        defects.append(Defect("deployment_output", "platform routes in dist"))
    return checks, defects
