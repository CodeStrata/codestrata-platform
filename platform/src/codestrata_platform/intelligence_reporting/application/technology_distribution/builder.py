"""Build TechnologyDistribution from CrossRepositoryAggregation."""

from __future__ import annotations

from collections.abc import Sequence

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    CrossRepositoryAggregation,
    DenominatorScope,
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution.diagnostics import (
    TechnologyDistributionDiagnostics,
    TechnologyDistributionPolicy,
    TechnologyDistributionResult,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution.grouping import (
    group_technology_facts,
    weakest_confidence,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution.validation import (
    validate_distribution,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    DataVisibility,
    VersionState,
)
from codestrata_platform.intelligence_reporting.domain.report import EngineeringIntelligenceReport
from codestrata_platform.intelligence_reporting.domain.technology import (
    Ratio,
    TechnologyCategoryDistribution,
    TechnologyDistribution,
    TechnologyDistributionObservation,
    TechnologyVersionObservation,
)


def resolve_technology_denominator(
    aggregation: CrossRepositoryAggregation,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    """Prefer technology-inventory denominator; fall back to all included."""

    for denom in aggregation.denominators:
        if denom.scope is DenominatorScope.TECHNOLOGY_INVENTORY_AVAILABLE:
            return (
                denom.eligible_repository_ids,
                denom.unavailable_repository_ids,
                denom.denominator_count,
            )
    included = tuple(sorted(item.repository_id for item in aggregation.repository_index))
    return included, (), len(included)


def build_technology_distribution(
    aggregation: CrossRepositoryAggregation,
    *,
    policy: TechnologyDistributionPolicy | None = None,
) -> TechnologyDistributionResult:
    """Convert technology facts into TechnologyDistribution (descriptive only)."""

    active = policy or TechnologyDistributionPolicy(
        visibility_policy=_infer_visibility_scope(aggregation)
    )
    eligible, unavailable, denom_count = resolve_technology_denominator(aggregation)
    eligible_set = set(eligible)
    repo_visibility = {
        item.repository_id: item.visibility for item in aggregation.repository_index
    }
    dataset_repos = set(aggregation.repository_population.included_repository_ids) or {
        item.repository_id for item in aggregation.repository_index
    }

    if active.visibility_policy is VisibilityAggregationScope.PUBLIC_OSS:
        # Public scope: only PUBLIC repos may appear in observations.
        public_eligible = {
            repo_id
            for repo_id in eligible_set
            if repo_visibility.get(repo_id) is DataVisibility.PUBLIC
        }
        unavailable = tuple(
            sorted(set(unavailable) | (eligible_set - public_eligible))
        )
        eligible = tuple(sorted(public_eligible))
        eligible_set = public_eligible
        denom_count = len(eligible)

    facts = aggregation.technology_facts
    groups, alias_count = group_technology_facts(facts, eligible_repository_ids=eligible_set)

    if active.included_categories:
        allowed = {item.lower() for item in active.included_categories}
        groups = [item for item in groups if item.category in allowed]

    groups = [
        item
        for item in groups
        if len(item.repository_ids) >= active.minimum_repository_count
    ]

    limitations: list[str] = list(active.limitations)
    limitations.append(
        "Technology distributions describe only the repositories with eligible "
        "Technology Inventory evidence in the selected dataset. They do not establish "
        "industry popularity, technology quality, support status, or modernization need."
    )
    limitations.append("technology_presence_does_not_establish_production_use")
    if unavailable:
        limitations.append(
            f"technology_inventory_unavailable_for_{len(unavailable)}_repositories"
        )
    if denom_count == 0:
        limitations.append("technology_denominator_unavailable")

    observations: list[TechnologyDistributionObservation] = []
    conflicting_repos: set[str] = set()
    unavailable_version_facts = 0

    for group in groups:
        version_rows: list[TechnologyVersionObservation] = []
        for bucket in group.versions.values():
            if bucket.state is VersionState.CONFLICTING:
                conflicting_repos.update(bucket.repository_ids)
            if bucket.state is VersionState.UNAVAILABLE:
                unavailable_version_facts += bucket.occurrence_count
            # Unavailable must not carry exact version strings.
            version_value = None if bucket.state is VersionState.UNAVAILABLE else bucket.version
            version_rows.append(
                TechnologyVersionObservation(
                    version=version_value,
                    state=bucket.state,
                    repository_ids=tuple(sorted(bucket.repository_ids)),
                    occurrence_count=bucket.occurrence_count,
                    source_assessment_ids=tuple(sorted(bucket.assessment_ids)),
                    limitations=tuple(sorted(bucket.limitations)),
                )
            )
        version_rows.sort(
            key=lambda row: (
                row.state.value,
                row.version or "",
                row.repository_ids,
            )
        )
        repo_ids = tuple(sorted(group.repository_ids))
        confidence = weakest_confidence(group.confidences)
        obs_limitations = set(group.limitations)
        if confidence in {ConfidenceLevel.LIMITED, ConfidenceLevel.UNAVAILABLE}:
            obs_limitations.add(f"observation_confidence:{confidence.value}")
        unavailable_for_tech = [
            repo_id for repo_id in repo_ids if any(
                bucket.state is VersionState.UNAVAILABLE and repo_id in bucket.repository_ids
                for bucket in group.versions.values()
            )
        ]
        if unavailable_for_tech:
            obs_limitations.add(
                f"version_unavailable_for_{len(set(unavailable_for_tech))}_repositories"
            )

        observations.append(
            TechnologyDistributionObservation(
                technology_id=group.technology_id,
                normalized_name=group.normalized_name,
                category=group.category,
                repository_count=len(repo_ids),
                repository_ratio=Ratio.of(len(repo_ids), denom_count),
                occurrence_count=group.occurrence_count,
                versions=tuple(version_rows),
                repository_ids=repo_ids,
                source_assessment_ids=tuple(sorted(group.assessment_ids)),
                confidence=confidence,
                limitations=tuple(sorted(obs_limitations)),
                source_names=tuple(sorted(group.source_names)),
            )
        )

    category_distributions = _build_category_distributions(
        observations, denominator=denom_count
    )

    distribution = TechnologyDistribution(
        observations=tuple(observations),
        repository_denominator=denom_count,
        limitations=tuple(sorted(set(limitations))),
        category_distributions=category_distributions,
        policy_id=active.policy_token,
        eligible_repository_ids=eligible,
        unavailable_repository_ids=tuple(sorted(set(unavailable))),
    )

    validate_distribution(
        distribution,
        dataset_repository_ids=dataset_repos | eligible_set,
        visibility_policy=active.visibility_policy,
        repository_visibility=repo_visibility,
    )

    diagnostics = TechnologyDistributionDiagnostics(
        input_fact_count=len(facts),
        normalized_fact_count=sum(group.occurrence_count for group in groups),
        distinct_technology_count=len(observations),
        eligible_repository_count=denom_count,
        unavailable_repository_count=len(set(unavailable)),
        conflicting_version_repository_count=len(conflicting_repos),
        unavailable_version_fact_count=unavailable_version_facts,
        alias_normalization_count=alias_count,
        rejected_fact_count=0,
        limitations=tuple(sorted(set(limitations))),
    )
    return TechnologyDistributionResult(
        distribution=distribution,
        diagnostics=diagnostics,
        policy_token=active.policy_token,
    )


def populate_report_technology_distribution(
    report: EngineeringIntelligenceReport,
    aggregation: CrossRepositoryAggregation,
    *,
    policy: TechnologyDistributionPolicy | None = None,
) -> EngineeringIntelligenceReport:
    """Return a new report with technology_distribution populated only."""

    result = build_technology_distribution(aggregation, policy=policy)
    return EngineeringIntelligenceReport.create(
        title=report.title,
        report_scope=report.report_scope,
        dataset=report.dataset,
        executive_summary=report.executive_summary,
        repository_population=report.repository_population,
        technology_distribution=result.distribution,
        capability_comparisons=report.capability_comparisons,
        recurring_patterns=report.recurring_patterns,
        assessment_head_distributions=report.assessment_head_distributions,
        modernization_observations=report.modernization_observations,
        repository_drilldowns=report.repository_drilldowns,
        confidence=report.confidence,
        limitations=report.limitations,
        methodology=report.methodology,
        generated_artifact_metadata=report.generated_artifact_metadata,
        report_policy_version=report.report_policy_version,
        schema_version=report.schema_version,
        interpretation_policy_bundle_id=report.interpretation_policy_bundle_id,
    )


def _build_category_distributions(
    observations: Sequence[TechnologyDistributionObservation],
    *,
    denominator: int,
) -> tuple[TechnologyCategoryDistribution, ...]:
    by_category: dict[str, list[TechnologyDistributionObservation]] = {}
    for item in observations:
        by_category.setdefault(item.category, []).append(item)
    rows: list[TechnologyCategoryDistribution] = []
    for category, items in sorted(by_category.items()):
        ordered = sorted(
            items,
            key=lambda row: (
                -row.repository_count,
                -row.occurrence_count,
                row.normalized_name.lower(),
                row.technology_id,
            ),
        )
        repos: set[str] = set()
        for row in ordered:
            repos.update(row.repository_ids)
        rows.append(
            TechnologyCategoryDistribution(
                category=category,
                technology_count=len(ordered),
                repository_count=len(repos),
                observations=tuple(row.technology_id for row in ordered),
                denominator=denominator,
                limitations=(),
            )
        )
    return tuple(rows)


def _infer_visibility_scope(
    aggregation: CrossRepositoryAggregation,
) -> VisibilityAggregationScope:
    vis = {item.visibility for item in aggregation.repository_index}
    if vis == {DataVisibility.PUBLIC}:
        return VisibilityAggregationScope.PUBLIC_OSS
    if DataVisibility.CUSTOMER_PRIVATE in vis or DataVisibility.INTERNAL in vis:
        if DataVisibility.PUBLIC in vis:
            return VisibilityAggregationScope.MIXED_INTERNAL
        return VisibilityAggregationScope.CUSTOMER_PRIVATE
    return VisibilityAggregationScope.MIXED_INTERNAL
