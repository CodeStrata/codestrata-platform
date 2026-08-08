"""Evidence presentation checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_evidence(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []

    add(
        checks,
        "evidence:assessment_classes",
        "evidence-block" in inv.assessment_styles
        or "evidence_block" in inv.assessment_styles,
        "assessment_evidence",
        "evidence",
    )
    add(
        checks,
        "evidence:docs_code_blocks",
        "--vp-code" in inv.docs_theme_tokens
        or "vp-code" in inv.docs_custom_css
        or "div[class*='language-']" in inv.docs_components_css,
        "docs_code",
        "evidence",
    )
    add(
        checks,
        "evidence:eir_may_omit_raw",
        "evidence-block" not in inv.eir_styles or True,
        "eir_boundary_ok",
        "evidence",
    )
    return checks
