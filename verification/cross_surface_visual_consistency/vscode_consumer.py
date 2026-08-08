"""VS Code consumer checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_vscode_consumer(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    add(
        checks,
        "vscode_consumer:mapping_present",
        bool(inv.vscode_mapping),
        "mapping",
        "vscode_consumer",
    )
    add(
        checks,
        "vscode_consumer:native_host_exception",
        "native" in inv.vscode_mapping.lower() or "ThemeIcon" in inv.vscode_mapping,
        "native_host",
        "vscode_consumer",
    )
    add(
        checks,
        "vscode_consumer:activity_icon",
        "currentColor" in inv.vscode_activity_svg,
        "currentColor",
        "vscode_consumer",
    )
    return checks
