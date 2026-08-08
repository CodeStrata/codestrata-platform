"""Models for Slice 15.7 aggregation verification."""

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
class CommunityInsightsAggregationReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "15"
    slice: str = "15.7"
    policy_id: str = "community-insights-aggregation-policy"
    policy_version: str = "1.0"
    checkpoint_mode: str = "retention_only_with_limitation"
    cache_mode: str = "none"
    athena_required: bool = False
    policy_status: str = "not_executed"
    registry_status: str = "not_executed"
    reader_status: str = "not_executed"
    aggregation_status: str = "not_executed"
    privacy_status: str = "not_executed"
    infrastructure_boundary_status: str = "not_executed"
    dashboard_boundary_status: str = "not_executed"
    auth_boundary_status: str = "not_executed"
    slice_15_8_boundary_status: str = "not_executed"
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
            "aggregation_status": self.aggregation_status,
            "athena_required": self.athena_required,
            "auth_boundary_status": self.auth_boundary_status,
            "blockers": list(self.blockers),
            "cache_mode": self.cache_mode,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "checkpoint_mode": self.checkpoint_mode,
            "dashboard_boundary_status": self.dashboard_boundary_status,
            "defects": [d.to_dict() for d in self.defects],
            "determinism_status": self.determinism_status,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "infrastructure_boundary_status": self.infrastructure_boundary_status,
            "limitations": sorted(self.limitations),
            "policy_id": self.policy_id,
            "policy_status": self.policy_status,
            "policy_version": self.policy_version,
            "privacy_status": self.privacy_status,
            "reader_status": self.reader_status,
            "registry_status": self.registry_status,
            "release_posture": self.release_posture,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "slice_15_8_boundary_status": self.slice_15_8_boundary_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
        }
