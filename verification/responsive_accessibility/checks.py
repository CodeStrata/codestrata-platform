"""Orchestrator for Slice 14.11 check modules."""

from __future__ import annotations

from pathlib import Path

from verification.responsive_accessibility.aria import check_aria
from verification.responsive_accessibility.assessment_responsive import (
    check_assessment_responsive,
)
from verification.responsive_accessibility.brand_assets import check_brand_assets
from verification.responsive_accessibility.code_evidence import check_code_evidence
from verification.responsive_accessibility.consistency_boundary import (
    check_consistency_boundary,
)
from verification.responsive_accessibility.contrast import check_contrast
from verification.responsive_accessibility.dark_theme import check_dark_theme
from verification.responsive_accessibility.deployment_boundary import (
    check_deployment_boundary,
)
from verification.responsive_accessibility.determinism import check_determinism
from verification.responsive_accessibility.docs_responsive import check_docs_responsive
from verification.responsive_accessibility.eir_responsive import check_eir_responsive
from verification.responsive_accessibility.focus import check_focus
from verification.responsive_accessibility.forced_colors import check_forced_colors
from verification.responsive_accessibility.headings import check_headings
from verification.responsive_accessibility.html_language import check_html_language
from verification.responsive_accessibility.images import check_images
from verification.responsive_accessibility.inventory import (
    SurfaceInventory,
    build_inventory,
    check_inventory,
    token_colors,
)
from verification.responsive_accessibility.keyboard import check_keyboard
from verification.responsive_accessibility.landmarks import check_landmarks
from verification.responsive_accessibility.links import check_links
from verification.responsive_accessibility.marketplace import check_marketplace
from verification.responsive_accessibility.policy import (
    check_design_system_contract,
    check_policy,
)
from verification.responsive_accessibility.print_styles import check_print_styles
from verification.responsive_accessibility.reduced_motion import check_reduced_motion
from verification.responsive_accessibility.scenarios import run_negative_scenarios
from verification.responsive_accessibility.screen_reader_boundary import (
    check_screen_reader_boundary,
)
from verification.responsive_accessibility.skip_links import check_skip_links
from verification.responsive_accessibility.status_visualization import (
    check_status_visualization,
)
from verification.responsive_accessibility.tables import check_tables
from verification.responsive_accessibility.touch_targets import check_touch_targets
from verification.responsive_accessibility.typography import check_typography
from verification.responsive_accessibility.viewport_matrix import check_viewport_matrix
from verification.responsive_accessibility.vscode_boundary import check_vscode_boundary
from verification.responsive_accessibility.zoom import check_zoom
from verification.responsive_accessibility.models import (
    CheckResult,
    ContrastMeasurement,
    Defect,
    ViewportOutcome,
)


def _extend(
    checks: list[CheckResult],
    defects: list[Defect],
    result: tuple[list[CheckResult], list[Defect]] | list[CheckResult],
) -> None:
    if isinstance(result, tuple):
        checks.extend(result[0])
        defects.extend(result[1])
    else:
        checks.extend(result)


def check_all(
    monorepo: Path,
    *,
    browser_checks: list[CheckResult] | None = None,
    browser_viewports: list[ViewportOutcome] | None = None,
    inventory: SurfaceInventory | None = None,
) -> tuple[
    list[CheckResult],
    list[Defect],
    list[ContrastMeasurement],
    list[ViewportOutcome],
    SurfaceInventory,
]:
    """Run every Slice 14.11 check in the declared test order."""

    inv = inventory or build_inventory(monorepo)
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    # 1–2. Policy + design-system contracts
    _extend(checks, defects, check_policy(inv))
    _extend(checks, defects, check_design_system_contract(inv))
    checks.extend(check_inventory(inv))

    # 3. Contrast
    colors = token_colors(inv)
    contrast_checks, contrast_defects, measurements = check_contrast(
        inv.accessibility_contract, colors
    )
    checks.extend(contrast_checks)
    defects.extend(contrast_defects)

    # 4–20. Structural / surface checks
    for fn in (
        check_typography,
        check_zoom,
        check_keyboard,
        check_focus,
        check_headings,
        check_landmarks,
        check_skip_links,
        check_tables,
        check_links,
        check_images,
        check_brand_assets,
        check_status_visualization,
        check_code_evidence,
        check_viewport_matrix,
        check_docs_responsive,
        check_assessment_responsive,
        check_eir_responsive,
        check_vscode_boundary,
        check_marketplace,
        check_touch_targets,
        check_reduced_motion,
        check_forced_colors,
        check_dark_theme,
        check_print_styles,
        check_html_language,
        check_aria,
        check_screen_reader_boundary,
        check_deployment_boundary,
        check_consistency_boundary,
        check_determinism,
    ):
        _extend(checks, defects, fn(inv))

    # Negative scenarios A–Z
    checks.extend(run_negative_scenarios(inv))

    # Browser validation (optional; injected by the runner when available)
    if browser_checks:
        checks.extend(browser_checks)
    viewports = list(browser_viewports or [])

    return checks, defects, measurements, viewports, inv
