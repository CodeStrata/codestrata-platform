"""Validation harness data models."""

from __future__ import annotations

import re
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validation.finding_correlations.expectations import FindingCorrelationExpectation
from validation.finding_severity.expectations import FindingSeverityExpectation
from validation.inventory import TechnologyInventoryExpectation
from validation.security import SecurityExpectation, SecurityFindingActual
from validation.architecture import (
    ArchitectureExpectation,
    ArchitectureFindingActual,
    ArchitectureGraphActual,
)
from validation.technical_debt import (
    TechnicalDebtExpectation,
    TechnicalDebtFindingActual,
)
from validation.dependency import (
    DependencyExpectation,
    DependencyFindingActual,
    DependencyManifestActual,
)
from validation.cloud import (
    CloudExpectation,
    CloudFindingActual,
    CloudRecommendationActual,
    CloudSignalActual,
)
from validation.ai_readiness import (
    AiReadinessExpectation,
    AiReadinessFindingActual,
    AiReadinessRecommendationActual,
    AiReadinessSignalActual,
)
from validation.modernization import (
    ModernizationExpectation,
    ModernizationPriorityActionActual,
    ModernizationRecommendationActual,
    ModernizationRoadmapInitiativeActual,
)

_FLOATING_REFS = frozenset({"main", "master", "HEAD", "head", "develop", "trunk"})
_COMMIT_SHA_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
_REPO_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")


class RepositorySourceType(StrEnum):
    LOCAL = "local"
    REMOTE = "remote"


class ValidationVerdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


class CountRange(BaseModel):
    """Inclusive integer range for expectation counts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    minimum: int | None = Field(default=None, ge=0)
    maximum: int | None = Field(default=None, ge=0)
    exact: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_range(self) -> CountRange:
        if self.exact is not None and (self.minimum is not None or self.maximum is not None):
            raise ValueError("exact cannot be combined with minimum/maximum")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("minimum cannot exceed maximum")
        if self.exact is None and self.minimum is None and self.maximum is None:
            raise ValueError("count range requires exact, minimum, and/or maximum")
        return self

    def contains(self, value: int) -> bool:
        if self.exact is not None:
            return value == self.exact
        if self.minimum is not None and value < self.minimum:
            return False
        if self.maximum is not None and value > self.maximum:
            return False
        return True

    def describe(self) -> str:
        if self.exact is not None:
            return f"exact={self.exact}"
        parts: list[str] = []
        if self.minimum is not None:
            parts.append(f"min={self.minimum}")
        if self.maximum is not None:
            parts.append(f"max={self.maximum}")
        return ",".join(parts)


class ExpectedResults(BaseModel):
    """Flexible expected-result contract for one validation repository.

    Every field is optional so later pack-specific validators can declare only
    what they care about. Contradictory required/forbidden sets are rejected.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str | None = None
    expected_assessment_status: str | None = None
    expected_coverage_states: tuple[str, ...] = ()
    expected_limitations: tuple[str, ...] = ()
    forbidden_limitations: tuple[str, ...] = ()

    technology_facts_expected: tuple[str, ...] = ()
    technology_facts_forbidden: tuple[str, ...] = ()
    technology_inventory: TechnologyInventoryExpectation | None = None
    security: SecurityExpectation | None = None
    architecture: ArchitectureExpectation | None = None
    technical_debt: TechnicalDebtExpectation | None = None
    dependency: DependencyExpectation | None = None
    cloud: CloudExpectation | None = None
    ai_readiness: AiReadinessExpectation | None = None
    modernization: ModernizationExpectation | None = None
    # Additive Slice 5.12 — optional required/forbidden correlation pairs.
    finding_correlations: FindingCorrelationExpectation | None = None
    # Additive Slice 5.13 — optional severity constraints by rule-prefix.
    finding_severity: FindingSeverityExpectation | None = None

    expected_finding_rule_ids: tuple[str, ...] = ()
    forbidden_finding_rule_ids: tuple[str, ...] = ()
    finding_count: CountRange | None = None
    maximum_allowed_false_positives: int | None = Field(default=None, ge=0)
    minimum_required_detections: int | None = Field(default=None, ge=0)

    expected_recommendation_ids: tuple[str, ...] = ()
    forbidden_recommendation_ids: tuple[str, ...] = ()
    expected_recommendation_categories: tuple[str, ...] = ()
    recommendation_count: CountRange | None = None

    expected_priority_action_categories: tuple[str, ...] = ()
    expected_roadmap_phases: tuple[str, ...] = ()

    expected_evidence_paths: tuple[str, ...] = ()
    forbidden_evidence_paths: tuple[str, ...] = ()

    expected_assessment_heads: tuple[str, ...] = ()
    expected_artifacts: tuple[str, ...] = ()
    expect_ai_executed: bool | None = False

    notes: str | None = None

    @model_validator(mode="after")
    def _reject_contradictions(self) -> ExpectedResults:
        _reject_overlap(
            self.technology_facts_expected,
            self.technology_facts_forbidden,
            area="technology_facts",
        )
        _reject_overlap(
            self.expected_finding_rule_ids,
            self.forbidden_finding_rule_ids,
            area="finding_rule_ids",
        )
        _reject_overlap(
            self.expected_recommendation_ids,
            self.forbidden_recommendation_ids,
            area="recommendation_ids",
        )
        _reject_overlap(
            self.expected_evidence_paths,
            self.forbidden_evidence_paths,
            area="evidence_paths",
        )
        _reject_overlap(
            self.expected_limitations,
            self.forbidden_limitations,
            area="limitations",
        )
        return self


