"""Visible focus indicator checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "focus"


def check_focus(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    for surface, styles in (("assessment", inv.assessment_styles), ("eir", inv.eir_styles)):
        add(
            f"focus:{surface}_focus_token",
            ":focus-visible" in styles and "var(--focus)" in styles,
            "focus_token",
        )
        add(
            f"focus:{surface}_forced_colors_highlight",
            "forced-colors: active" in styles and "Highlight" in styles,
            "highlight",
        )
        bare_none = "outline: none" in styles or "outline:none" in styles
        add(
            f"focus:{surface}_outline_restored",
            not bare_none or ":focus-visible" in styles,
            "restored" if ":focus-visible" in styles else "unguarded_none",
        )

    add(
        "focus:docs_tokens_focus_visible",
        ":focus-visible" in inv.docs_tokens_css and "var(--cs-focus)" in inv.docs_tokens_css,
        "docs_focus",
    )
    docs_outline_none = "outline: none" in inv.docs_css or "outline:none" in inv.docs_css
    add(
        "focus:docs_outline_restored",
        not docs_outline_none or ":focus-visible" in inv.docs_css,
        "restored",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("focus", "visible focus contract not satisfied"))
    return checks, defects
