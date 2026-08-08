"""VS Code extension accessibility boundary checks."""

from __future__ import annotations

import re

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "vscode_boundary"
_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def check_vscode_boundary(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    vscode_blob = "\n".join(inv.vscode_sources.values())

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    add(
        "vscode_boundary:package_version",
        inv.vscode_package.get("version") == "0.2.0",
        str(inv.vscode_package.get("version")),
    )
    add(
        "vscode_boundary:no_webview_apis",
        "createWebviewPanel" not in vscode_blob and "WebviewView" not in vscode_blob,
        "absent",
    )
    # Hex literals that exactly match Design System catalog colours are token
    # references (Marketplace gallery generator metadata), not invented palette.
    catalog_hex = {
        value.lower()
        for value in inv.token_catalog.get("colors", {}).values()
        if isinstance(value, str) and value.startswith("#")
    }
    hex_hits = [
        value
        for value in _HEX.findall(vscode_blob)
        if value.lower() not in catalog_hex
    ]
    add(
        "vscode_boundary:no_hardcoded_hex",
        not hex_hits,
        "ok" if not hex_hits else f"{len(hex_hits)}",
    )
    add(
        "vscode_boundary:status_bar_a11y",
        "accessibilityInformation" in inv.vscode_status_bar,
        "declared",
    )
    add(
        "vscode_boundary:findings_tree_a11y",
        "accessibilityInformation" in inv.vscode_findings_tree,
        "declared",
    )
    add(
        "vscode_boundary:recommendations_tree_a11y",
        "accessibilityInformation" in inv.vscode_recommendations_tree,
        "declared",
    )
    add(
        "vscode_boundary:theme_icons",
        "ThemeIcon" in vscode_blob,
        "theme_icon",
    )
    icon = inv.vscode_activity_icon
    add(
        "vscode_boundary:activity_icon",
        "currentColor" in icon and "viewBox=" in icon,
        "svg",
    )
    add(
        "vscode_boundary:no_create_webview",
        "createWebviewPanel" not in vscode_blob,
        "absent",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("vscode_boundary", "VS Code extension boundary violated"))
    return checks, defects