class ValidationRepository(BaseModel):
    """Definition of one repository under validation harness control."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_id: str
    display_name: str
    source_type: RepositorySourceType
    local_path: str | None = None
    remote_url: str | None = None
    pinned_ref: str | None = None
    expected_commit: str | None = None
    assessment_config: str | None = None
    enabled_packs: tuple[str, ...] = ()
    expected_results_path: str
    tags: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    notes: str | None = None
    enabled: bool = True

    @field_validator("repository_id")
    @classmethod
    def _stable_id(cls, value: str) -> str:
        if not _REPO_ID_RE.match(value):
            raise ValueError(
                "repository_id must be lowercase alphanumeric with _/- "
                f"(2–64 chars), got {value!r}"
            )
        return value

    @field_validator("local_path")
    @classmethod
    def _relative_local_path(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if Path(value).is_absolute():
            raise ValueError(
                "local_path must be repository-relative to the validation root; "
                f"absolute paths are rejected: {value!r}"
            )
        return value

    @field_validator("expected_commit")
    @classmethod
    def _commit_shape(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not _COMMIT_SHA_RE.match(value):
            raise ValueError(f"expected_commit must be a 7–40 hex SHA, got {value!r}")
        return value.lower()

    @field_validator("remote_url")
    @classmethod
    def _no_embedded_credentials(cls, value: str | None) -> str | None:
        if value is None:
            return value
        lowered = value.lower()
        host = value.split("://", 1)[-1].split("/", 1)[0]
        if "@" in host:
            raise ValueError("remote_url must not embed credentials")
        if "token=" in lowered or "password=" in lowered:
            raise ValueError("remote_url must not embed credentials")
        return value

    @model_validator(mode="after")
    def _source_rules(self) -> ValidationRepository:
        if self.source_type == RepositorySourceType.LOCAL:
            if not self.local_path:
                raise ValueError("local repositories require local_path")
            if self.remote_url:
                raise ValueError("local repositories must not set remote_url")
        elif self.source_type == RepositorySourceType.REMOTE:
            if not self.remote_url:
                raise ValueError("remote repositories require remote_url")
            if not self.pinned_ref:
                raise ValueError("remote repositories require pinned_ref")
            if self.pinned_ref.strip() in _FLOATING_REFS:
                raise ValueError(
                    "floating branch references (main/master/HEAD/develop) are "
                    f"prohibited for release validation; got pinned_ref={self.pinned_ref!r}"
                )
            if self.local_path:
                raise ValueError("remote repositories must not set local_path")
        if not self.expected_results_path or Path(self.expected_results_path).is_absolute():
            raise ValueError(
                "expected_results_path must be a non-empty path relative to the validation root"
            )
        return self


class ActualAssessmentResult(BaseModel):
    """Normalized assessment outputs used for comparison.

    Does not include source code bodies. Absolute paths are runtime-only and
    must be relativized before any committed summary artifact.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str | None = None
    assessment_status: str | None = None
    technologies: tuple[str, ...] = ()
    repository_facts: tuple[str, ...] = ()
    evidence_paths: tuple[str, ...] = ()
    finding_rule_ids: tuple[str, ...] = ()
    finding_ids: tuple[str, ...] = ()
    findings_count: int = 0
    recommendation_ids: tuple[str, ...] = ()
    recommendation_categories: tuple[str, ...] = ()
    recommendations_count: int = 0
    priority_action_categories: tuple[str, ...] = ()
    roadmap_phases: tuple[str, ...] = ()
    coverage_states: tuple[str, ...] = ()
    confidence: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    execution_warnings: tuple[str, ...] = ()
    assessment_heads: tuple[str, ...] = ()
    technologies_by_category: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    technology_versions: dict[str, str | None] = Field(default_factory=dict)
    dependency_ecosystems: tuple[str, ...] = ()
    application_indicators: tuple[str, ...] = ()
    repository_composition_facts: tuple[str, ...] = ()
    security_findings: tuple[SecurityFindingActual, ...] = ()
    architecture_findings: tuple[ArchitectureFindingActual, ...] = ()
    architecture_graph: ArchitectureGraphActual | None = None
    technical_debt_findings: tuple[TechnicalDebtFindingActual, ...] = ()
    dependency_findings: tuple[DependencyFindingActual, ...] = ()
    dependency_manifests: tuple[DependencyManifestActual, ...] = ()
    cloud_findings: tuple[CloudFindingActual, ...] = ()
    cloud_signals: tuple[CloudSignalActual, ...] = ()
    cloud_recommendations: tuple[CloudRecommendationActual, ...] = ()
    ai_readiness_findings: tuple[AiReadinessFindingActual, ...] = ()
    ai_readiness_signals: tuple[AiReadinessSignalActual, ...] = ()
    ai_readiness_recommendations: tuple[AiReadinessRecommendationActual, ...] = ()
    modernization_recommendations: tuple[ModernizationRecommendationActual, ...] = ()
    modernization_priority_actions: tuple[ModernizationPriorityActionActual, ...] = ()
    modernization_roadmap_initiatives: tuple[ModernizationRoadmapInitiativeActual, ...] = ()
    # Additive Slice 5.12 — stable rule-pair keys from finding_correlations.
    finding_correlation_pairs: tuple[str, ...] = ()
    artifact_paths: dict[str, str] = Field(default_factory=dict)
    assessment_duration_ms: float | None = None
    ai_executed: bool = False
    report_document: dict[str, Any] = Field(default_factory=dict)
    # ACTIVE_0_2_0_RELEASE_GATE: "manifest_0_2_0" means on-disk assessment.json
    # is the lightweight manifest (not legacy full report.json).
    persisted_layout: str = "full_report_json"


