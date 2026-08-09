"""Models for Slice 17.2."""

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
class CommunityCloudRemoteStateReport:
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
    recovery_classification: str
    forensic_audit: dict[str, Any]
    policy: dict[str, Any]
    register: dict[str, Any]
    aws_identity: dict[str, Any]
    bucket: dict[str, Any]
    backend: dict[str, Any]
    epic17_boundary: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "aws_identity": self.aws_identity,
            "backend": self.backend,
            "bucket": self.bucket,
            "checks": self.checks,
            "defects": self.defects,
            "epic": self.epic,
            "epic17_boundary": self.epic17_boundary,
            "failed_checks": self.failed_checks,
            "forensic_audit": self.forensic_audit,
            "limitations": self.limitations,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "policy": self.policy,
            "recovery_classification": self.recovery_classification,
            "register": self.register,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
        }
