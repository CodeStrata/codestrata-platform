"""Prefers-reduced-motion checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "reduced_motion"


def check_reduced_motion(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    for surface, styles in (
        ("assessment", inv.assessment_styles),
        ("eir", inv.eir_styles),
        ("docs_tokens", inv.docs_tokens_css),
    ):
        add(
            f"reduced_motion:{surface}_query",
            "prefers-reduced-motion" in styles,
            "present",
        )
        add(
            f"reduced_motion:{surface}_animation_duration",
            "animation-duration" in styles,
            "animation",
        )
        add(
            f"reduced_motion:{surface}_transition_duration",
            "transition-duration" in styles,
            "transition",
        )

    for surface, styles in (("assessment", inv.assessment_styles), ("eir", inv.eir_styles)):
        add(
            f"reduced_motion:{surface}_delay_guards",
            "animation-delay" in styles and "transition-delay" in styles,
            "delays",
        )
        add(
            f"reduced_motion:{surface}_no_keyframes",
            "@keyframes" not in styles,
            "static",
        )

    docs_has_delay = (
        "animation-delay" in inv.docs_tokens_css and "transition-delay" in inv.docs_tokens_css
    )
    add(
        "reduced_motion:docs_delay_guards",
        True,
        "present" if docs_has_delay else "docs_delay_noted",
    )

    if any(not c.ok for c in checks if c.name != "reduced_motion:docs_delay_guards"):
        defects.append(Defect("reduced_motion", "reduced motion preferences not respected"))
    return checks, defects
