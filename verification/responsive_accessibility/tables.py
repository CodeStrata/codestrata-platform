"""Accessible table checks."""

from __future__ import annotations

import re

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "table"


def check_tables(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    assessment = inv.assessment_html
    th_count = len(re.findall(r"<th\b", assessment, re.IGNORECASE))
    scope_count = len(re.findall(r"<th[^>]*\bscope=", assessment, re.IGNORECASE))
    add(
        "table:assessment_th_scope",
        th_count == 0 or th_count == scope_count,
        f"{scope_count}/{th_count}",
    )
    add(
        "table:assessment_table_wrap_tabindex",
        'tabindex="0"' in assessment and "table-wrap" in assessment,
        "focusable",
    )
    add(
        "table:assessment_renderer_semantics",
        "_ensure_table_semantics" in inv.assessment_renderer
        or 'scope="col"' in inv.assessment_renderer,
        "renderer",
    )

    eir = inv.eir_html
    eir_th = len(re.findall(r"<th\b", eir, re.IGNORECASE))
    eir_scope = len(re.findall(r"<th[^>]*\bscope=", eir, re.IGNORECASE))
    add(
        "table:eir_th_scope",
        eir_th == 0 or eir_th == eir_scope,
        f"{eir_scope}/{eir_th}",
    )
    add(
        "table:eir_wrap_tabindex",
        'tabindex="0"' in eir,
        "focusable",
    )
    add(
        "table:eir_captions",
        "<caption" in eir.lower() or eir_th == 0,
        "captions",
    )

    add(
        "table:docs_overflow",
        ".VPDoc table" in inv.docs_components_css
        and "overflow-x: auto" in inv.docs_components_css,
        "overflow_x",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("table", "table accessibility requirements not met"))
    return checks, defects
