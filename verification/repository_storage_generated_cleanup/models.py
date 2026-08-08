"""Models for Slice 16.6."""

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
class RepositoryStorageGeneratedCleanupReport:
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
    classification_counts: dict[str, int]
    removed_artifacts: list[str]
    retained_protected: list[str]
    owner_review_items: list[str]
    sqlite_classifications: list[dict[str, str]]
    recreation_results: list[dict[str, str]]
    gitignore_posture: list[dict[str, str]]
    worktree_hygiene: dict[str, Any]
    artifact_register_relative: str
    release_posture: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_register_relative": self.artifact_register_relative,
            "checks": self.checks,
            "classification_counts": self.classification_counts,
            "defects": self.defects,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "gitignore_posture": self.gitignore_posture,
            "limitations": self.limitations,
            "owner_review_items": self.owner_review_items,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "policy": self.policy,
            "recreation_results": self.recreation_results,
            "release_posture": self.release_posture,
            "removed_artifacts": self.removed_artifacts,
            "retained_protected": self.retained_protected,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "sqlite_classifications": self.sqlite_classifications,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "worktree_hygiene": self.worktree_hygiene,
        }
