"""Models for Slice 15.3 event coverage verification."""

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
class CommunityInsightsEventCoverageReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "15"
    slice: str = "15.3"
    policy_id: str = "community-insights-event-coverage-policy"
    policy_version: str = "1.0"
    model_adoption_privacy_decision: str = "C_normalized_model_family_allowed"
    metric_matrix: list[dict[str, Any]] = field(default_factory=list)
    change_register: list[dict[str, Any]] = field(default_factory=list)
    schema_inventory: list[dict[str, Any]] = field(default_factory=list)
    field_classifications: list[dict[str, Any]] = field(default_factory=list)
    stream_inventory_status: str = "not_executed"
    identity_status: str = "not_executed"
    metric_coverage_status: str = "not_executed"
    privacy_status: str = "not_executed"
    change_register_status: str = "not_executed"
    ingestion_boundary_status: str = "not_executed"
    aggregation_boundary_status: str = "not_executed"
    dashboard_boundary_status: str = "not_executed"
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
            "aggregation_boundary_status": self.aggregation_boundary_status,
            "blockers": list(self.blockers),
            "change_register": self.change_register,
            "change_register_status": self.change_register_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "dashboard_boundary_status": self.dashboard_boundary_status,
            "defects": [d.to_dict() for d in self.defects],
            "determinism_status": self.determinism_status,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "field_classifications": self.field_classifications,
            "identity_status": self.identity_status,
            "ingestion_boundary_status": self.ingestion_boundary_status,
            "limitations": sorted(self.limitations),
            "metric_coverage_status": self.metric_coverage_status,
            "metric_matrix": self.metric_matrix,
            "model_adoption_privacy_decision": self.model_adoption_privacy_decision,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "privacy_status": self.privacy_status,
            "release_posture": self.release_posture,
            "schema_inventory": self.schema_inventory,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "slice_15_7_boundary_status": self.slice_15_7_boundary_status,
            "stream_inventory_status": self.stream_inventory_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
        }
