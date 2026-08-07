"""Models for Slice 13.10 source locality verification."""

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
class VsCodeSourceLocalityReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    locality_policy_status: str = "not_executed"
    filesystem_read_status: str = "not_executed"
    filesystem_write_status: str = "not_executed"
    generated_artifact_status: str = "not_executed"
    process_boundary_status: str = "not_executed"
    standard_assessment_status: str = "not_executed"
    ai_assessment_status: str = "not_executed"
    ai_provider_boundary_status: str = "not_executed"
    report_boundary_status: str = "not_executed"
    discovery_boundary_status: str = "not_executed"
    installation_boundary_status: str = "not_executed"
    initialization_boundary_status: str = "not_executed"
    recovery_boundary_status: str = "not_executed"
    telemetry_boundary_status: str = "not_executed"
    analytics_boundary_status: str = "not_executed"
    network_boundary_status: str = "not_executed"
    cloud_boundary_status: str = "not_executed"
    data_lake_boundary_status: str = "not_executed"
    identity_boundary_status: str = "not_executed"
    credential_boundary_status: str = "not_executed"
    git_boundary_status: str = "not_executed"
    output_boundary_status: str = "not_executed"
    privacy_claim_status: str = "not_executed"
    vscode_regression_status: str = "not_executed"
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ai_assessment_status": self.ai_assessment_status,
            "ai_provider_boundary_status": self.ai_provider_boundary_status,
            "analytics_boundary_status": self.analytics_boundary_status,
            "blockers": list(self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "cloud_boundary_status": self.cloud_boundary_status,
            "credential_boundary_status": self.credential_boundary_status,
            "data_lake_boundary_status": self.data_lake_boundary_status,
            "defects": [d.to_dict() for d in self.defects],
            "discovery_boundary_status": self.discovery_boundary_status,
            "failed_checks": self.failed_checks,
            "filesystem_read_status": self.filesystem_read_status,
            "filesystem_write_status": self.filesystem_write_status,
            "generated_artifact_status": self.generated_artifact_status,
            "git_boundary_status": self.git_boundary_status,
            "identity_boundary_status": self.identity_boundary_status,
            "initialization_boundary_status": self.initialization_boundary_status,
            "installation_boundary_status": self.installation_boundary_status,
            "limitations": sorted(self.limitations),
            "locality_policy_status": self.locality_policy_status,
            "network_boundary_status": self.network_boundary_status,
            "output_boundary_status": self.output_boundary_status,
            "privacy_claim_status": self.privacy_claim_status,
            "process_boundary_status": self.process_boundary_status,
            "recovery_boundary_status": self.recovery_boundary_status,
            "report_boundary_status": self.report_boundary_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "standard_assessment_status": self.standard_assessment_status,
            "telemetry_boundary_status": self.telemetry_boundary_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_regression_status": self.vscode_regression_status,
        }
