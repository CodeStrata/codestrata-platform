"""Slice 13.11 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_cli_compatibility import VSCODE_CLI_COMPATIBILITY_ID
from verification.vscode_cli_compatibility.checks import check_all
from verification.vscode_cli_compatibility.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1311_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.vscode_cli_compatibility.models import (
    CheckResult,
    Defect,
    Verdict,
    VsCodeCliCompatibilityReport,
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


def build_report(monorepo: Path) -> VsCodeCliCompatibilityReport:
    contract = default_contract()
    assert contract.start_epic_14 is False

    checks, defects = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    return VsCodeCliCompatibilityReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VSCODE_CLI_COMPATIBILITY_ID,
        verdict=_decide(failed, defects, limitations),
        compatibility_policy_status=_status(checks, "compatibility_policy"),
        matrix_status=_status(checks, "matrix"),
        ordering_status=_status(checks, "ordering"),
        workflow_integration_status=_status(checks, "workflow_integration"),
        doctor_integration_status=_status(checks, "doctor_integration"),
        installation_guidance_status=_status(checks, "installation_guidance"),
        privacy_status=_status(checks, "privacy"),
        determinism_status=_status(checks, "determinism"),
        vscode_regression_status=_status(checks, "vscode_regression"),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
    )


def write_report(monorepo: Path, report: VsCodeCliCompatibilityReport) -> Path:
    out_dir = monorepo / SV1311_OUTPUT_RELATIVE
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
