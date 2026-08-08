"""Dark theme consistency checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_dark_theme(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    docs_dark = (
        "prefers-color-scheme: dark" in inv.docs_custom_css
        or "[data-theme=\"dark\"]" in inv.docs_custom_css
        or ".dark" in inv.docs_custom_css
    )
    add(
        checks,
        "dark_theme:docs_support",
        docs_dark or "--cs-canvas" in inv.docs_theme_tokens,
        "docs_dark",
        "dark_theme",
    )
    add(
        checks,
        "dark_theme:assessment_tokens",
        "--cs-canvas" in inv.assessment_styles,
        "assessment_tokens",
        "dark_theme",
    )
    add(
        checks,
        "dark_theme:eir_tokens",
        "--cs-canvas" in inv.eir_styles,
        "eir_tokens",
        "dark_theme",
    )
    return checks
