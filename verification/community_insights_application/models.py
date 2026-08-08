"""Models for Slice 15.8 application verification."""

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
class CommunityInsightsApplicationReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "15"
    slice: str = "15.8"
    policy_id: str = "codestrata-insights-application-policy"
    policy_version: str = "1.0"
    future_repository: str = "codestrata-insights"
    future_host: str = "insights.codestrata.ai"
    stack: str = "react_vite_typescript"
    policy_status: str = "not_executed"
    application_status: str = "not_executed"
    design_system_status: str = "not_executed"
    metric_contract_status: str = "not_executed"
    export_status: str = "not_executed"
    privacy_status: str = "not_executed"
    auth_boundary_status: str = "not_executed"
    deployment_boundary_status: str = "not_executed"
    slice_15_9_boundary_status: str = "not_executed"
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
            "application_status": self.application_status,
            "auth_boundary_status": self.auth_boundary_status,
            "blockers": list(self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "defects": [d.to_dict() for d in self.defects],
            "deployment_boundary_status": self.deployment_boundary_status,
            "design_system_status": self.design_system_status,
            "determinism_status": self.determinism_status,
            "epic": self.epic,
            "export_status": self.export_status,
            "failed_checks": self.failed_checks,
            "future_host": self.future_host,
            "future_repository": self.future_repository,
            "limitations": sorted(self.limitations),
            "metric_contract_status": self.metric_contract_status,
            "policy_id": self.policy_id,
            "policy_status": self.policy_status,
            "policy_version": self.policy_version,
            "privacy_status": self.privacy_status,
            "release_posture": self.release_posture,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "slice_15_9_boundary_status": self.slice_15_9_boundary_status,
            "stack": self.stack,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
        }
