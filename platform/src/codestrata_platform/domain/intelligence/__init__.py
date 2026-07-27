"""Assessment intelligence aggregate for normalized findings and metrics."""

from __future__ import annotations

from codestrata_platform.domain.intelligence.aggregate import AssessmentIntelligence
from codestrata_platform.domain.intelligence.enums import (
    FindingCategory,
    FindingSeverity,
    FindingStatus,
    IntelligenceIngestionStatus,
    MetricValueKind,
    RecommendationPriority,
    RecommendationStatus,
)
from codestrata_platform.domain.intelligence.ids import (
    AssessmentIntelligenceId,
    EvidenceReferenceId,
    FindingId,
    RecommendationId,
)
from codestrata_platform.domain.intelligence.ports import (
    AssessmentArtifactReader,
    AssessmentIntelligenceRepository,
    CompletedArtifactContent,
    FindingRepository,
    MetricRepository,
    RecommendationRepository,
)
from codestrata_platform.domain.intelligence.value_objects import (
    EvidenceReference,
    Finding,
    IntelligenceSchemaVersion,
    Metric,
    MetricName,
    MetricValue,
    Recommendation,
)

__all__ = [
    "AssessmentArtifactReader",
    "AssessmentIntelligence",
    "AssessmentIntelligenceId",
    "AssessmentIntelligenceRepository",
    "CompletedArtifactContent",
    "EvidenceReference",
    "EvidenceReferenceId",
    "Finding",
    "FindingCategory",
    "FindingId",
    "FindingRepository",
    "FindingSeverity",
    "FindingStatus",
    "IntelligenceIngestionStatus",
    "IntelligenceSchemaVersion",
    "Metric",
    "MetricName",
    "MetricRepository",
    "MetricValue",
    "MetricValueKind",
    "Recommendation",
    "RecommendationId",
    "RecommendationPriority",
    "RecommendationRepository",
    "RecommendationStatus",
]
