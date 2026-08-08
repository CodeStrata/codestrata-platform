"""Models for Slice 16.7."""

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
class RepositoryBoundaryResidencyReport:
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
    residency_map_relative: str
    platform_register_relative: str
    residency_status_counts: dict[str, int]
    platform_classification_counts: dict[str, int]
    visibility_map: list[dict[str, str]]
    owner_review_items: list[str]
    import_boundary_results: list[dict[str, str]]
    export_boundary_results: list[dict[str, str]]
    files_moved: list[str]
    files_removed: list[str]
    release_posture: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "checks": self.checks,
            "defects": self.defects,
            "epic": self.epic,
            "export_boundary_results": self.export_boundary_results,
            "failed_checks": self.failed_checks,
            "files_moved": self.files_moved,
            "files_removed": self.files_removed,
            "import_boundary_results": self.import_boundary_results,
            "limitations": self.limitations,
            "owner_review_items": self.owner_review_items,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "platform_classification_counts": self.platform_classification_counts,
            "platform_register_relative": self.platform_register_relative,
            "policy": self.policy,
            "release_posture": self.release_posture,
            "residency_map_relative": self.residency_map_relative,
            "residency_status_counts": self.residency_status_counts,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "visibility_map": self.visibility_map,
        }
