"""Models for Slice 15.4 ingestion verification."""

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
class CommunityInsightsIngestionReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "15"
    slice: str = "15.4"
    policy_id: str = "community-insights-ingestion-policy"
    policy_version: str = "1.0"
    operational_activation_state: str = "activation_ready_but_production_disabled"
    change_register_disposition: dict[str, Any] = field(default_factory=dict)
    package_ecosystem_vocab: list[str] = field(default_factory=list)
    provider_families: list[str] = field(default_factory=list)
    policy_status: str = "not_executed"
    cr_status: str = "not_executed"
    ecosystem_status: str = "not_executed"
    provider_status: str = "not_executed"
    model_status: str = "not_executed"
    identity_status: str = "not_executed"
    privacy_status: str = "not_executed"
    activation_status: str = "not_executed"
    isolation_status: str = "not_executed"
    quarantine_status: str = "not_executed"
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
            "change_register_disposition": self.change_register_disposition,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "cr_status": self.cr_status,
            "dashboard_boundary_status": self.dashboard_boundary_status,
            "defects": [d.to_dict() for d in self.defects],
            "determinism_status": self.determinism_status,
            "ecosystem_status": self.ecosystem_status,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "identity_status": self.identity_status,
            "isolation_status": self.isolation_status,
            "limitations": sorted(self.limitations),
            "model_status": self.model_status,
            "operational_activation_state": self.operational_activation_state,
            "package_ecosystem_vocab": self.package_ecosystem_vocab,
            "policy_id": self.policy_id,
            "policy_status": self.policy_status,
            "policy_version": self.policy_version,
            "privacy_status": self.privacy_status,
            "provider_families": self.provider_families,
            "provider_status": self.provider_status,
            "quarantine_status": self.quarantine_status,
            "release_posture": self.release_posture,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "slice_15_7_boundary_status": self.slice_15_7_boundary_status,
            "activation_status": self.activation_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
        }
