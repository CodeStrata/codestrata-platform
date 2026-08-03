"""Explicit aggregation denominators — never average percentages."""

from __future__ import annotations

from collections.abc import Sequence

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    AggregatedRepositoryRecord,
    AggregationDenominator,
    DenominatorScope,
    DisabledHeadPolicy,
    IntelligenceAggregationPolicy,
    UnavailableHeadPolicy,
)
from codestrata_platform.intelligence_reporting.domain.technology import Ratio


def build_denominator(
    *,
    denominator_id: str,
    scope: DenominatorScope,
    eligible: Sequence[str],
    excluded: Sequence[str] = (),
    unavailable: Sequence[str] = (),
    limitations: Sequence[str] = (),
    numerator: int | None = None,
) -> AggregationDenominator:
    eligible_ids = tuple(sorted(set(eligible)))
    count = len(eligible_ids)
    ratio = None
    if numerator is not None:
        ratio = Ratio.of(numerator, count)
    lim = list(limitations)
    if count == 0:
        lim.append("zero_denominator_unavailable")
    return AggregationDenominator(
        denominator_id=denominator_id,
        scope=scope,
        eligible_repository_ids=eligible_ids,
        excluded_repository_ids=tuple(sorted(set(excluded))),
        unavailable_repository_ids=tuple(sorted(set(unavailable))),
        denominator_count=count,
        limitations=tuple(sorted(set(lim))),
        ratio=ratio,
    )


def build_standard_denominators(
    repositories: Sequence[AggregatedRepositoryRecord],
    *,
    policy: IntelligenceAggregationPolicy,
    assessment_head_id: str | None = None,
) -> tuple[AggregationDenominator, ...]:
    included = [item.repository_id for item in repositories]
    comparable = [item.repository_id for item in repositories if item.comparable]
    incomparable = [item.repository_id for item in repositories if not item.comparable]
    legacy = [item.repository_id for item in repositories if item.legacy_or_incomplete]

    denominators = [
        build_denominator(
            denominator_id="denom:all_included",
            scope=DenominatorScope.ALL_INCLUDED_REPOSITORIES,
            eligible=included,
        ),
        build_denominator(
            denominator_id="denom:comparable",
            scope=DenominatorScope.COMPARABLE_REPOSITORIES,
            eligible=comparable,
            excluded=incomparable,
            unavailable=legacy,
            limitations=("canonical_completeness_required",) if legacy else (),
        ),
    ]

    if assessment_head_id:
        available: list[str] = []
        activated: list[str] = []
        evaluated: list[str] = []
        disabled: list[str] = []
        unavailable_heads: list[str] = []
        for item in repositories:
            head = assessment_head_id
            if head in item.missing_heads:
                unavailable_heads.append(item.repository_id)
                continue
            if head in item.disabled_heads:
                disabled.append(item.repository_id)
                if policy.disabled_head_policy is DisabledHeadPolicy.INCLUDE_AS_DISABLED:
                    available.append(item.repository_id)
                continue
            if head in item.unavailable_heads:
                unavailable_heads.append(item.repository_id)
                if policy.unavailable_head_policy is UnavailableHeadPolicy.INCLUDE_AS_UNAVAILABLE:
                    available.append(item.repository_id)
                continue
            available.append(item.repository_id)
            if head in item.enabled_heads:
                activated.append(item.repository_id)
                evaluated.append(item.repository_id)
            else:
                # Available but not enabled — not evaluated.
                pass
        denominators.extend(
            [
                build_denominator(
                    denominator_id=f"denom:head_available:{assessment_head_id}",
                    scope=DenominatorScope.ASSESSMENT_HEAD_AVAILABLE,
                    eligible=available,
                    excluded=disabled,
                    unavailable=unavailable_heads,
                ),
                build_denominator(
                    denominator_id=f"denom:head_activated:{assessment_head_id}",
                    scope=DenominatorScope.ASSESSMENT_HEAD_ACTIVATED,
                    eligible=activated,
                    excluded=disabled,
                    unavailable=unavailable_heads,
                ),
                build_denominator(
                    denominator_id=f"denom:head_evaluated:{assessment_head_id}",
                    scope=DenominatorScope.ASSESSMENT_HEAD_EVALUATED,
                    eligible=evaluated,
                    excluded=disabled,
                    unavailable=unavailable_heads,
                ),
            ]
        )

    tech_capable = [
        item.repository_id
        for item in repositories
        if "technology_inventory" in item.enabled_heads
        or "technology_inventory" in item.disabled_heads
        or not item.legacy_or_incomplete
    ]
    denominators.append(
        build_denominator(
            denominator_id="denom:technology_inventory_available",
            scope=DenominatorScope.TECHNOLOGY_INVENTORY_AVAILABLE,
            eligible=tech_capable,
            unavailable=[item.repository_id for item in repositories if item.legacy_or_incomplete],
        )
    )
    return tuple(denominators)
