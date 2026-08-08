"""Adaptation registry checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_adaptations(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    adaptations = inv.consistency_contract.get("adaptations") or []
    ids = {a.get("id") for a in adaptations}

    required = {
        "vscode_native_host",
        "offline_report_fonts",
        "offline_report_fonts_eir",
        "print_report_overrides",
        "print_report_overrides_eir",
        "marketplace_raster",
        "api_portal_framework_shell",
        "docs_vitepress_remap",
    }
    missing = sorted(required - ids)

    add(
        checks,
        "adaptations:registry_complete",
        not missing,
        "complete" if not missing else ",".join(missing),
        "adaptations",
    )
    add(
        checks,
        "adaptations:each_has_kind",
        all(a.get("kind") and a.get("surface") for a in adaptations),
        f"{len(adaptations)}_entries",
        "adaptations",
    )
    return checks
