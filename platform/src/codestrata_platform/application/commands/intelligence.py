"""Assessment intelligence application commands."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.intelligence.ids import AssessmentIntelligenceId


@dataclass(frozen=True, slots=True)
class RegisterAssessmentIntelligenceCommand:
    assessment_id: AssessmentId
    engine_assessment_id: str
    source_artifact_ids: tuple[str, ...]
    parser_version: str = "1.0.0"


@dataclass(frozen=True, slots=True)
class BeginIntelligenceIngestionCommand:
    intelligence_id: AssessmentIntelligenceId


@dataclass(frozen=True, slots=True)
class CompleteIntelligenceIngestionCommand:
    intelligence_id: AssessmentIntelligenceId


@dataclass(frozen=True, slots=True)
class FailIntelligenceIngestionCommand:
    intelligence_id: AssessmentIntelligenceId
    reason: str
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class UpsertFindingsCommand:
    intelligence_id: AssessmentIntelligenceId
    finding_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class UpsertMetricsCommand:
    intelligence_id: AssessmentIntelligenceId
    metric_names: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class UpsertRecommendationsCommand:
    intelligence_id: AssessmentIntelligenceId
    recommendation_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProcessAssessmentIntelligenceCommand:
    """Process completed artifacts into normalized assessment intelligence.

    Revision / idempotency model:
    ``SHA-256(sorted artifact_id:checksum + parser_version)``.
    Same key + COMPLETED returns the existing ingestion (idempotent).
    A different key creates revision N+1 and marks prior COMPLETED rows SUPERSEDED.
    """

    assessment_id: AssessmentId
    artifact_ids: tuple[str, ...] | None = None
    parser_version: str = "1.0.0"