class ComparisonMismatch(BaseModel):
    """One expectation mismatch with repository- and area-specific diagnostics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_id: str
    assessment_area: str
    expectation: str
    actual: str
    artifact_path: str | None = None
    diagnostic: str


class PackPrecisionRecord(BaseModel):
    """Compact precision/recall snapshot for one pack validator (Slice 4.11).

    Slices 5.7–5.8 add optional canonical PrecisionMetric / RecallMetric
    projection fields while retaining schema 1.0 compatibility (additive only).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    pack: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ambiguous: int = 0
    precision: float | None = None
    recall: float | None = None
    passed: bool | None = None
    # Additive Slice 5.7 — older records omit these and remain readable.
    precision_metric: dict[str, Any] | None = None
    precision_metric_id: str | None = None
    precision_availability: str | None = None
    precision_classification_status: str | None = None
    sample: dict[str, Any] | None = None
    # Additive Slice 5.8
    recall_metric: dict[str, Any] | None = None
    recall_metric_id: str | None = None
    recall_availability: str | None = None
    recall_classification_status: str | None = None
    recall_sample: dict[str, Any] | None = None


class ComparisonOutcome(BaseModel):
    """Full comparison result from ``compare_actual_to_expected``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mismatches: tuple[ComparisonMismatch, ...] = ()
    expectations_evaluated: int = 0
    expectations_matched: int = 0
    pack_precision: tuple[PackPrecisionRecord, ...] = ()
    # Additive Slice 5.9 — serialized FalsePositiveRecord dicts (schema 1.0 compatible).
    false_positives: tuple[dict[str, Any], ...] = ()
    # Additive Slice 5.10 — serialized FalseNegativeRecord dicts.
    false_negatives: tuple[dict[str, Any], ...] = ()

    def as_tuple(self) -> tuple[tuple[ComparisonMismatch, ...], int, int]:
        return self.mismatches, self.expectations_evaluated, self.expectations_matched


class ValidationRunResult(BaseModel):
    """Outcome for one repository validation run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_id: str
    verdict: ValidationVerdict
    mismatches: tuple[ComparisonMismatch, ...] = ()
    error_message: str | None = None
    skip_reason: str | None = None
    duration_ms: float | None = None
    artifact_dir: str | None = None
    record_dir: str | None = None
    expectations_evaluated: int = 0
    expectations_matched: int = 0
    ai_executed: bool = False


class ValidationSummary(BaseModel):
    """In-memory / minimal JSON summary across repositories."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_repositories: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    total_expectations: int = 0
    matched_expectations: int = 0
    mismatches_by_area: dict[str, int] = Field(default_factory=dict)
    repository_durations_ms: dict[str, float] = Field(default_factory=dict)
    artifact_locations: dict[str, str] = Field(default_factory=dict)
    results: tuple[ValidationRunResult, ...] = ()


def _reject_overlap(
    required: tuple[str, ...],
    forbidden: tuple[str, ...],
    *,
    area: str,
) -> None:
    overlap = sorted(set(required) & set(forbidden))
    if overlap:
        raise ValueError(f"contradictory {area} expectations: {overlap}")
