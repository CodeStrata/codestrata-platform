"""Models for Slice 15.6 metrics verification."""

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
class CommunityInsightsMetricsReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "15"
    slice: str = "15.6"
    policy_id: str = "community-insights-metrics-policy"
    policy_version: str = "1.0"
    mau_window: str = "rolling_30_utc_days"
    cohort_minimum: int = 3
    metric_summaries: list[dict[str, Any]] = field(default_factory=list)
    policy_status: str = "not_executed"
    catalog_status: str = "not_executed"
    privacy_status: str = "not_executed"
    completeness_status: str = "not_executed"
    aggregation_boundary_status: str = "not_executed"
    dashboard_boundary_status: str = "not_executed"
    auth_boundary_status: str = "not_executed"
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
            "auth_boundary_status": self.auth_boundary_status,
            "blockers": list(self.blockers),
            "catalog_status": self.catalog_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "cohort_minimum": self.cohort_minimum,
            "completeness_status": self.completeness_status,
            "dashboard_boundary_status": self.dashboard_boundary_status,
            "defects": [d.to_dict() for d in self.defects],
            "determinism_status": self.determinism_status,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "limitations": sorted(self.limitations),
            "mau_window": self.mau_window,
            "metric_summaries": self.metric_summaries,
            "policy_id": self.policy_id,
            "policy_status": self.policy_status,
            "policy_version": self.policy_version,
            "privacy_status": self.privacy_status,
            "release_posture": self.release_posture,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "slice_15_7_boundary_status": self.slice_15_7_boundary_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
        }
