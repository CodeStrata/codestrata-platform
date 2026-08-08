"""Slice 14.13 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.cross_surface_visual_consistency import CROSS_SURFACE_CONSISTENCY_ID
from verification.cross_surface_visual_consistency.checks import check_all
from verification.cross_surface_visual_consistency.contract import (
    ALLOWED_LIMITATIONS,
    default_contract,
    monorepo_root_from_here,
)
from verification.cross_surface_visual_consistency.inventory import build_inventory
from verification.cross_surface_visual_consistency.models import (
    CheckResult,
    CrossSurfaceVisualConsistencyReport,
    Defect,
    Verdict,
)
from verification.cross_surface_visual_consistency.reporting import write_report


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok for c in subset) else "fail"


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def release_posture(*, complete: bool) -> dict[str, bool]:
    return {
        "assessment_schema_1_2": True,
        "design_system_remains_1_0": True,
        "extension_version_0_2_0": True,
        "no_commit": True,
        "no_deploy": True,
        "no_publish": True,
        "no_runtime_change": True,
        "no_tag": True,
        "slice_14_13_complete": complete,
        "start_epic_15": False,
    }


def build_report(monorepo: Path) -> CrossSurfaceVisualConsistencyReport:
    contract = default_contract()
    assert contract.start_epic_15 is False

    inv = build_inventory(monorepo)
    checks, defects, matrix = check_all(monorepo, inventory=inv)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    complete = failed == 0 and not defects
    posture = release_posture(complete=complete)

    return CrossSurfaceVisualConsistencyReport(
        schema_name=contract.schema_name,
        schema_version=contract.schema_version,
        verification_id=CROSS_SURFACE_CONSISTENCY_ID,
        verdict=_decide(failed, defects, limitations),
        policy_status=_status(checks, "policy"),
        contract_status=_status(checks, "contract"),
        matrix_status=_status(checks, "matrix"),
        adaptations_status=_status(checks, "adaptations"),
        identity_status=_status(checks, "identity"),
        colors_status=_status(checks, "colors"),
        typography_status=_status(checks, "typography"),
        spacing_status=_status(checks, "spacing"),
        radii_status=_status(checks, "radii"),
        borders_status=_status(checks, "borders"),
        shadows_status=_status(checks, "shadows"),
        components_status=_status(checks, "components"),
        evidence_status=_status(checks, "evidence"),
        visualization_status=_status(checks, "visualization"),
        report_shells_status=_status(checks, "report_shells"),
        navigation_status=_status(checks, "navigation"),
        naming_status=_status(checks, "naming"),
        community_scope_status=_status(checks, "community_scope"),
        docs_consumer_status=_status(checks, "docs_consumer"),
        assessment_consumer_status=_status(checks, "assessment_consumer"),
        eir_consumer_status=_status(checks, "eir_consumer"),
        vscode_consumer_status=_status(checks, "vscode_consumer"),
        marketplace_consumer_status=_status(checks, "marketplace_consumer"),
        api_portal_consumer_status=_status(checks, "api_portal_consumer"),
        deployment_output_status=_status(checks, "deployment_output"),
        dark_theme_status=_status(checks, "dark_theme"),
        print_consistency_status=_status(checks, "print_consistency"),
        responsive_regression_status=_status(checks, "responsive_regression"),
        accessibility_regression_status=_status(checks, "accessibility_regression"),
        legacy_branding_status=_status(checks, "legacy_branding"),
        browser_validation_status=_status(checks, "browser_validation"),
        epic_completion_boundary_status=_status(checks, "epic_completion_boundary"),
        determinism_status=_status(checks, "determinism"),
        consistency_matrix=matrix,
        defects=defects,
        blockers=[],
        limitations=limitations,
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
