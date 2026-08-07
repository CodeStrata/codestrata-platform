"""Slice 13.14 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_clean_install import VSCODE_CLEAN_INSTALL_ID
from verification.vscode_clean_install.checks import check_all
from verification.vscode_clean_install.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1314_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.vscode_clean_install.models import (
    CheckResult,
    Defect,
    Verdict,
    VsCodeCleanInstallReport,
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


def build_report(monorepo: Path) -> VsCodeCleanInstallReport:
    contract = default_contract()
    assert contract.start_epic_14 is False
    assert contract.no_publish is True

    checks, defects, meta = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    return VsCodeCleanInstallReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VSCODE_CLEAN_INSTALL_ID,
        verdict=_decide(failed, defects, limitations),
        clean_install_policy_status=_status(checks, "clean_install_policy"),
        package_build_status=_status(checks, "package_build"),
        package_inventory_status=_status(checks, "package_inventory"),
        isolated_environment_status=_status(checks, "isolated_environment"),
        install_status=_status(checks, "install"),
        activation_status=_status(checks, "activation"),
        first_run_status=_status(checks, "first_run"),
        cli_missing_status=_status(checks, "cli_missing"),
        cli_incompatible_status=_status(checks, "cli_incompatible"),
        cli_compatible_status=_status(checks, "cli_compatible"),
        initialization_status=_status(checks, "initialization"),
        standard_assessment_status=_status(checks, "standard_assessment"),
        ai_assessment_status=_status(checks, "ai_assessment"),
        progress_status=_status(checks, "progress"),
        report_status=_status(checks, "report"),
        recovery_status=_status(checks, "recovery"),
        telemetry_consent_status=_status(checks, "telemetry_consent"),
        analytics_status=_status(checks, "analytics"),
        state_inventory_status=_status(checks, "state_inventory"),
        update_status=_status(checks, "update"),
        uninstall_reinstall_status=_status(checks, "uninstall_reinstall"),
        cursor_absence_status=_status(checks, "cursor_absence"),
        package_integrity_status=_status(checks, "package_integrity"),
        vscode_compatibility_status=_status(checks, "vscode_compatibility"),
        privacy_status=_status(checks, "privacy"),
        vscode_regression_status=_status(checks, "vscode_regression"),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
        package_file_count=int(meta.get("package_file_count", 0)),
        package_size_bytes=int(meta.get("package_size_bytes", 0)),
    )


def write_report(monorepo: Path, report: VsCodeCleanInstallReport) -> Path:
    out_dir = monorepo / SV1314_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"
    assert "timestamp" not in text
    assert "/Users/" not in text
    assert "file://" not in text
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        f"Package files: {report.package_file_count} · "
        f"size_bytes: {report.package_size_bytes}\n\n"
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
        f"checks={report.total_checks} failed={report.failed_checks} "
        f"files={report.package_file_count} bytes={report.package_size_bytes}"
    )
    for check in report.checks:
        if not check.ok:
            print(f"  FAIL {check.name}: {check.detail}")
    print(f"report={path}")
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
