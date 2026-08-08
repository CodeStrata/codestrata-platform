"""Visualization / severity marker checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_visualization(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []

    add(
        checks,
        "visualization:assessment_severity_markers",
        "severity-marker" in inv.assessment_styles
        or "status-badge" in inv.assessment_styles,
        "assessment_markers",
        "visualization",
    )
    add(
        checks,
        "visualization:eir_severity_markers",
        "severity-marker" in inv.eir_styles or "status-badge" in inv.eir_styles,
        "eir_markers",
        "visualization",
    )
    add(
        checks,
        "visualization:not_color_only_assessment",
        "aria-label" in inv.assessment_renderer
        or "visually-hidden" in inv.assessment_styles,
        "assessment_a11y_text",
        "visualization",
    )
    add(
        checks,
        "visualization:not_color_only_eir",
        "aria-label" in inv.eir_renderer or "visually-hidden" in inv.eir_styles,
        "eir_a11y_text",
        "visualization",
    )
    return checks
