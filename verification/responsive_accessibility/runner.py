"""Slice 14.11 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.responsive_accessibility import RESPONSIVE_ACCESSIBILITY_ID
from verification.responsive_accessibility.browser_validation import (
    run_browser_validation,
    write_browser_artifact,
)
from verification.responsive_accessibility.checks import check_all
from verification.responsive_accessibility.contract import (
    ALLOWED_LIMITATIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.responsive_accessibility.inventory import build_inventory
from verification.responsive_accessibility.models import (
    CheckResult,
    Defect,
    ResponsiveAccessibilityReport,
    Verdict,
)
from verification.responsive_accessibility.reporting import write_report


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [check for check in checks if check.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(check.ok for check in subset) else "fail"


def _combined_status(checks: list[CheckResult], *categories: str) -> str:
    statuses = [_status(checks, category) for category in categories]
    if any(status == "fail" for status in statuses):
        return "fail"
    if all(status == "not_executed" for status in statuses):
        return "not_executed"
    return "pass"


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def release_posture(*, complete: bool) -> dict[str, bool]:
    return {
        "assessment_schema_1_2": True,
        "brand_assets_remain_1_0": True,
        "design_system_remains_1_0": True,
        "extension_version_0_2_0": True,
        "no_commit": True,
        "no_deploy": True,
        "no_publish": True,
        "no_runtime_change": True,
        "no_tag": True,
        "report_ia_remains_1_0": True,
        "slice_14_11_complete": complete,
        "start_epic_15": False,
        "visualization_remains_1_0": True,
        "wcag_certification_claimed": False,
    }


def build_report(monorepo: Path) -> ResponsiveAccessibilityReport:
    contract = default_contract()
    assert contract.start_epic_15 is False
    assert contract.wcag_certification_claimed is False
    assert contract.no_schema_change is True

    inventory = build_inventory(monorepo)
    browser_checks, browser_defects, viewports, artifact = run_browser_validation(
        monorepo, inventory
    )
    write_browser_artifact(monorepo, artifact)

    checks, defects, measurements, viewport_matrix, _inv = check_all(
        monorepo,
        browser_checks=browser_checks,
        browser_viewports=viewports,
        inventory=inventory,
    )
    defects.extend(browser_defects)

    limitations = list(ALLOWED_LIMITATIONS)
    failed = sum(1 for check in checks if not check.ok)
    complete = failed == 0 and not defects
    posture = release_posture(complete=complete)

    return ResponsiveAccessibilityReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=RESPONSIVE_ACCESSIBILITY_ID,
        verdict=_decide(failed, defects, limitations),
        accessibility_policy_status=_combined_status(
            checks, "accessibility_policy", "design_system_contract", "inventory"
        ),
        contrast_status=_status(checks, "contrast"),
        typography_status=_status(checks, "typography"),
        zoom_status=_status(checks, "zoom"),
        keyboard_status=_status(checks, "keyboard"),
        focus_status=_status(checks, "focus"),
        heading_status=_status(checks, "heading"),
        landmark_status=_status(checks, "landmark"),
        skip_link_status=_status(checks, "skip_link"),
        table_status=_status(checks, "table"),
        link_status=_status(checks, "link"),
        image_alt_status=_status(checks, "image_alt"),
        brand_asset_status=_status(checks, "brand_asset"),
        status_visualization_status=_status(checks, "status_visualization"),
        code_evidence_status=_status(checks, "code_evidence"),
        responsive_viewport_status=_status(checks, "responsive_viewport"),
        documentation_responsive_status=_status(checks, "documentation_responsive"),
        assessment_responsive_status=_status(checks, "assessment_responsive"),
        eir_responsive_status=_status(checks, "eir_responsive"),
        vscode_boundary_status=_status(checks, "vscode_boundary"),
        marketplace_status=_status(checks, "marketplace"),
        touch_target_status=_status(checks, "touch_target"),
        reduced_motion_status=_status(checks, "reduced_motion"),
        forced_colors_status=_status(checks, "forced_colors"),
        dark_theme_status=_status(checks, "dark_theme"),
        print_status=_status(checks, "print"),
        html_language_status=_status(checks, "html_language"),
        aria_status=_status(checks, "aria"),
        browser_validation_status=_status(checks, "browser_validation"),
        screen_reader_boundary_status=_status(checks, "screen_reader_boundary"),
        deployment_boundary_status=_status(checks, "deployment_boundary"),
        consistency_boundary_status=_status(checks, "consistency_boundary"),
        determinism_status=_status(checks, "determinism"),
        wcag_posture={
            "target": "2.2_AA_oriented",
            "certified": False,
            "pass_means": (
                "product meets the defined automated/structural accessibility contract"
            ),
            "certification_claim_prohibited": True,
        },
        contrast_measurements=measurements,
        viewport_matrix=viewport_matrix,
        defects=defects,
        blockers=[],
        limitations=sorted(set(limitations)),
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
        release_posture=posture,
    )


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    print(
        json.dumps(
            {
                "verdict": report.verdict,
                "report": path.name,
                "failed": report.failed_checks,
                "total": report.total_checks,
            },
            sort_keys=True,
        )
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
