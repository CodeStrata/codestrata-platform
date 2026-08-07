"""Models for Slice 13.4 repository initialization verification reports."""

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
class VsCodeRepositoryInitializationReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    initialization_policy_status: str = "not_executed"
    command_surface_status: str = "not_executed"
    workspace_boundary_status: str = "not_executed"
    cli_readiness_status: str = "not_executed"
    state_detection_status: str = "not_executed"
    engine_authority_status: str = "not_executed"
    process_boundary_status: str = "not_executed"
    idempotency_status: str = "not_executed"
    existing_configuration_status: str = "not_executed"
    post_init_verification_status: str = "not_executed"
    source_mutation_status: str = "not_executed"
    git_boundary_status: str = "not_executed"
    network_boundary_status: str = "not_executed"
    ai_boundary_status: str = "not_executed"
    telemetry_boundary_status: str = "not_executed"
    analytics_boundary_status: str = "not_executed"
    report_boundary_status: str = "not_executed"
    workflow_integration_status: str = "not_executed"
    cancellation_status: str = "not_executed"
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
            "ai_boundary_status": self.ai_boundary_status,
            "analytics_boundary_status": self.analytics_boundary_status,
            "blockers": list(self.blockers),
            "cancellation_status": self.cancellation_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "cli_readiness_status": self.cli_readiness_status,
            "command_surface_status": self.command_surface_status,
            "defects": [d.to_dict() for d in self.defects],
            "engine_authority_status": self.engine_authority_status,
            "existing_configuration_status": self.existing_configuration_status,
            "failed_checks": self.failed_checks,
            "git_boundary_status": self.git_boundary_status,
            "idempotency_status": self.idempotency_status,
            "initialization_policy_status": self.initialization_policy_status,
            "limitations": sorted(self.limitations),
            "network_boundary_status": self.network_boundary_status,
            "post_init_verification_status": self.post_init_verification_status,
            "privacy_status": self.privacy_status,
            "process_boundary_status": self.process_boundary_status,
            "report_boundary_status": self.report_boundary_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "source_mutation_status": self.source_mutation_status,
            "state_detection_status": self.state_detection_status,
            "telemetry_boundary_status": self.telemetry_boundary_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_regression_status": self.vscode_regression_status,
            "workflow_integration_status": self.workflow_integration_status,
            "workspace_boundary_status": self.workspace_boundary_status,
        }
