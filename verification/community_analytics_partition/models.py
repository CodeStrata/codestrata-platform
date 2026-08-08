"""Models for Slice 15.2 analytics partition verification."""

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
class CommunityAnalyticsPartitionReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "15"
    slice: str = "15.2"
    policy_id: str = "community-analytics-partition-policy"
    policy_version: str = "1.0"
    partition_redesign_required: bool = False
    metric_matrix: list[dict[str, Any]] = field(default_factory=list)
    partition_hierarchy_status: str = "not_executed"
    prefix_strategy_status: str = "not_executed"
    bounded_query_status: str = "not_executed"
    metric_support_status: str = "not_executed"
    privacy_partition_status: str = "not_executed"
    deterministic_mapping_status: str = "not_executed"
    backward_compatibility_status: str = "not_executed"
    slice_15_7_boundary_status: str = "not_executed"
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
            "backward_compatibility_status": self.backward_compatibility_status,
            "blockers": list(self.blockers),
            "bounded_query_status": self.bounded_query_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "defects": [d.to_dict() for d in self.defects],
            "determinism_status": self.determinism_status,
            "deterministic_mapping_status": self.deterministic_mapping_status,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "limitations": sorted(self.limitations),
            "metric_matrix": self.metric_matrix,
            "metric_support_status": self.metric_support_status,
            "partition_hierarchy_status": self.partition_hierarchy_status,
            "partition_redesign_required": self.partition_redesign_required,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "prefix_strategy_status": self.prefix_strategy_status,
            "privacy_partition_status": self.privacy_partition_status,
            "release_posture": self.release_posture,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "slice_15_7_boundary_status": self.slice_15_7_boundary_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
        }
