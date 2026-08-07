"""Slice 13.3 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_cli_installation import VSCODE_CLI_INSTALLATION_ID
from verification.vscode_cli_installation.checks import check_all
from verification.vscode_cli_installation.contract import (
    ALLOWED_LIMITATIONS,
    APPROACH_DECISION,
    METHOD_IDS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV133_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.vscode_cli_installation.models import (
    CheckResult,
    Defect,
    Verdict,
    VsCodeCliInstallationReport,
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


def build_report(monorepo: Path) -> VsCodeCliInstallationReport:
    contract = default_contract()
    assert contract.start_slice_13_4 is False
    assert contract.approach == APPROACH_DECISION

    checks, defects = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    return VsCodeCliInstallationReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VSCODE_CLI_INSTALLATION_ID,
        verdict=_decide(failed, defects, limitations),
        installation_policy_status=_status(checks, "installation_policy"),
        approach_decision=APPROACH_DECISION,
        method_inventory=list(METHOD_IDS),
        discovery_mapping_status=_status(checks, "discovery_mapping"),
        command_surface_status=_status(checks, "command_surface"),
        first_run_status=_status(checks, "first_run"),
        guidance_status=_status(checks, "guidance"),
        clipboard_status=_status(checks, "clipboard"),
        terminal_status=_status(checks, "terminal"),
        documentation_status=_status(checks, "documentation"),
        automatic_installation_status=_status(checks, "automatic_installation"),
        network_boundary_status=_status(checks, "network_boundary"),
        persistence_boundary_status=_status(checks, "persistence_boundary"),
        telemetry_boundary_status=_status(checks, "telemetry_boundary"),
        analytics_boundary_status=_status(checks, "analytics_boundary"),
        doctor_boundary_status=_status(checks, "doctor_boundary"),
        activation_boundary_status=_status(checks, "activation_boundary"),
        privacy_status=_status(checks, "privacy"),
        vscode_regression_status=_status(checks, "vscode_regression"),
        deferred_clean_install_status=_status(checks, "deferred_clean_install"),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
    )


def write_report(monorepo: Path, report: VsCodeCliInstallationReport) -> Path:
    out_dir = monorepo / SV133_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Approach: `{report.approach_decision}`\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 13.5 assessment redesign not started by this package. "
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
