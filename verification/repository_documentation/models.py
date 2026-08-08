"""Models for Slice 16.2 documentation verification."""

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
class DocEntry:
    path: str
    classification: str
    notes: str = ""
    secondary: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "classification": self.classification,
            "path": self.path,
        }
        if self.notes:
            d["notes"] = self.notes
        if self.secondary:
            d["secondary"] = list(self.secondary)
        return d


@dataclass(slots=True)
class RepositoryDocumentationReport:
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
    documentation_inventory: list[dict[str, Any]]
    classification_counts: dict[str, int]
    duplicates: list[str]
    broken_links: list[str]
    owner_review_items: list[str]
    archive_candidates: list[str]
    delete_candidates: list[str]
    documentation_hierarchy: dict[str, Any]
    authoritative_document_registry: dict[str, str]
    release_posture: dict[str, Any]
    statuses: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "archive_candidates": self.archive_candidates,
            "authoritative_document_registry": self.authoritative_document_registry,
            "broken_links": self.broken_links,
            "checks": self.checks,
            "classification_counts": self.classification_counts,
            "defects": self.defects,
            "delete_candidates": self.delete_candidates,
            "documentation_hierarchy": self.documentation_hierarchy,
            "documentation_inventory": self.documentation_inventory,
            "duplicates": self.duplicates,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "limitations": self.limitations,
            "owner_review_items": self.owner_review_items,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "policy": self.policy,
            "release_posture": self.release_posture,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
        }
