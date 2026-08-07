"""Slice 13.7 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_html_report_opening import VSCODE_HTML_REPORT_OPENING_ID
from verification.vscode_html_report_opening.checks import check_all
from verification.vscode_html_report_opening.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV137_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.vscode_html_report_opening.models import (
    CheckResult,
    Defect,
    Verdict,
    VsCodeHtmlReportOpeningReport,
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


def build_report(monorepo: Path) -> VsCodeHtmlReportOpeningReport:
    contract = default_contract()
    assert contract.start_epic_14 is False

    checks, defects = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    return VsCodeHtmlReportOpeningReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VSCODE_HTML_REPORT_OPENING_ID,
        verdict=_decide(failed, defects, limitations),
        report_policy_status=_status(checks, "report_policy"),
        engine_authority_status=_status(checks, "engine_authority"),
        location_contract_status=_status(checks, "location_contract"),
        containment_status=_status(checks, "containment"),
        symlink_boundary_status=_status(checks, "symlink_boundary"),
        file_validation_status=_status(checks, "file_validation"),
        stale_report_status=_status(checks, "stale_report"),
        ambiguity_status=_status(checks, "ambiguity"),
        automatic_open_status=_status(checks, "automatic_open"),
        explicit_open_status=_status(checks, "explicit_open"),
        assessment_integration_status=_status(checks, "assessment_integration"),
        open_api_status=_status(checks, "open_api"),
        primary_authority_status=_status(checks, "primary_authority"),
        network_boundary_status=_status(checks, "network_boundary"),
        telemetry_boundary_status=_status(checks, "telemetry_boundary"),
        analytics_boundary_status=_status(checks, "analytics_boundary"),
        privacy_status=_status(checks, "privacy"),
        vscode_regression_status=_status(checks, "vscode_regression"),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
    )


def write_report(monorepo: Path, report: VsCodeHtmlReportOpeningReport) -> Path:
    out_dir = monorepo / SV137_OUTPUT_RELATIVE
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
        "Epic 14 Product Experience not started. No commit/tag/publish/deploy.\n",
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
