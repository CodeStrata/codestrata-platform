"""Models for Slice 15.1 Community Data Lake audit."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL"]
FindingClass = Literal["Accepted", "Requires Change", "Historical", "Deferred"]


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
class AuditFinding:
    area: str
    classification: FindingClass
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CommunityDataLakeAuditReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "15"
    slice: str = "15.1"
    policy_id: str = "community-data-lake-policy"
    policy_version: str = "1.0"
    findings: list[AuditFinding] = field(default_factory=list)
    bucket_layout_status: str = "not_executed"
    event_partitions_status: str = "not_executed"
    schema_consistency_status: str = "not_executed"
    privacy_compliance_status: str = "not_executed"
    anonymous_identity_status: str = "not_executed"
    no_source_code_status: str = "not_executed"
    no_personal_identifiers_status: str = "not_executed"
    dashboard_readiness_status: str = "not_executed"
    export_boundary_status: str = "not_executed"
    retention_status: str = "not_executed"
    ownership_status: str = "not_executed"
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
            "anonymous_identity_status": self.anonymous_identity_status,
            "blockers": list(self.blockers),
            "bucket_layout_status": self.bucket_layout_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "dashboard_readiness_status": self.dashboard_readiness_status,
            "defects": [d.to_dict() for d in self.defects],
            "determinism_status": self.determinism_status,
            "epic": self.epic,
            "event_partitions_status": self.event_partitions_status,
            "export_boundary_status": self.export_boundary_status,
            "failed_checks": self.failed_checks,
            "findings": [f.to_dict() for f in self.findings],
            "limitations": sorted(self.limitations),
            "no_personal_identifiers_status": self.no_personal_identifiers_status,
            "no_source_code_status": self.no_source_code_status,
            "ownership_status": self.ownership_status,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "privacy_compliance_status": self.privacy_compliance_status,
            "release_posture": self.release_posture,
            "retention_status": self.retention_status,
            "schema_consistency_status": self.schema_consistency_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "slice_15_7_boundary_status": self.slice_15_7_boundary_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
        }
