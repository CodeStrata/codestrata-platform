"""Shadow consistency checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_shadows(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    combined = inv.docs_custom_css + inv.assessment_styles + inv.eir_styles + inv.token_css

    add(
        checks,
        "shadows:token_scale",
        "--cs-shadow" in inv.token_css,
        "cs_shadow_tokens",
        "shadows",
    )
    add(
        checks,
        "shadows:active_surfaces",
        "--cs-shadow" in combined
        or "var(--cs-shadow" in combined
        or "box-shadow" in combined,
        "shadow_in_active",
        "shadows",
    )
    add(
        checks,
        "shadows:presentation_contract",
        bool(inv.presentation_contract.get("shadow_roles")),
        "presentation_shadows",
        "shadows",
    )
    return checks
