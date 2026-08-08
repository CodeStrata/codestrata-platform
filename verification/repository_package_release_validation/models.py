"""Models for Slice 16.9."""

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
class RepositoryPackageReleaseValidationReport:
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
    export_validation: dict[str, Any]
    standalone_package_validation: dict[str, Any]
    standalone_build_validation: dict[str, Any]
    release_artifact_validation: dict[str, Any]
    public_repository_readiness: dict[str, Any]
    security_validation: dict[str, Any]
    determinism: dict[str, Any]
    repository_inventory: list[dict[str, str]]
    release_posture: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "checks": self.checks,
            "defects": self.defects,
            "determinism": self.determinism,
            "epic": self.epic,
            "export_validation": self.export_validation,
            "failed_checks": self.failed_checks,
            "limitations": self.limitations,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "policy": self.policy,
            "public_repository_readiness": self.public_repository_readiness,
            "release_artifact_validation": self.release_artifact_validation,
            "release_posture": self.release_posture,
            "repository_inventory": self.repository_inventory,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "security_validation": self.security_validation,
            "slice": self.slice,
            "standalone_build_validation": self.standalone_build_validation,
            "standalone_package_validation": self.standalone_package_validation,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
        }
