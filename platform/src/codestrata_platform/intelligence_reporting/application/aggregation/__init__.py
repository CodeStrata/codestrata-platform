"""Cross-repository aggregation foundation (Platform-only).

This aggregation layer produces factual cross-repository inputs. It does not
create recurring-pattern conclusions, portfolio recommendations, or industry
benchmarks.
"""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.aggregation.aggregate_dataset import (
    aggregate_intelligence_dataset,
    build_aggregation_id,
)
from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    AggregateCounts,
    AggregatedAssessmentHeadFact,
    AggregatedConfidenceFact,
    AggregatedCorrelationFact,
    AggregatedCoverageFact,
    AggregatedEntityRef,
    AggregatedFindingFact,
    AggregatedPriorityActionFact,
    AggregatedRecommendationFact,
    AggregatedRepositoryRecord,
    AggregatedRoadmapFact,
    AggregatedTechnologyFact,
    AggregationDenominator,
    AggregationDiagnostics,
    CrossRepositoryAggregation,
    DenominatorScope,
    IntelligenceAggregationPolicy,
    LegacyAssessmentPolicy,
    VisibilityAggregationScope,
)

__all__ = [
    "AggregateCounts",
    "AggregatedAssessmentHeadFact",
    "AggregatedConfidenceFact",
    "AggregatedCorrelationFact",
    "AggregatedCoverageFact",
    "AggregatedEntityRef",
    "AggregatedFindingFact",
    "AggregatedPriorityActionFact",
    "AggregatedRecommendationFact",
    "AggregatedRepositoryRecord",
    "AggregatedRoadmapFact",
    "AggregatedTechnologyFact",
    "AggregationDenominator",
    "AggregationDiagnostics",
    "CrossRepositoryAggregation",
    "DenominatorScope",
    "IntelligenceAggregationPolicy",
    "LegacyAssessmentPolicy",
    "VisibilityAggregationScope",
    "aggregate_intelligence_dataset",
    "build_aggregation_id",
]
