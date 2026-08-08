"""Link text and external link safety checks."""

from __future__ import annotations

import re

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "link"
_EMPTY_ANCHOR = re.compile(r"<a\s*>\s*</a>", re.IGNORECASE)
_CLICK_HERE = re.compile(r">\s*click here\s*<", re.IGNORECASE)


def check_links(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    for surface, html in (("assessment", inv.assessment_html), ("eir", inv.eir_html)):
        add(
            f"link:{surface}_no_click_here",
            _CLICK_HERE.search(html) is None,
            "descriptive",
        )
        empty = _EMPTY_ANCHOR.findall(html)
        add(
            f"link:{surface}_no_empty_anchors",
            not empty,
            "ok" if not empty else f"{len(empty)}",
        )

    add(
        "link:docs_home_noopener",
        "noopener" in inv.docs_home_link,
        "external_safe",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("link", "link text or rel contract violated"))
    return checks, defects
