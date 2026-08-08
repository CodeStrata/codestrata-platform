"""Touch target size checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "touch_target"


def check_touch_targets(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    custom = inv.docs_custom_css

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    add(
        "touch_target:docs_home_base_34",
        "min-height: 34px" in custom and "cs-docs-home" in custom,
        "34px",
    )
    add(
        "touch_target:docs_home_mobile_44",
        "720px" in custom and "min-height: 44px" in custom,
        "44px",
    )
    add(
        "touch_target:docs_btn_padding",
        ".btn" in custom and "padding" in custom,
        "padding",
    )

    report_styles = inv.assessment_styles + inv.eir_styles
    add(
        "touch_target:skip_link_padding",
        ".skip-link" in report_styles and "padding:" in report_styles,
        "skip_link",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("touch_target", "minimum touch target sizes not met"))
    return checks, defects
