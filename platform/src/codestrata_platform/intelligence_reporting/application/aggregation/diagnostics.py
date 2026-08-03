"""Structured aggregation diagnostics — no narrative conclusions."""

from __future__ import annotations

from collections.abc import Sequence

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    AggregatedRepositoryRecord,
    AggregationDenominator,
    AggregationDiagnostics,
)
from codestrata_platform.intelligence_reporting.domain.technology import Ratio


def build_diagnostics(
    *,
    repositories: Sequence[AggregatedRepositoryRecord],
    excluded_repository_count: int,
    technology_fact_count: int,
    finding_fact_count: int,
    recommendation_fact_count: int,
    priority_action_fact_count: int,
    roadmap_fact_count: int,
    correlation_fact_count: int,
    unresolved_reference_count: int,
    duplicate_reference_count: int,
    denominators: Sequence[AggregationDenominator],
    limitations: Sequence[str],
) -> AggregationDiagnostics:
    unavailable_denominators = sum(
        1
        for item in denominators
        if item.denominator_count == 0
        or (item.ratio is not None and item.ratio.status.value == "unavailable")
    )
    return AggregationDiagnostics(
        included_repository_count=len(repositories),
        excluded_repository_count=excluded_repository_count,
        legacy_repository_count=sum(1 for item in repositories if item.legacy_or_incomplete),
        comparable_repository_count=sum(1 for item in repositories if item.comparable),
        technology_fact_count=technology_fact_count,
        finding_fact_count=finding_fact_count,
        recommendation_fact_count=recommendation_fact_count,
        priority_action_fact_count=priority_action_fact_count,
        roadmap_fact_count=roadmap_fact_count,
        correlation_fact_count=correlation_fact_count,
        unresolved_reference_count=unresolved_reference_count,
        duplicate_reference_count=duplicate_reference_count,
        unavailable_denominator_count=unavailable_denominators,
        limitations=tuple(sorted(set(limitations))),
    )


def technology_presence_ratio(
    *,
    repository_ids_with_tech: Sequence[str],
    denominator: AggregationDenominator,
) -> Ratio:
    """Repository presence ratio — distinct repos, never occurrence/repo average."""

    present = sorted(set(repository_ids_with_tech) & set(denominator.eligible_repository_ids))
    return Ratio.of(len(present), denominator.denominator_count)
