"""Viewport matrix and breakpoint contract checks."""

from __future__ import annotations

from verification.responsive_accessibility.contract import VIEWPORT_MATRIX_PX
from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "responsive_viewport"


def check_viewport_matrix(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    matrix = tuple(inv.responsive_contract.get("viewport_matrix_px", ()))
    add(
        "responsive_viewport:contract_matrix",
        matrix == VIEWPORT_MATRIX_PX,
        ",".join(str(w) for w in matrix) if matrix else "missing",
    )

    max_widths = ("1024px", "820px", "560px")
    for surface, styles in (("assessment", inv.assessment_styles), ("eir", inv.eir_styles)):
        for width in max_widths:
            add(
                f"responsive_viewport:{surface}_max_{width}",
                f"max-width: {width}" in styles,
                width,
            )
        add(
            f"responsive_viewport:{surface}_sticky_toc",
            "min-width: 1040px" in styles,
            "1040",
        )

    add(
        "responsive_viewport:docs_720",
        "720px" in inv.docs_custom_css,
        "720",
    )
    add(
        "responsive_viewport:docs_960",
        "960px" in inv.docs_custom_css,
        "960",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("responsive_viewport", "responsive viewport contract not satisfied"))
    return checks, defects
