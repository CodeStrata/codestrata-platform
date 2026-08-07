"""Slice 13.5 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_assessment_execution import VSCODE_ASSESSMENT_EXECUTION_ID
from verification.vscode_assessment_execution.checks import check_all
from verification.vscode_assessment_execution.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV135_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.vscode_assessment_execution.models import (
    CheckResult,
    Defect,
    Verdict,
    VsCodeAssessmentExecutionReport,
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


def build_report(monorepo: Path) -> VsCodeAssessmentExecutionReport:
    contract = default_contract()
    assert contract.start_epic_14 is False

    checks, defects = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    return VsCodeAssessmentExecutionReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VSCODE_ASSESSMENT_EXECUTION_ID,
        verdict=_decide(failed, defects, limitations),
        assessment_policy_status=_status(checks, "assessment_policy"),
        command_surface_status=_status(checks, "command_surface"),
        readiness_status=_status(checks, "readiness"),
        initialization_boundary_status=_status(checks, "initialization_boundary"),
        standard_assessment_status=_status(checks, "standard_assessment"),
        ai_assessment_status=_status(checks, "ai_assessment"),
        engine_authority_status=_status(checks, "engine_authority"),
        cli_invocation_status=_status(checks, "cli_invocation"),
        consent_ordering_status=_status(checks, "consent_ordering"),
        telemetry_boundary_status=_status(checks, "telemetry_boundary"),
        analytics_boundary_status=_status(checks, "analytics_boundary"),
        process_boundary_status=_status(checks, "process_boundary"),
        cancellation_status=_status(checks, "cancellation"),
        primary_authority_status=_status(checks, "primary_authority"),
        report_postcondition_status=_status(checks, "report_postcondition"),
        source_mutation_status=_status(checks, "source_mutation"),
        config_mutation_status=_status(checks, "config_mutation"),
        git_boundary_status=_status(checks, "git_boundary"),
        network_boundary_status=_status(checks, "network_boundary"),
        privacy_status=_status(checks, "privacy"),
        vscode_regression_status=_status(checks, "vscode_regression"),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
    )


def write_report(monorepo: Path, report: VsCodeAssessmentExecutionReport) -> Path:
    out_dir = monorepo / SV135_OUTPUT_RELATIVE
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
