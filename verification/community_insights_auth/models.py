"""Models for Slice 15.9 auth verification."""

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
class CommunityInsightsAuthReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "15"
    slice: str = "15.9"
    policy_id: str = "community-insights-auth-policy"
    policy_version: str = "1.0"
    policy_status: str = "not_executed"
    contract_status: str = "not_executed"
    platform_status: str = "not_executed"
    runtime_status: str = "not_executed"
    frontend_status: str = "not_executed"
    infrastructure_boundary_status: str = "not_executed"
    cors_csrf_status: str = "not_executed"
    privacy_status: str = "not_executed"
    deployment_boundary_status: str = "not_executed"
    aggregation_boundary_status: str = "not_executed"
    metrics_boundary_status: str = "not_executed"
    slice_15_10_boundary_status: str = "not_executed"
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
            "aggregation_boundary_status": self.aggregation_boundary_status,
            "blockers": list(self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "contract_status": self.contract_status,
            "cors_csrf_status": self.cors_csrf_status,
            "defects": [d.to_dict() for d in self.defects],
            "deployment_boundary_status": self.deployment_boundary_status,
            "determinism_status": self.determinism_status,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "frontend_status": self.frontend_status,
            "infrastructure_boundary_status": self.infrastructure_boundary_status,
            "limitations": sorted(self.limitations),
            "metrics_boundary_status": self.metrics_boundary_status,
            "platform_status": self.platform_status,
            "policy_id": self.policy_id,
            "policy_status": self.policy_status,
            "policy_version": self.policy_version,
            "privacy_status": self.privacy_status,
            "release_posture": self.release_posture,
            "runtime_status": self.runtime_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "scenarios_status": self.scenarios_status,
            "slice": self.slice,
            "slice_15_10_boundary_status": self.slice_15_10_boundary_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
        }
