"""Fail-closed validation for cross-repository aggregation."""

from __future__ import annotations

from collections.abc import Sequence

from codestrata_platform.intelligence_reporting.application.aggregation.indexes import (
    assert_unique_entity_refs,
    assert_unique_repositories,
)
from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    AggregatedCorrelationFact,
    AggregatedFindingFact,
    AggregatedPriorityActionFact,
    AggregatedRecommendationFact,
    AggregatedRepositoryRecord,
    AggregatedRoadmapFact,
    AggregationDenominator,
    CrossRepositoryAggregation,
)
from codestrata_platform.intelligence_reporting.application.errors import (
    AggregationInvariantError,
)
from codestrata_platform.intelligence_reporting.domain.enums import InclusionStatus
from codestrata_platform.intelligence_reporting.domain.dataset import IntelligenceDataset


def validate_aggregation(
    *,
    dataset: IntelligenceDataset,
    repositories: Sequence[AggregatedRepositoryRecord],
    finding_facts: Sequence[AggregatedFindingFact],
    recommendation_facts: Sequence[AggregatedRecommendationFact],
    priority_action_facts: Sequence[AggregatedPriorityActionFact],
    roadmap_facts: Sequence[AggregatedRoadmapFact],
    correlation_facts: Sequence[AggregatedCorrelationFact],
    denominators: Sequence[AggregationDenominator],
    assessment_index_size: int,
) -> None:
    assert_unique_repositories(repositories)
    included = set(dataset.included_repository_ids)
    for item in repositories:
        if item.repository_id not in included:
            raise AggregationInvariantError(
                f"aggregated repository {item.repository_id} is not included in dataset",
                reason_code="repository_not_in_dataset",
            )

    finding_keys = {
        (item.repository_id, item.assessment_id, item.finding_id) for item in finding_facts
    }
    recommendation_keys = {
        (item.repository_id, item.assessment_id, item.recommendation_id)
        for item in recommendation_facts
    }
    action_keys = {
        (item.repository_id, item.assessment_id, item.priority_action_id)
        for item in priority_action_facts
    }

    for item in recommendation_facts:
        for fid in item.supporting_finding_ids:
            if (item.repository_id, item.assessment_id, fid) not in finding_keys:
                raise AggregationInvariantError(
                    f"recommendation support finding missing: {fid}",
                    reason_code="unresolved_finding_ref",
                )
    for item in priority_action_facts:
        for rid in item.supporting_recommendation_ids:
            if (item.repository_id, item.assessment_id, rid) not in recommendation_keys:
                raise AggregationInvariantError(
                    f"priority action support recommendation missing: {rid}",
                    reason_code="unresolved_recommendation_ref",
                )
        for fid in item.supporting_finding_ids:
            if (item.repository_id, item.assessment_id, fid) not in finding_keys:
                raise AggregationInvariantError(
                    f"priority action support finding missing: {fid}",
                    reason_code="unresolved_finding_ref",
                )
    for item in roadmap_facts:
        for aid in item.supporting_priority_action_ids:
            if (item.repository_id, item.assessment_id, aid) not in action_keys:
                raise AggregationInvariantError(
                    f"roadmap support priority action missing: {aid}",
                    reason_code="unresolved_priority_action_ref",
                )
    for item in correlation_facts:
        for fid in item.finding_ids:
            if (item.repository_id, item.assessment_id, fid) not in finding_keys:
                raise AggregationInvariantError(
                    f"correlation finding missing: {fid}",
                    reason_code="unresolved_correlation_finding_ref",
                )

    for denom in denominators:
        if denom.denominator_count == 0 and (
            denom.ratio is not None and denom.ratio.value is not None
        ):
            raise AggregationInvariantError(
                "zero denominator cannot carry a ratio value",
                reason_code="zero_denominator_has_value",
            )

    # Excluded dataset assessments must not contribute repository facts.
    excluded_ids = {
        item.repository_id
        for item in dataset.repository_assessments
        if item.inclusion_status is not InclusionStatus.INCLUDED
    }
    for item in repositories:
        if item.repository_id in excluded_ids:
            raise AggregationInvariantError(
                "excluded repository contributed aggregation facts",
                reason_code="excluded_repository_contributed",
            )

    _ = assessment_index_size


def validate_no_embedded_reports(aggregation: CrossRepositoryAggregation) -> None:
    blob = repr(aggregation)
    for forbidden in (
        '"evidence":',
        "source_body",
        "redacted_excerpt",
        "file://",
        "/Users/",
        "BEGIN PRIVATE KEY",
    ):
        if forbidden in blob:
            raise AggregationInvariantError(
                f"aggregation contains unsafe or embedded report content: {forbidden}",
                reason_code="unsafe_or_embedded_content",
            )
