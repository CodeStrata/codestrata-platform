"""Forced-colors (high contrast) baseline checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "forced_colors"


def check_forced_colors(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    for surface, styles in (("assessment", inv.assessment_styles), ("eir", inv.eir_styles)):
        add(
            f"forced_colors:{surface}_query",
            "forced-colors: active" in styles,
            "active",
        )
        add(
            f"forced_colors:{surface}_system_colors",
            "CanvasText" in styles or "Highlight" in styles,
            "system",
        )

    add(
        "forced_colors:docs_components",
        "forced-colors: active" in inv.docs_components_css,
        "active",
    )
    add(
        "forced_colors:docs_system_colors",
        "CanvasText" in inv.docs_components_css or "Highlight" in inv.docs_components_css,
        "system",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("forced_colors", "forced-colors baseline not declared"))
    return checks, defects
