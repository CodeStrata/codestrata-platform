"""Text zoom and viewport scaling checks."""

from __future__ import annotations

import re

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "zoom"


def check_zoom(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    forbidden = ("user-scalable=no", "maximum-scale=1")
    combined_css = inv.assessment_styles + inv.eir_styles + inv.docs_css
    add(
        "zoom:no_scale_lock",
        not any(token in combined_css for token in forbidden),
        "unrestricted",
    )

    for surface, html in (("assessment", inv.assessment_html), ("eir", inv.eir_html)):
        add(
            f"zoom:{surface}_viewport_meta",
            "width=device-width" in html,
            "device_width",
        )

    for surface, styles in (("assessment", inv.assessment_styles), ("eir", inv.eir_styles)):
        add(
            f"zoom:{surface}_no_root_16px",
            not re.search(r"html\s*\{[^}]*font-size:\s*16px", styles, re.IGNORECASE | re.DOTALL),
            "relative_root",
        )
        add(
            f"zoom:{surface}_clamp_titles",
            "clamp(" in styles,
            "clamp_present",
        )

    if any(not c.ok for c in checks):
        defects.append(Defect("zoom", "text zoom or viewport scaling constraints violated"))
    return checks, defects
