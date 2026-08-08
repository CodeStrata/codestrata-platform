"""Typography consistency checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add, scan_forbidden
from verification.cross_surface_visual_consistency.contract import FORBIDDEN_ACTIVE_IDENTITY
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_typography(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    mappings = inv.consumer_mappings.get("typography") or inv.consumer_mappings

    add(
        checks,
        "typography:consumer_mappings_present",
        bool(inv.consumer_mappings),
        "mappings_loaded",
        "typography",
    )
    add(
        checks,
        "typography:delivery_modes",
        "documentation" in str(mappings) or "docs" in str(mappings),
        "docs_mode",
        "typography",
    )

    active = (
        inv.docs_theme_tokens
        + inv.docs_custom_css
        + inv.token_css
        + inv.assessment_styles
        + inv.eir_styles
        + inv.swagger_css
        + str(inv.presentation_contract)
    )
    georgia_hits = scan_forbidden(active, ("Georgia",))
    add(
        checks,
        "typography:no_georgia_active",
        not georgia_hits,
        "clean" if not georgia_hits else "georgia_found",
        "typography",
    )
    add(
        checks,
        "typography:inter_or_system_stacks",
        "Inter" in active
        or "system-ui" in active
        or "sans-serif" in active
        or "font_body" in active
        or "font-body" in active,
        "body_stack",
        "typography",
    )
    return checks
