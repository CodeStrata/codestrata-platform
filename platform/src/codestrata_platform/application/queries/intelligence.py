"""Assessment intelligence application queries."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.intelligence.enums import FindingSeverity
from codestrata_platform.domain.intelligence.ids import (
    AssessmentIntelligenceId,
    FindingId,
    RecommendationId,
)


@dataclass(frozen=True, slots=True)
class GetAssessmentIntelligenceQuery:
    intelligence_id: AssessmentIntelligenceId


@dataclass(frozen=True, slots=True)
class GetLatestAssessmentIntelligenceQuery:
    assessment_id: AssessmentId


@dataclass(frozen=True, slots=True)
class ListAssessmentFindingsQuery:
    assessment_id: AssessmentId
    severity: FindingSeverity | None = None


@dataclass(frozen=True, slots=True)
class ListAssessmentMetricsQuery:
    assessment_id: AssessmentId


@dataclass(frozen=True, slots=True)
class ListAssessmentRecommendationsQuery:
    assessment_id: AssessmentId


@dataclass(frozen=True, slots=True)
class GetFindingQuery:
    finding_id: FindingId


@dataclass(frozen=True, slots=True)
class GetRecommendationQuery:
    recommendation_id: RecommendationId
