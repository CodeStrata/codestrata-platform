"""Brand asset accessibility checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "brand_asset"


def check_brand_assets(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    for surface, html in (("assessment", inv.assessment_html), ("eir", inv.eir_html)):
        add(
            f"brand_asset:{surface}_mark_aria_hidden",
            "cs-mark" in html and 'aria-hidden="true"' in html,
            "hidden",
        )
        add(
            f"brand_asset:{surface}_mark_not_focusable",
            'focusable="false"' in html,
            "non_focusable",
        )

    icon = inv.vscode_activity_icon
    add(
        "brand_asset:activity_icon_current_color",
        "currentColor" in icon,
        "currentColor",
    )
    add(
        "brand_asset:activity_icon_viewbox",
        'viewBox="0 0 22 22"' in icon or "viewBox=" in icon,
        "viewbox",
    )
    add(
        "brand_asset:docs_home_svg_hidden",
        'aria-hidden="true"' in inv.docs_home_link,
        "hidden",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("brand_asset", "brand asset accessibility contract not met"))
    return checks, defects
