"""Slice 13.2 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_cli_discovery import VSCODE_CLI_DISCOVERY_ID
from verification.vscode_cli_discovery.checks import (
    _status,
    check_discovery_package,
    check_integration,
    check_parsers_and_compat,
    check_scenarios,
)
from verification.vscode_cli_discovery.contract import (
    ALLOWED_LIMITATIONS,
    CANDIDATE_SOURCES,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV132_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.vscode_cli_discovery.models import (
    CheckResult,
    Defect,
    Verdict,
    VsCodeCliDiscoveryReport,
)


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def build_report(monorepo: Path) -> VsCodeCliDiscoveryReport:
    contract = default_contract()
    assert contract.start_slice_13_3 is True

    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    buckets: dict[str, list[CheckResult]] = {}

    def take(name: str, pair: tuple[list[CheckResult], list[Defect]]) -> None:
        c, d = pair
        buckets[name] = c
        all_checks.extend(c)
        all_defects.extend(d)

    take("pkg", check_discovery_package(monorepo))
    take("parsers", check_parsers_and_compat(monorepo))
    take("integration", check_integration(monorepo))
    take("scenarios", check_scenarios(monorepo))

    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in all_checks if not c.ok)

    def cat(category: str) -> list[CheckResult]:
        return [c for c in all_checks if c.category == category]

    report = VsCodeCliDiscoveryReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VSCODE_CLI_DISCOVERY_ID,
        verdict=_decide(failed, all_defects, limitations),
        discovery_policy_status=_status(cat("discovery_policy")),
        candidate_source_inventory=list(CANDIDATE_SOURCES),
        precedence_status=_status(cat("precedence") + cat("explicit_configuration")),
        explicit_configuration_status=_status(cat("explicit_configuration")),
        path_discovery_status=_status(cat("path_discovery")),
        executable_validation_status=_status(cat("executable_validation")),
        probe_status=_status(cat("probe")),
        identity_validation_status=_status(cat("identity_validation")),
        version_parsing_status=_status(cat("version_parsing")),
        compatibility_status=_status(cat("compatibility")),
        activation_boundary_status=_status(cat("activation_boundary")),
        workflow_integration_status=_status(cat("workflow_integration")),
        doctor_boundary_status=_status(cat("doctor_boundary")),
        privacy_status=_status(cat("privacy")),
        telemetry_boundary_status=_status(cat("telemetry_boundary")),
        analytics_boundary_status=_status(cat("analytics_boundary")),
        subprocess_boundary_status=_status(cat("subprocess_boundary")),
        vscode_regression_status=_status(cat("vscode_regression")),
        deferred_installation_status=_status(cat("deferred_installation")),
        defects=all_defects,
        blockers=[],
        limitations=limitations,
        checks=all_checks,
        total_checks=len(all_checks),
        failed_checks=failed,
    )
    return report


def write_report(monorepo: Path, report: VsCodeCliDiscoveryReport) -> Path:
    out_dir = monorepo / SV132_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    payload = report.to_dict()
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    md_path = out_dir / REPORT_MD
    md_path.write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Epic 13 complete for v0.2.0 epic scope (see sv13-15). "
        "Epic 14 Product Experience not started. No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    failed = [c for c in report.checks if not c.ok]
    print(
        f"{SCHEMA_NAME}:{SCHEMA_VERSION} verdict={report.verdict} "
        f"checks={report.total_checks} failed={report.failed_checks}"
    )
    for check in failed:
        print(f"  FAIL {check.name}: {check.detail}")
    print(f"report={path}")
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
