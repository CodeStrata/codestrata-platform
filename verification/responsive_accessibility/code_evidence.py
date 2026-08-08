"""Code and evidence overflow checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "code_evidence"


def check_code_evidence(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    add(
        "code_evidence:assessment_wrap",
        "overflow-wrap: anywhere" in inv.assessment_styles,
        "anywhere",
    )
    add(
        "code_evidence:assessment_evidence_scroll",
        "overflow-x: auto" in inv.assessment_styles and "evidence" in inv.assessment_styles,
        "scroll",
    )
    add(
        "code_evidence:eir_tech_ref_wrap",
        "overflow-wrap: anywhere" in inv.eir_styles,
        "anywhere",
    )
    add(
        "code_evidence:docs_terminal_scroll",
        ".cs-terminal" in inv.docs_components_css
        and "overflow-x: auto" in inv.docs_components_css,
        "terminal",
    )
    add(
        "code_evidence:docs_table_scroll",
        ".VPDoc table" in inv.docs_components_css
        and "overflow-x: auto" in inv.docs_components_css,
        "table",
    )

    for surface, styles in (("assessment", inv.assessment_styles), ("eir", inv.eir_styles)):
        add(
            f"code_evidence:{surface}_no_break_all",
            "word-break: break-all" not in styles,
            "avoid_break_all",
        )

    if any(not c.ok for c in checks):
        defects.append(Defect("code_evidence", "code or evidence overflow handling insufficient"))
    return checks, defects
