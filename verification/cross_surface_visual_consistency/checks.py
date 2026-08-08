"""Orchestrator for Slice 14.13 checks."""

from __future__ import annotations

from pathlib import Path

from verification.cross_surface_visual_consistency.accessibility_regression import (
    check_accessibility_regression,
)
from verification.cross_surface_visual_consistency.adaptations import check_adaptations
from verification.cross_surface_visual_consistency.api_portal_consumer import (
    check_api_portal_consumer,
)
from verification.cross_surface_visual_consistency.assessment_consumer import (
    check_assessment_consumer,
)
from verification.cross_surface_visual_consistency.browser_validation import (
    check_browser_validation,
)
from verification.cross_surface_visual_consistency.borders import check_borders
from verification.cross_surface_visual_consistency.colors import check_colors
from verification.cross_surface_visual_consistency.community_scope import check_community_scope
from verification.cross_surface_visual_consistency.components import check_components
from verification.cross_surface_visual_consistency.contract_checks import check_contract
from verification.cross_surface_visual_consistency.dark_theme import check_dark_theme
from verification.cross_surface_visual_consistency.deployment_output import check_deployment_output
from verification.cross_surface_visual_consistency.determinism import check_determinism
from verification.cross_surface_visual_consistency.docs_consumer import check_docs_consumer
from verification.cross_surface_visual_consistency.eir_consumer import check_eir_consumer
from verification.cross_surface_visual_consistency.epic_completion_boundary import (
    check_epic_completion_boundary,
)
from verification.cross_surface_visual_consistency.evidence import check_evidence
from verification.cross_surface_visual_consistency.identity import check_identity
from verification.cross_surface_visual_consistency.inventory import (
    ConsistencyInventory,
    build_inventory,
)
from verification.cross_surface_visual_consistency.legacy_branding import check_legacy_branding
from verification.cross_surface_visual_consistency.marketplace_consumer import (
    check_marketplace_consumer,
)
from verification.cross_surface_visual_consistency.matrix import check_matrix
from verification.cross_surface_visual_consistency.models import (
    CheckResult,
    ConsistencyMatrixCell,
    Defect,
)
from verification.cross_surface_visual_consistency.naming import check_naming
from verification.cross_surface_visual_consistency.navigation import check_navigation
from verification.cross_surface_visual_consistency.policy import check_policy
from verification.cross_surface_visual_consistency.print_consistency import check_print_consistency
from verification.cross_surface_visual_consistency.radii import check_radii
from verification.cross_surface_visual_consistency.report_shells import check_report_shells
from verification.cross_surface_visual_consistency.responsive_regression import (
    check_responsive_regression,
)
from verification.cross_surface_visual_consistency.scenarios import check_scenarios
from verification.cross_surface_visual_consistency.shadows import check_shadows
from verification.cross_surface_visual_consistency.spacing import check_spacing
from verification.cross_surface_visual_consistency.typography import check_typography
from verification.cross_surface_visual_consistency.visualization import check_visualization
from verification.cross_surface_visual_consistency.vscode_consumer import check_vscode_consumer


def check_all(
    monorepo: Path,
    *,
    inventory: ConsistencyInventory | None = None,
) -> tuple[list[CheckResult], list[Defect], list[ConsistencyMatrixCell]]:
    inv = inventory or build_inventory(monorepo)
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    checks.extend(check_policy(inv))
    checks.extend(check_contract(inv))
    matrix_checks, matrix, matrix_defects = check_matrix(inv)
    checks.extend(matrix_checks)
    defects.extend(matrix_defects)
    checks.extend(check_adaptations(inv))
    checks.extend(check_identity(inv))
    checks.extend(check_colors(inv))
    checks.extend(check_typography(inv))
    checks.extend(check_spacing(inv))
    checks.extend(check_radii(inv))
    checks.extend(check_borders(inv))
    checks.extend(check_shadows(inv))
    checks.extend(check_components(inv))
    checks.extend(check_evidence(inv))
    checks.extend(check_visualization(inv))
    checks.extend(check_report_shells(inv))
    checks.extend(check_navigation(inv))
    checks.extend(check_naming(inv))
    checks.extend(check_community_scope(inv))
    checks.extend(check_docs_consumer(inv))
    checks.extend(check_assessment_consumer(inv))
    checks.extend(check_eir_consumer(inv))
    checks.extend(check_vscode_consumer(inv))
    checks.extend(check_marketplace_consumer(inv))
    checks.extend(check_api_portal_consumer(inv))
    deploy_checks, deploy_defects = check_deployment_output(inv)
    checks.extend(deploy_checks)
    defects.extend(deploy_defects)
    checks.extend(check_dark_theme(inv))
    checks.extend(check_print_consistency(inv))
    checks.extend(check_responsive_regression(inv))
    checks.extend(check_accessibility_regression(inv))
    legacy_checks, legacy_defects = check_legacy_branding(inv)
    checks.extend(legacy_checks)
    defects.extend(legacy_defects)
    browser_checks, browser_defects = check_browser_validation(inv)
    checks.extend(browser_checks)
    defects.extend(browser_defects)
    boundary_checks, boundary_defects = check_epic_completion_boundary(inv)
    checks.extend(boundary_checks)
    defects.extend(boundary_defects)
    checks.extend(check_scenarios(inv))
    checks.extend(check_determinism(inv))

    return checks, defects, matrix
