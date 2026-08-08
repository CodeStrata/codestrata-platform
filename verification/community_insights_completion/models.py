"""Models for Slice 15.12 Epic 15 completion verification."""

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


@dataclass(frozen=True, slots=True)
class SliceRow:
    slice: str
    title: str
    policy: str
    verification_schema: str
    status: str
    checks: int
    failed_checks: int
    blockers: list[str]
    limitations: list[str]
    completion_state: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "blockers": list(self.blockers),
            "checks": self.checks,
            "completion_state": self.completion_state,
            "failed_checks": self.failed_checks,
            "limitations": list(self.limitations),
            "policy": self.policy,
            "slice": self.slice,
            "status": self.status,
            "title": self.title,
            "verification_schema": self.verification_schema,
        }


@dataclass
class CommunityInsightsCompletionReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "15"
    epic_complete: bool = False
    slice_matrix: list[dict[str, Any]] = field(default_factory=list)
    policy_registry: list[dict[str, str]] = field(default_factory=list)
    schema_registry: list[dict[str, str]] = field(default_factory=list)
    slice_matrix_status: str = "not_executed"
    policy_registry_status: str = "not_executed"
    schema_registry_status: str = "not_executed"
    data_lake_status: str = "not_executed"
    partitioning_status: str = "not_executed"
    event_coverage_status: str = "not_executed"
    ingestion_status: str = "not_executed"
    query_strategy_status: str = "not_executed"
    metrics_status: str = "not_executed"
    aggregation_status: str = "not_executed"
    application_status: str = "not_executed"
    authentication_status: str = "not_executed"
    dashboard_status: str = "not_executed"
    system_validation_status: str = "not_executed"
    low_cost_status: str = "not_executed"
    privacy_status: str = "not_executed"
    source_locality_status: str = "not_executed"
    production_data_status: str = "not_executed"
    export_status: str = "not_executed"
    iam_status: str = "not_executed"
    design_system_status: str = "not_executed"
    documentation_boundary_status: str = "not_executed"
    epic_16_boundary_status: str = "not_executed"
    release_posture_status: str = "not_executed"
    determinism_status: str = "not_executed"
    release_posture: dict[str, Any] = field(default_factory=dict)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    completed_slices: int = 0
    total_slices: int = 12

    def to_dict(self) -> dict[str, Any]:
        return {
            "aggregation_status": self.aggregation_status,
            "application_status": self.application_status,
            "authentication_status": self.authentication_status,
            "blockers": list(self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "completed_slices": self.completed_slices,
            "dashboard_status": self.dashboard_status,
            "data_lake_status": self.data_lake_status,
            "defects": [d.to_dict() for d in self.defects],
            "design_system_status": self.design_system_status,
            "determinism_status": self.determinism_status,
            "documentation_boundary_status": self.documentation_boundary_status,
            "epic": self.epic,
            "epic_16_boundary_status": self.epic_16_boundary_status,
            "epic_complete": self.epic_complete,
            "event_coverage_status": self.event_coverage_status,
            "export_status": self.export_status,
            "failed_checks": self.failed_checks,
            "iam_status": self.iam_status,
            "ingestion_status": self.ingestion_status,
            "limitations": sorted(self.limitations),
            "live_dashboard_data_available": False,
            "low_cost_status": self.low_cost_status,
            "metrics_status": self.metrics_status,
            "partitioning_status": self.partitioning_status,
            "policy_registry": self.policy_registry,
            "policy_registry_status": self.policy_registry_status,
            "privacy_status": self.privacy_status,
            "production_data_status": self.production_data_status,
            "production_ingestion_enabled": False,
            "query_strategy_status": self.query_strategy_status,
            "release_posture": self.release_posture,
            "release_posture_status": self.release_posture_status,
            "schema_name": self.schema_name,
            "schema_registry": self.schema_registry,
            "schema_registry_status": self.schema_registry_status,
            "schema_version": self.schema_version,
            "slice_matrix": self.slice_matrix,
            "slice_matrix_status": self.slice_matrix_status,
            "source_locality_status": self.source_locality_status,
            "system_validation_status": self.system_validation_status,
            "total_checks": self.total_checks,
            "total_slices": self.total_slices,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
        }
