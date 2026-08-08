"""Models for Slice 16.3."""

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
class RepositoryCodeCleanupReport:
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
    cleanup_register: list[dict[str, Any]]
    classification_counts: dict[str, int]
    residency_register: list[dict[str, Any]]
    dependency_candidates: list[str]
    owner_review_items: list[str]
    removed_paths: list[str]
    removed_symbols: list[dict[str, str]]
    release_posture: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "checks": self.checks,
            "classification_counts": self.classification_counts,
            "cleanup_register": self.cleanup_register,
            "defects": self.defects,
            "dependency_candidates": self.dependency_candidates,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "limitations": self.limitations,
            "owner_review_items": self.owner_review_items,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "policy": self.policy,
            "release_posture": self.release_posture,
            "removed_paths": self.removed_paths,
            "removed_symbols": self.removed_symbols,
            "residency_register": self.residency_register,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
        }
