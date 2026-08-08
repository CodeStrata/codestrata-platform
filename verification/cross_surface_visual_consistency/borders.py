"""Border consistency checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_borders(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    combined = inv.assessment_styles + inv.eir_styles + inv.docs_custom_css

    add(
        checks,
        "borders:token_scale",
        "--cs-border" in inv.token_css,
        "cs_border_tokens",
        "borders",
    )
    add(
        checks,
        "borders:active_surfaces",
        "--cs-border" in combined or "var(--cs-border" in combined,
        "border_in_active",
        "borders",
    )
    add(
        checks,
        "borders:presentation_contract",
        bool(inv.presentation_contract.get("border_roles")),
        "presentation_borders",
        "borders",
    )
    return checks
