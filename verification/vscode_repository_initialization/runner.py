"""Slice 13.4 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_repository_initialization import (
    VSCODE_REPOSITORY_INITIALIZATION_ID,
)
from verification.vscode_repository_initialization.checks import check_all
from verification.vscode_repository_initialization.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV134_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.vscode_repository_initialization.models import (
    CheckResult,
    Defect,
    Verdict,
    VsCodeRepositoryInitializationReport,
)


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


def build_report(monorepo: Path) -> VsCodeRepositoryInitializationReport:
    contract = default_contract()
    assert contract.start_epic_14 is False

    checks, defects = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    return VsCodeRepositoryInitializationReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VSCODE_REPOSITORY_INITIALIZATION_ID,
        verdict=_decide(failed, defects, limitations),
        initialization_policy_status=_status(checks, "initialization_policy"),
        command_surface_status=_status(checks, "command_surface"),
        workspace_boundary_status=_status(checks, "workspace_boundary"),
        cli_readiness_status=_status(checks, "cli_readiness"),
        state_detection_status=_status(checks, "state_detection"),
        engine_authority_status=_status(checks, "engine_authority"),
        process_boundary_status=_status(checks, "process_boundary"),
        idempotency_status=_status(checks, "idempotency"),
        existing_configuration_status=_status(checks, "existing_configuration"),
        post_init_verification_status=_status(checks, "post_init_verification"),
        source_mutation_status=_status(checks, "source_mutation"),
        git_boundary_status=_status(checks, "git_boundary"),
        network_boundary_status=_status(checks, "network_boundary"),
        ai_boundary_status=_status(checks, "ai_boundary"),
        telemetry_boundary_status=_status(checks, "telemetry_boundary"),
        analytics_boundary_status=_status(checks, "analytics_boundary"),
        report_boundary_status=_status(checks, "report_boundary"),
        workflow_integration_status=_status(checks, "workflow_integration"),
        cancellation_status=_status(checks, "cancellation"),
        privacy_status=_status(checks, "privacy"),
        vscode_regression_status=_status(checks, "vscode_regression"),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
    )


def write_report(monorepo: Path, report: VsCodeRepositoryInitializationReport) -> Path:
    out_dir = monorepo / SV134_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Epic 14 Product Experience not started. "
        "No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    print(
        f"{SCHEMA_NAME}:{SCHEMA_VERSION} verdict={report.verdict} "
        f"checks={report.total_checks} failed={report.failed_checks}"
    )
    for check in report.checks:
        if not check.ok:
            print(f"  FAIL {check.name}: {check.detail}")
    print(f"report={path}")
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
