"""Print stylesheet checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "print"


def check_print_styles(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    for surface, styles in (("assessment", inv.assessment_styles), ("eir", inv.eir_styles)):
        add(f"print:{surface}_media_block", "@media print" in styles, "present")
        add(
            f"print:{surface}_light_scheme",
            "color-scheme: light" in styles,
            "light",
        )
        add(
            f"print:{surface}_hide_chrome",
            ".skip-link" in styles
            and "display: none" in styles
            and "report-product-bar" in styles,
            "hidden",
        )
        add(
            f"print:{surface}_badge_ink",
            (".badge" in styles or ".status-badge" in styles)
            and "border:" in styles,
            "badges",
        )

    add(
        "print:eir_details_expanded",
        "details > *" in inv.eir_styles or "display: block" in inv.eir_styles,
        "details",
    )
    add(
        "print:eir_no_section_break_avoid",
        "section { break-inside: avoid" not in inv.eir_styles
        and "section {{ break-inside: avoid" not in inv.eir_styles,
        "absent",
    )
    add(
        "print:assessment_card_break_avoid",
        "break-inside: avoid" in inv.assessment_styles,
        "cards",
    )
    add(
        "print:assessment_no_section_break_avoid",
        ".section {{ break-inside: avoid" not in inv.assessment_styles,
        "absent",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("print", "print readability contract not met"))
    return checks, defects
