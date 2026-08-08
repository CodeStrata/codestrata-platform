"""Models for Slice 16.5."""

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
class RepositoryDependencyBuildCleanupReport:
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
    dependency_classification_counts: dict[str, int]
    dependencies_removed: list[str]
    dependencies_changed: list[str]
    dependency_register_relative: str
    build_authority_register_relative: str
    owner_review_items: list[str]
    deferred_dependency_items: list[str]
    security_advisories: list[dict[str, str]]
    lockfile_posture: list[dict[str, str]]
    package_root_results: list[dict[str, str]]
    dynamic_install_findings: list[dict[str, str]]
    version_authority: dict[str, str]
    release_posture: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "build_authority_register_relative": self.build_authority_register_relative,
            "checks": self.checks,
            "defects": self.defects,
            "deferred_dependency_items": self.deferred_dependency_items,
            "dependencies_changed": self.dependencies_changed,
            "dependencies_removed": self.dependencies_removed,
            "dependency_classification_counts": self.dependency_classification_counts,
            "dependency_register_relative": self.dependency_register_relative,
            "dynamic_install_findings": self.dynamic_install_findings,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "limitations": self.limitations,
            "lockfile_posture": self.lockfile_posture,
            "owner_review_items": self.owner_review_items,
            "package_id": self.package_id,
            "package_root_results": self.package_root_results,
            "package_version": self.package_version,
            "policy": self.policy,
            "release_posture": self.release_posture,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "security_advisories": self.security_advisories,
            "slice": self.slice,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "version_authority": self.version_authority,
        }
