"""Assessment report responsive checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "assessment_responsive"


def check_assessment_responsive(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    styles = inv.assessment_styles
    html = inv.assessment_html

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    add("assessment_responsive:toc_static_1024", "max-width: 1024px" in styles, "1024")
    add("assessment_responsive:toc_sticky_1040", "min-width: 1040px" in styles, "1040")
    add("assessment_responsive:severity_grid_820", "820px" in styles, "820")
    add("assessment_responsive:cards_560", "560px" in styles, "560")

    add(
        "assessment_responsive:html_skip",
        'href="#main-content"' in html,
        "skip",
    )
    add("assessment_responsive:html_single_h1", html.lower().count("<h1") == 1, "h1")
    add(
        "assessment_responsive:html_main",
        "<main" in html.lower() or 'role="main"' in html,
        "main",
    )
    add(
        "assessment_responsive:html_table_wrap",
        'tabindex="0"' in html and "table-wrap" in html,
        "table",
    )
    add(
        "assessment_responsive:html_forced_colors",
        "forced-colors: active" in styles,
        "forced_colors",
    )
    add(
        "assessment_responsive:html_reduced_motion",
        "prefers-reduced-motion" in styles,
        "motion",
    )
    add(
        "assessment_responsive:html_print",
        "@media print" in styles,
        "print",
    )
    add(
        "assessment_responsive:partial_main_target",
        'id="main-content"' in inv.assessment_partial_html,
        "partial",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("assessment_responsive", "assessment responsive contract not met"))
    return checks, defects
