"""Models for Slice 15.11 validation verification."""

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
class CommunityInsightsValidationReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "15"
    slice: str = "15.11"
    policy_id: str = "community-insights-validation-policy"
    policy_version: str = "1.0"
    policy_status: str = "not_executed"
    contract_status: str = "not_executed"
    metric_correctness_status: str = "not_executed"
    privacy_status: str = "not_executed"
    suppression_status: str = "not_executed"
    query_bounds_status: str = "not_executed"
    auth_status: str = "not_executed"
    access_control_status: str = "not_executed"
    ui_status: str = "not_executed"
    design_system_status: str = "not_executed"
    accessibility_status: str = "not_executed"
    responsive_status: str = "not_executed"
    security_status: str = "not_executed"
    export_status: str = "not_executed"
    athena_boundary_status: str = "not_executed"
    deployment_boundary_status: str = "not_executed"
    epic_completion_boundary_status: str = "not_executed"
    scenarios_status: str = "not_executed"
    determinism_status: str = "not_executed"
    release_posture: dict[str, Any] = field(default_factory=dict)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "access_control_status": self.access_control_status,
            "accessibility_status": self.accessibility_status,
            "athena_boundary_status": self.athena_boundary_status,
            "auth_status": self.auth_status,
            "blockers": list(self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "contract_status": self.contract_status,
            "defects": [d.to_dict() for d in self.defects],
            "deployment_boundary_status": self.deployment_boundary_status,
            "design_system_status": self.design_system_status,
            "determinism_status": self.determinism_status,
            "epic": self.epic,
            "epic_completion_boundary_status": self.epic_completion_boundary_status,
            "export_status": self.export_status,
            "failed_checks": self.failed_checks,
            "limitations": sorted(self.limitations),
            "metric_correctness_status": self.metric_correctness_status,
            "policy_id": self.policy_id,
            "policy_status": self.policy_status,
            "policy_version": self.policy_version,
            "privacy_status": self.privacy_status,
            "query_bounds_status": self.query_bounds_status,
            "release_posture": self.release_posture,
            "responsive_status": self.responsive_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "scenarios_status": self.scenarios_status,
            "security_status": self.security_status,
            "slice": self.slice,
            "suppression_status": self.suppression_status,
            "total_checks": self.total_checks,
            "ui_status": self.ui_status,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
        }
