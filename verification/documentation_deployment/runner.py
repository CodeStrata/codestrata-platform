"""Slice 14.12 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.documentation_deployment import DOCUMENTATION_DEPLOYMENT_ID
from verification.documentation_deployment.checks import check_all
from verification.documentation_deployment.contract import (
    ALLOWED_LIMITATIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.documentation_deployment.determinism import check_determinism
from verification.documentation_deployment.models import (
    CheckResult,
    Defect,
    DocumentationDeploymentReport,
    Verdict,
)
from verification.documentation_deployment.reporting import write_report

CONDITIONAL_LIMITATIONS = frozenset({"dry_run_requires_node_22", "npm_audit_unavailable"})
BASELINE_LIMITATIONS = tuple(
    limitation
    for limitation in ALLOWED_LIMITATIONS
    if limitation not in CONDITIONAL_LIMITATIONS
)


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [check for check in checks if check.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(check.ok for check in subset) else "fail"


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
        "no_production_deploy": True,
        "no_publish": True,
        "no_runtime_change": True,
        "no_tag": True,
        "slice_14_12_complete": complete,
        "start_slice_15_7": False,
    }


def build_report(monorepo: Path) -> DocumentationDeploymentReport:
    contract = default_contract()
    assert contract.start_slice_15_7 is False
    assert contract.no_production_deploy is True

    checks, defects, extra_limitations, _inv = check_all(monorepo)
    limitations = sorted(set(BASELINE_LIMITATIONS) | set(extra_limitations))
    failed = sum(1 for check in checks if not check.ok)
    complete = failed == 0 and not defects
    posture = release_posture(complete=complete)

    report = DocumentationDeploymentReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=DOCUMENTATION_DEPLOYMENT_ID,
        verdict=_decide(failed, defects, limitations),
        policy_status=_status(checks, "policy"),
        inventory_status=_status(checks, "inventory"),
        package_root_status=_status(checks, "package_root"),
        vitepress_status=_status(checks, "vitepress"),
        build_output_status=_status(checks, "build_output"),
        wrangler_status=_status(checks, "wrangler"),
        output_alignment_status=_status(checks, "output_alignment"),
        preflight_status=_status(checks, "preflight"),
        build_ownership_status=_status(checks, "build_ownership"),
        non_interactive_status=_status(checks, "non_interactive"),
        mutation_boundary_status=_status(checks, "mutation_boundary"),
        generated_scope_status=_status(checks, "generated_scope"),
        assets_status=_status(checks, "assets"),
        community_export_status=_status(checks, "community_export"),
        dependencies_status=_status(checks, "dependencies"),
        node_runtime_status=_status(checks, "node_runtime"),
        security_status=_status(checks, "security"),
        wrangler_telemetry_status=_status(checks, "wrangler_telemetry"),
        cloudflare_settings_status=_status(checks, "cloudflare_settings"),
        clean_ci_status=_status(checks, "clean_ci"),
        dry_run_status=_status(checks, "dry_run"),
        accessibility_regression_status=_status(checks, "accessibility_regression"),
        consistency_boundary_status=_status(checks, "consistency_boundary"),
        determinism_status="not_executed",
        scenarios_status=_status(checks, "scenarios"),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
        release_posture=posture,
    )

    det_checks = check_determinism(report)
    report.checks.extend(det_checks)
    report.total_checks = len(report.checks)
    report.failed_checks = sum(1 for check in report.checks if not check.ok)
    report.determinism_status = _status(report.checks, "determinism")
    report.verdict = _decide(report.failed_checks, defects, limitations)
    report.release_posture = release_posture(complete=report.failed_checks == 0 and not defects)
    return report


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
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
