"""Models for Slice 16.4."""

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
class RepositoryAssetDesignCleanupReport:
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
    inventory_counts: dict[str, int]
    classification_counts: dict[str, int]
    authoritative_masters: list[str]
    generated_derivative_count: int
    authorized_duplicate_count: int
    stale_duplicate_count: int
    orphan_count: int
    deleted_assets: list[str]
    retained_historical_archive_count: int
    owner_review_items: list[str]
    consumer_mapping: list[dict[str, str]]
    generator_mapping: list[dict[str, str]]
    repository_residency_mapping: list[dict[str, str]]
    dependency_candidates: list[str]
    current_visual_authority: str
    asset_manifest_relative: str
    release_posture: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_manifest_relative": self.asset_manifest_relative,
            "authoritative_masters": self.authoritative_masters,
            "authorized_duplicate_count": self.authorized_duplicate_count,
            "checks": self.checks,
            "classification_counts": self.classification_counts,
            "consumer_mapping": self.consumer_mapping,
            "current_visual_authority": self.current_visual_authority,
            "defects": self.defects,
            "deleted_assets": self.deleted_assets,
            "dependency_candidates": self.dependency_candidates,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "generated_derivative_count": self.generated_derivative_count,
            "generator_mapping": self.generator_mapping,
            "inventory_counts": self.inventory_counts,
            "limitations": self.limitations,
            "orphan_count": self.orphan_count,
            "owner_review_items": self.owner_review_items,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "policy": self.policy,
            "release_posture": self.release_posture,
            "repository_residency_mapping": self.repository_residency_mapping,
            "retained_historical_archive_count": self.retained_historical_archive_count,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "stale_duplicate_count": self.stale_duplicate_count,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
        }
