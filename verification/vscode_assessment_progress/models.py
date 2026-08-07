"""Models for Slice 13.6 assessment progress verification reports."""

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
class VsCodeAssessmentProgressReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    progress_policy_status: str = "not_executed"
    lifecycle_status: str = "not_executed"
    phase_inventory: list[str] = field(default_factory=list)
    indeterminate_progress_status: str = "not_executed"
    engine_signal_status: str = "not_executed"
    standard_assessment_status: str = "not_executed"
    ai_assessment_status: str = "not_executed"
    cancellation_status: str = "not_executed"
    race_condition_status: str = "not_executed"
    primary_authority_status: str = "not_executed"
    telemetry_boundary_status: str = "not_executed"
    analytics_boundary_status: str = "not_executed"
    output_boundary_status: str = "not_executed"
    notification_boundary_status: str = "not_executed"
    report_phase_status: str = "not_executed"
    workflow_integration_status: str = "not_executed"
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
            "blockers": list(self.blockers),
            "cancellation_status": self.cancellation_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "defects": [d.to_dict() for d in self.defects],
            "engine_signal_status": self.engine_signal_status,
            "failed_checks": self.failed_checks,
            "indeterminate_progress_status": self.indeterminate_progress_status,
            "lifecycle_status": self.lifecycle_status,
            "limitations": sorted(self.limitations),
            "notification_boundary_status": self.notification_boundary_status,
            "output_boundary_status": self.output_boundary_status,
            "phase_inventory": list(self.phase_inventory),
            "primary_authority_status": self.primary_authority_status,
            "privacy_status": self.privacy_status,
            "progress_policy_status": self.progress_policy_status,
            "race_condition_status": self.race_condition_status,
            "report_phase_status": self.report_phase_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "standard_assessment_status": self.standard_assessment_status,
            "telemetry_boundary_status": self.telemetry_boundary_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_regression_status": self.vscode_regression_status,
            "workflow_integration_status": self.workflow_integration_status,
        }
