"""Slice 13.6 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_assessment_progress import VSCODE_ASSESSMENT_PROGRESS_ID
from verification.vscode_assessment_progress.checks import check_all
from verification.vscode_assessment_progress.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV136_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.vscode_assessment_progress.models import (
    CheckResult,
    Defect,
    Verdict,
    VsCodeAssessmentProgressReport,
)
from verification.vscode_assessment_progress.scenarios import PHASE_INVENTORY


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


def build_report(monorepo: Path) -> VsCodeAssessmentProgressReport:
    contract = default_contract()
    assert contract.start_epic_14 is False

    checks, defects = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    return VsCodeAssessmentProgressReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VSCODE_ASSESSMENT_PROGRESS_ID,
        verdict=_decide(failed, defects, limitations),
        progress_policy_status=_status(checks, "progress_policy"),
        lifecycle_status=_status(checks, "lifecycle"),
        phase_inventory=list(PHASE_INVENTORY),
        indeterminate_progress_status=_status(checks, "indeterminate_progress"),
        engine_signal_status=_status(checks, "engine_signal"),
        standard_assessment_status=_status(checks, "standard_assessment"),
        ai_assessment_status=_status(checks, "ai_assessment"),
        cancellation_status=_status(checks, "cancellation"),
        race_condition_status=_status(checks, "race_condition"),
        primary_authority_status=_status(checks, "primary_authority"),
        telemetry_boundary_status=_status(checks, "telemetry_boundary"),
        analytics_boundary_status=_status(checks, "analytics_boundary"),
        output_boundary_status=_status(checks, "output_boundary"),
        notification_boundary_status=_status(checks, "notification_boundary"),
        report_phase_status=_status(checks, "report_phase"),
        workflow_integration_status=_status(checks, "workflow_integration"),
        privacy_status=_status(checks, "privacy"),
        vscode_regression_status=_status(checks, "vscode_regression"),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
    )


def write_report(monorepo: Path, report: VsCodeAssessmentProgressReport) -> Path:
    out_dir = monorepo / SV136_OUTPUT_RELATIVE
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
