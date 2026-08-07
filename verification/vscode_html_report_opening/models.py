"""Models for Slice 13.7 HTML report opening verification."""

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
class VsCodeHtmlReportOpeningReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    report_policy_status: str = "not_executed"
    engine_authority_status: str = "not_executed"
    location_contract_status: str = "not_executed"
    containment_status: str = "not_executed"
    symlink_boundary_status: str = "not_executed"
    file_validation_status: str = "not_executed"
    stale_report_status: str = "not_executed"
    ambiguity_status: str = "not_executed"
    automatic_open_status: str = "not_executed"
    explicit_open_status: str = "not_executed"
    assessment_integration_status: str = "not_executed"
    open_api_status: str = "not_executed"
    primary_authority_status: str = "not_executed"
    network_boundary_status: str = "not_executed"
    telemetry_boundary_status: str = "not_executed"
    analytics_boundary_status: str = "not_executed"
    privacy_status: str = "not_executed"
    vscode_regression_status: str = "not_executed"
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ambiguity_status": self.ambiguity_status,
            "analytics_boundary_status": self.analytics_boundary_status,
            "assessment_integration_status": self.assessment_integration_status,
            "automatic_open_status": self.automatic_open_status,
            "blockers": list(self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "containment_status": self.containment_status,
            "defects": [d.to_dict() for d in self.defects],
            "engine_authority_status": self.engine_authority_status,
            "explicit_open_status": self.explicit_open_status,
            "failed_checks": self.failed_checks,
            "file_validation_status": self.file_validation_status,
            "limitations": sorted(self.limitations),
            "location_contract_status": self.location_contract_status,
            "network_boundary_status": self.network_boundary_status,
            "open_api_status": self.open_api_status,
            "primary_authority_status": self.primary_authority_status,
            "privacy_status": self.privacy_status,
            "report_policy_status": self.report_policy_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "stale_report_status": self.stale_report_status,
            "symlink_boundary_status": self.symlink_boundary_status,
            "telemetry_boundary_status": self.telemetry_boundary_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_regression_status": self.vscode_regression_status,
        }
