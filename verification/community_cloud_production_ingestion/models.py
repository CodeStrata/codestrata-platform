"""Models for Slice 17.7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL"]


@dataclass(slots=True)
class CheckResult:
    check_id: str
    ok: bool
    detail: str
    category: str


@dataclass(slots=True)
class Defect:
    classification: str
    surface: str
    expected: str
    observed: str


@dataclass(slots=True)
class CommunityCloudProductionIngestionReport:
    schema: str
    schema_version: str
    package_id: str
    package_version: str
    epic: str
    slice: str
    verdict: Verdict
    total_checks: int
    failed_checks: int
    limitations: list[str]
    checks: list[dict[str, Any]]
    defects: list[dict[str, Any]]
    policy: dict[str, Any]
    register: dict[str, Any]
    evidence: dict[str, Any]
    inventory: dict[str, Any]
    writer_policy: dict[str, Any]
    writer_attachment: dict[str, Any]
    ingestion_activation: dict[str, Any]
    streams: dict[str, Any]
    data_lake: dict[str, Any]
    privacy: dict[str, Any]
    quarantine: dict[str, Any]
    consent: dict[str, Any]
    failure_isolation: dict[str, Any]
    report_artifact_boundary: dict[str, Any]
    security: dict[str, Any]
    cost: dict[str, Any]
    rollback: dict[str, Any]
    zero_drift: dict[str, Any]
    runtime_security_regression: dict[str, Any]
    epic17_regressions: dict[str, Any]
    epic16_regression: dict[str, Any]
    epic17_boundary: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "checks": self.checks,
            "consent": self.consent,
            "cost": self.cost,
            "data_lake": self.data_lake,
            "defects": self.defects,
            "epic": self.epic,
            "epic16_regression": self.epic16_regression,
            "epic17_boundary": self.epic17_boundary,
            "epic17_regressions": self.epic17_regressions,
            "evidence": self.evidence,
            "failed_checks": self.failed_checks,
            "failure_isolation": self.failure_isolation,
            "ingestion_activation": self.ingestion_activation,
            "inventory": self.inventory,
            "limitations": self.limitations,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "policy": self.policy,
            "privacy": self.privacy,
            "quarantine": self.quarantine,
            "register": self.register,
            "report_artifact_boundary": self.report_artifact_boundary,
            "rollback": self.rollback,
            "runtime_security_regression": self.runtime_security_regression,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "security": self.security,
            "slice": self.slice,
            "statuses": self.statuses,
            "streams": self.streams,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "writer_attachment": self.writer_attachment,
            "writer_policy": self.writer_policy,
            "zero_drift": self.zero_drift,
        }
