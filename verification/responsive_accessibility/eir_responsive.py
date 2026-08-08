"""Engineering Intelligence Report responsive checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "eir_responsive"


def check_eir_responsive(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    styles = inv.eir_styles
    html = inv.eir_html

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    for width in ("1024px", "820px", "560px"):
        add(f"eir_responsive:max_{width}", f"max-width: {width}" in styles, width)
    add("eir_responsive:sticky_1040", "min-width: 1040px" in styles, "1040")
    add(
        "eir_responsive:cover_section",
        'class="cover"' in html.lower() or "section.cover" in styles,
        "cover",
    )
    add(
        "eir_responsive:summary_kpis_collapse",
        "summary-kpis" in styles and "820px" in styles,
        "collapses",
    )

    add("eir_responsive:html_skip", 'href="#main"' in html, "skip")
    add("eir_responsive:html_single_h1", html.lower().count("<h1") == 1, "h1")
    add("eir_responsive:html_main", "<main" in html.lower(), "main")
    add(
        "eir_responsive:html_table_wrap",
        'tabindex="0"' in html,
        "table",
    )
    add("eir_responsive:html_forced_colors", "forced-colors: active" in styles, "forced")
    add("eir_responsive:html_reduced_motion", "prefers-reduced-motion" in styles, "motion")
    add("eir_responsive:html_print", "@media print" in styles, "print")
    add(
        "eir_responsive:empty_skip_target",
        'id="main"' in inv.eir_empty_html,
        "empty",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("eir_responsive", "EIR responsive contract not met"))
    return checks, defects
