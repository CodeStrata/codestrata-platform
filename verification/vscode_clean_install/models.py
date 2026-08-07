"""Models for Slice 13.14 clean-install verification."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL"]


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str
    category: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "detail": self.detail,
            "name": self.name,
            "ok": self.ok,
        }


@dataclass(frozen=True, slots=True)
class Defect:
    classification: str
    surface: str
    expected: str
    observed: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VsCodeCleanInstallReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    clean_install_policy_status: str = "not_executed"
    package_build_status: str = "not_executed"
    package_inventory_status: str = "not_executed"
    isolated_environment_status: str = "not_executed"
    install_status: str = "not_executed"
    activation_status: str = "not_executed"
    first_run_status: str = "not_executed"
    cli_missing_status: str = "not_executed"
    cli_incompatible_status: str = "not_executed"
    cli_compatible_status: str = "not_executed"
    initialization_status: str = "not_executed"
    standard_assessment_status: str = "not_executed"
    ai_assessment_status: str = "not_executed"
    progress_status: str = "not_executed"
    report_status: str = "not_executed"
    recovery_status: str = "not_executed"
    telemetry_consent_status: str = "not_executed"
    analytics_status: str = "not_executed"
    state_inventory_status: str = "not_executed"
    update_status: str = "not_executed"
    uninstall_reinstall_status: str = "not_executed"
    cursor_absence_status: str = "not_executed"
    package_integrity_status: str = "not_executed"
    vscode_compatibility_status: str = "not_executed"
    privacy_status: str = "not_executed"
    vscode_regression_status: str = "not_executed"
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    package_file_count: int = 0
    package_size_bytes: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "activation_status": self.activation_status,
            "ai_assessment_status": self.ai_assessment_status,
            "analytics_status": self.analytics_status,
            "blockers": list(self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "cli_compatible_status": self.cli_compatible_status,
            "cli_incompatible_status": self.cli_incompatible_status,
            "cli_missing_status": self.cli_missing_status,
            "clean_install_policy_status": self.clean_install_policy_status,
            "cursor_absence_status": self.cursor_absence_status,
            "defects": [d.to_dict() for d in self.defects],
            "failed_checks": self.failed_checks,
            "first_run_status": self.first_run_status,
            "initialization_status": self.initialization_status,
            "install_status": self.install_status,
            "isolated_environment_status": self.isolated_environment_status,
            "limitations": sorted(self.limitations),
            "package_build_status": self.package_build_status,
            "package_file_count": self.package_file_count,
            "package_integrity_status": self.package_integrity_status,
            "package_inventory_status": self.package_inventory_status,
            "package_size_bytes": self.package_size_bytes,
            "privacy_status": self.privacy_status,
            "progress_status": self.progress_status,
            "recovery_status": self.recovery_status,
            "report_status": self.report_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "standard_assessment_status": self.standard_assessment_status,
            "state_inventory_status": self.state_inventory_status,
            "telemetry_consent_status": self.telemetry_consent_status,
            "total_checks": self.total_checks,
            "uninstall_reinstall_status": self.uninstall_reinstall_status,
            "update_status": self.update_status,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_compatibility_status": self.vscode_compatibility_status,
            "vscode_regression_status": self.vscode_regression_status,
        }
