"""Models for Slice 16.1 repository inventory verification."""

from __future__ import annotations

from dataclasses import dataclass, field
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
class InventoryEntry:
    path: str
    area: str
    kind: str
    classification: str
    notes: str = ""
    secondary_classifications: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "area": self.area,
            "classification": self.classification,
            "kind": self.kind,
            "path": self.path,
        }
        if self.notes:
            d["notes"] = self.notes
        if self.secondary_classifications:
            d["secondary_classifications"] = list(self.secondary_classifications)
        return d


@dataclass(slots=True)
class RepositoryInventoryReport:
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
    inventory_summary: dict[str, Any]
    classification_counts: dict[str, int]
    area_counts: dict[str, int]
    duplicate_candidates: list[str]
    stale_candidates: list[str]
    delete_candidates: list[str]
    archive_candidates: list[str]
    owner_review_items: list[str]
    special_audits: dict[str, Any]
    entries: list[dict[str, Any]]
    release_posture: dict[str, Any]
    statuses: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "area_counts": self.area_counts,
            "archive_candidates": self.archive_candidates,
            "checks": self.checks,
            "classification_counts": self.classification_counts,
            "defects": self.defects,
            "delete_candidates": self.delete_candidates,
            "duplicate_candidates": self.duplicate_candidates,
            "entries": self.entries,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "inventory_summary": self.inventory_summary,
            "limitations": self.limitations,
            "owner_review_items": self.owner_review_items,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "policy": self.policy,
            "release_posture": self.release_posture,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "special_audits": self.special_audits,
            "stale_candidates": self.stale_candidates,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
        }
