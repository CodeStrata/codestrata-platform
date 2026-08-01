"""Validation summary artifact contract (Epic 4 Slice 4.12).

Cross-repository engineering summary built only from Slice 4.11
``RepositoryValidationRecord`` artifacts. Separate from assessment schema 1.2
and record schema 1.0.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

SUMMARY_SCHEMA_VERSION = "1.0"
SUPPORTED_RECORD_SCHEMA_VERSION = "1.0"

CANONICAL_PACKS: tuple[str, ...] = (
    "technology_inventory",
    "security",
    "architecture",
    "technical_debt",
    "dependency",
    "cloud",
    "ai_readiness",
    "modernization",
)

DISCLAIMER = (
    "These results describe only the repositories and controlled fixtures included "
    "in this validation set. They are not a product-wide accuracy claim."
)


class SummaryScope(str, Enum):
    """How source records were selected."""

    LATEST_PER_REPOSITORY = "latest-per-repository"
    EXPLICIT_RUN_IDS = "explicit-run-ids"
    FILTERED_LATEST = "filtered-latest"


class OverallVerdict(str, Enum):
    """Deterministic suite-level verdict over selected records."""

    ERROR = "ERROR"
    FAIL = "FAIL"
    PASS = "PASS"
    SKIPPED = "SKIPPED"


class VerdictTotals(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0


class ExpectationTotals(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluated: int = 0
    matched: int = 0
    mismatched: int = 0
    # Repositories that contributed zero evaluated expectations (ERROR/SKIP without compare).
    repositories_without_evaluation: int = 0


class SourceRecordRef(BaseModel):
    """Records-root-relative pointer to a Slice 4.11 record."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_id: str
    run_id: str
    relative_path: str  # e.g. local-sample-js/latest/record.json

    @field_validator("relative_path")
    @classmethod
    def _reject_absolute(cls, value: str) -> str:
        _reject_unsafe_path(value)
        return value.replace("\\", "/")


class RepositorySummaryRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_id: str
    run_id: str
    verdict: str
    source_identity: str | None = None
    expectations_evaluated: int = 0
    expectations_matched: int = 0
    mismatch_count: int = 0
    pack_precision: tuple[dict[str, Any], ...] = ()
    error_message: str | None = None
    skip_reason: str | None = None
    source_record: SourceRecordRef
    assessment_artifact_names: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    assessment_schema_version: str | None = None
    ai_executed: bool = False


class PackAggregateSummary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    pack: str
    repositories_evaluated: int = 0
    repositories_passed: int = 0
    repositories_failed: int = 0
    repositories_unavailable: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    limitations: tuple[str, ...] = ()
    source_repository_ids: tuple[str, ...] = ()


class MismatchSummaryEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_id: str
    assessment_area: str
    expectation: str
    actual: str
    diagnostic: str
    source_record: SourceRecordRef


class CoverageGap(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    gap_id: str
    category: str
    description: str
    related_packs: tuple[str, ...] = ()
    related_repositories: tuple[str, ...] = ()
    derived_from: str  # records | matrix | registry


class ValidationSummaryArtifact(BaseModel):
    """Permanent cross-repository validation summary (Slice 4.12)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    summary_schema_version: str = SUMMARY_SCHEMA_VERSION
    generated_from_record_schema_version: str = SUPPORTED_RECORD_SCHEMA_VERSION
    summary_run_id: str
    scope: SummaryScope
    scope_label: str
    repository_count: int = 0
    repositories: tuple[RepositorySummaryRow, ...] = ()
    verdict_totals: VerdictTotals = Field(default_factory=VerdictTotals)
    expectation_totals: ExpectationTotals = Field(default_factory=ExpectationTotals)
    mismatch_totals: int = 0
    mismatches_by_area: dict[str, int] = Field(default_factory=dict)
    mismatches: tuple[MismatchSummaryEntry, ...] = ()
    pack_precision: tuple[PackAggregateSummary, ...] = ()
    unavailable_metrics: tuple[str, ...] = ()
    coverage_gaps: tuple[CoverageGap, ...] = ()
    source_record_refs: tuple[SourceRecordRef, ...] = ()
    overall_verdict: OverallVerdict
    limitations: tuple[str, ...] = ()
    disclaimer: str = DISCLAIMER
    # Volatile operator metadata — excluded from deterministic equivalence helpers.
    generated_at: str | None = None

    def canonical_dict(self) -> dict[str, Any]:
        """JSON-ready payload with volatile fields removed for equivalence checks."""

        payload = self.model_dump(mode="json")
        payload.pop("generated_at", None)
        return payload


def _reject_unsafe_path(value: str) -> None:
    cleaned = value.strip().replace("\\", "/")
    if not cleaned:
        raise ValueError("empty path reference")
    if cleaned.startswith("/"):
        raise ValueError(f"absolute path rejected: {value!r}")
    if len(cleaned) >= 3 and cleaned[1] == ":" and cleaned[0].isalpha():
        raise ValueError(f"absolute path rejected: {value!r}")
    lowered = cleaned.lower()
    if lowered.startswith("users/") or "/users/" in lowered:
        raise ValueError(f"unsafe absolute-style path rejected: {value!r}")
    if lowered.startswith("home/") or "/home/" in lowered:
        raise ValueError(f"unsafe absolute-style path rejected: {value!r}")
