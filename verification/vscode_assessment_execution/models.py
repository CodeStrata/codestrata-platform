"""Models for Slice 13.5 assessment execution verification reports."""

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
class VsCodeAssessmentExecutionReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    assessment_policy_status: str = "not_executed"
    command_surface_status: str = "not_executed"
    readiness_status: str = "not_executed"
    initialization_boundary_status: str = "not_executed"
    standard_assessment_status: str = "not_executed"
    ai_assessment_status: str = "not_executed"
    engine_authority_status: str = "not_executed"
    cli_invocation_status: str = "not_executed"
    consent_ordering_status: str = "not_executed"
    telemetry_boundary_status: str = "not_executed"
    analytics_boundary_status: str = "not_executed"
    process_boundary_status: str = "not_executed"
    cancellation_status: str = "not_executed"
    primary_authority_status: str = "not_executed"
    report_postcondition_status: str = "not_executed"
    source_mutation_status: str = "not_executed"
    config_mutation_status: str = "not_executed"
    git_boundary_status: str = "not_executed"
    network_boundary_status: str = "not_executed"
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
            "ai_assessment_status": self.ai_assessment_status,
            "analytics_boundary_status": self.analytics_boundary_status,
            "assessment_policy_status": self.assessment_policy_status,
            "blockers": list(self.blockers),
            "cancellation_status": self.cancellation_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "cli_invocation_status": self.cli_invocation_status,
            "command_surface_status": self.command_surface_status,
            "config_mutation_status": self.config_mutation_status,
            "consent_ordering_status": self.consent_ordering_status,
            "defects": [d.to_dict() for d in self.defects],
            "engine_authority_status": self.engine_authority_status,
            "failed_checks": self.failed_checks,
            "git_boundary_status": self.git_boundary_status,
            "initialization_boundary_status": self.initialization_boundary_status,
            "limitations": sorted(self.limitations),
            "network_boundary_status": self.network_boundary_status,
            "primary_authority_status": self.primary_authority_status,
            "privacy_status": self.privacy_status,
            "process_boundary_status": self.process_boundary_status,
            "readiness_status": self.readiness_status,
            "report_postcondition_status": self.report_postcondition_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "source_mutation_status": self.source_mutation_status,
            "standard_assessment_status": self.standard_assessment_status,
            "telemetry_boundary_status": self.telemetry_boundary_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_regression_status": self.vscode_regression_status,
        }
