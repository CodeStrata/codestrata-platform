"""Slice 13.9 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_telemetry_consent_integration import (
    VSCODE_TELEMETRY_CONSENT_INTEGRATION_ID,
)
from verification.vscode_telemetry_consent_integration.checks import check_all
from verification.vscode_telemetry_consent_integration.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV139_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.vscode_telemetry_consent_integration.models import (
    CheckResult,
    Defect,
    Verdict,
    VsCodeTelemetryConsentIntegrationReport,
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


def build_report(monorepo: Path) -> VsCodeTelemetryConsentIntegrationReport:
    contract = default_contract()
    assert contract.start_epic_14 is False

    checks, defects = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    return VsCodeTelemetryConsentIntegrationReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VSCODE_TELEMETRY_CONSENT_INTEGRATION_ID,
        verdict=_decide(failed, defects, limitations),
        integration_policy_status=_status(checks, "integration_policy"),
        runtime_relationship_status=_status(checks, "runtime_relationship"),
        eligibility_status=_status(checks, "eligibility"),
        readiness_ordering_status=_status(checks, "readiness_ordering"),
        consent_prompt_status=_status(checks, "consent_prompt"),
        consent_scope_status=_status(checks, "consent_scope"),
        non_interactive_status=_status(checks, "non_interactive"),
        allow_status=_status(checks, "allow"),
        deny_status=_status(checks, "deny"),
        analytics_integration_status=_status(checks, "analytics_integration"),
        telemetry_lifecycle_status=_status(checks, "telemetry_lifecycle"),
        primary_authority_status=_status(checks, "primary_authority"),
        report_boundary_status=_status(checks, "report_boundary"),
        recovery_boundary_status=_status(checks, "recovery_boundary"),
        init_install_discovery_status=_status(checks, "init_install_discovery"),
        activation_status=_status(checks, "activation"),
        persistence_status=_status(checks, "persistence"),
        identity_status=_status(checks, "identity"),
        transport_status=_status(checks, "transport"),
        privacy_status=_status(checks, "privacy"),
        diagnostics_status=_status(checks, "diagnostics"),
        cross_client_relationship_status=_status(
            checks, "cross_client_relationship"
        ),
        vscode_regression_status=_status(checks, "vscode_regression"),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
    )


def write_report(
    monorepo: Path, report: VsCodeTelemetryConsentIntegrationReport
) -> Path:
    out_dir = monorepo / SV139_OUTPUT_RELATIVE
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
