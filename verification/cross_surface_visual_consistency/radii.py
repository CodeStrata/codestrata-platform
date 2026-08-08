"""Radius consistency checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_radii(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    combined = (
        inv.token_css
        + inv.docs_theme_tokens
        + inv.assessment_styles
        + inv.eir_styles
        + inv.swagger_css
    )

    add(
        checks,
        "radii:token_scale",
        "--cs-radius" in inv.token_css,
        "cs_radius_tokens",
        "radii",
    )
    add(
        checks,
        "radii:active_surfaces",
        "--cs-radius" in combined,
        "radius_in_active",
        "radii",
    )
    add(
        checks,
        "radii:presentation_contract",
        bool(inv.presentation_contract.get("radius_roles")),
        "presentation_radii",
        "radii",
    )
    return checks
