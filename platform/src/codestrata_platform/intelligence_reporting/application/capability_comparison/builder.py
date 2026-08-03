"""Build CapabilityComparison and AssessmentHeadDistribution from aggregation."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    CrossRepositoryAggregation,
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.application.capability_comparison.distributions import (
    build_assessment_head_distribution,
    build_capability_distribution,
)
from codestrata_platform.intelligence_reporting.application.capability_comparison.policy import (
    CapabilityComparisonDiagnostics,
    CapabilityComparisonPolicy,
    CapabilityComparisonResult,
)
from codestrata_platform.intelligence_reporting.application.capability_comparison.snapshots import (
    build_primary_pa_counts,
    build_snapshots_for_head,
    collect_heads,
    eligible_repositories_for_visibility,
    repository_visibility_map,
    weakest_confidence,
)
from codestrata_platform.intelligence_reporting.application.capability_comparison.validation import (
    validate_capability_outputs,
)
from codestrata_platform.intelligence_reporting.domain.capability import CapabilityComparison
from codestrata_platform.intelligence_reporting.domain.enums import (
    ActivationStatus,
    ConfidenceLevel,
    CoverageStatus,
    DataVisibility,
)
from codestrata_platform.intelligence_reporting.domain.report import EngineeringIntelligenceReport


def build_capability_comparisons(
    aggregation: CrossRepositoryAggregation,
    *,
    policy: CapabilityComparisonPolicy | None = None,
) -> CapabilityComparisonResult:
    """Convert assessment-head facts into capability comparisons (factual only)."""

    active = policy or CapabilityComparisonPolicy(
        visibility_policy=_infer_visibility_scope(aggregation)
    )
    eligible = eligible_repositories_for_visibility(aggregation, policy=active)
    vis_map = repository_visibility_map(aggregation)
    dataset_repos = set(aggregation.repository_population.included_repository_ids) or {
        item.repository_id for item in aggregation.repository_index
    }
    pa_counts = build_primary_pa_counts(aggregation)
    heads = collect_heads(aggregation, policy=active)

    shared_limitations = list(active.limitations)
    shared_limitations.append(
        "Capability comparisons describe the assessed repository/head states within the "
        "selected dataset. They do not rank repositories, measure engineering-team "
        "performance, or establish organizational maturity."
    )
    shared_limitations.append("counts_are_not_normalized_by_repository_size")
    shared_limitations.append("findings_represent_detected_conditions_only")
    shared_limitations.append("zero_findings_do_not_certify_absence_of_risk")
    shared_limitations.append("dataset_selection_is_not_industry_representative")
    shared_limitations.append(
        "priority_action_ownership_policy:primary_head"
    )

    comparisons: list[CapabilityComparison] = []
    head_distributions = []
    comparable_snap = limited_snap = unavailable_snap = 0
    empty_head = 0
    missing_coverage = missing_confidence = 0
    excluded_total = 0

    for head_id in heads:
        snapshots, comparable_ids, limited_ids, excluded_ids = build_snapshots_for_head(
            aggregation,
            head_id=head_id,
            policy=active,
            eligible_repos=eligible,
            pa_counts=pa_counts,
        )
        excluded_total += len(excluded_ids)
        if not snapshots:
            empty_head += 1
            limitations = sorted(
                set(shared_limitations)
                | {
                    "no_eligible_repositories_for_head",
                    "denominator_unavailable",
                }
            )
            comparisons.append(
                CapabilityComparison(
                    assessment_head_id=head_id,
                    repositories=(),
                    confidence=ConfidenceLevel.UNAVAILABLE,
                    limitations=tuple(limitations),
                    excluded_repository_ids=tuple(sorted(set(excluded_ids))),
                    policy_id=active.policy_token,
                )
            )
            head_distributions.append(
                build_assessment_head_distribution(
                    head_id=head_id,
                    snapshots=(),
                    findings=aggregation.finding_facts,
                    limitations=limitations,
                )
            )
            continue

        for snap in snapshots:
            if snap.comparable:
                comparable_snap += 1
            elif snap.coverage_status is CoverageStatus.UNAVAILABLE:
                unavailable_snap += 1
                limited_snap += 1
            else:
                limited_snap += 1
            if snap.coverage_status is CoverageStatus.UNAVAILABLE:
                missing_coverage += 1
            if snap.confidence_level is ConfidenceLevel.UNAVAILABLE:
                missing_confidence += 1

        distribution = build_capability_distribution(snapshots)
        with_findings = sum(1 for item in snapshots if item.finding_count > 0)
        head_limitations = set(shared_limitations)
        disabled_n = sum(
            1 for item in snapshots if item.activation_status is ActivationStatus.DISABLED
        )
        if disabled_n:
            head_limitations.add(f"head_disabled_for_{disabled_n}_repositories")
        unavailable_n = sum(
            1 for item in snapshots if item.coverage_status is CoverageStatus.UNAVAILABLE
        )
        if unavailable_n:
            head_limitations.add(f"coverage_unavailable_for_{unavailable_n}_repositories")
        conf_unavailable_n = sum(
            1 for item in snapshots if item.confidence_level is ConfidenceLevel.UNAVAILABLE
        )
        if conf_unavailable_n:
            head_limitations.add(f"confidence_unavailable_for_{conf_unavailable_n}_repositories")
        if len(comparable_ids) < active.minimum_comparable_repository_count:
            head_limitations.add("sample_limited_comparable_repository_count")
        if len(comparable_ids) == 1:
            head_limitations.add("single_comparable_repository_sample_limited")

        section_confidence = weakest_confidence(
            [item.confidence_level for item in snapshots if item.comparable]
            or [item.confidence_level for item in snapshots]
        )
        if section_confidence in {ConfidenceLevel.LIMITED, ConfidenceLevel.UNAVAILABLE}:
            head_limitations.add(f"section_confidence:{section_confidence.value}")

        comparisons.append(
            CapabilityComparison(
                assessment_head_id=head_id,
                repositories=tuple(snapshots),
                distribution=distribution,
                confidence=section_confidence,
                limitations=tuple(sorted(head_limitations)),
                comparable_repository_ids=tuple(sorted(set(comparable_ids))),
                limited_repository_ids=tuple(sorted(set(limited_ids))),
                excluded_repository_ids=tuple(sorted(set(excluded_ids))),
                policy_id=active.policy_token,
                repositories_with_findings_count=with_findings,
            )
        )
        head_distributions.append(
            build_assessment_head_distribution(
                head_id=head_id,
                snapshots=snapshots,
                findings=aggregation.finding_facts,
                limitations=sorted(head_limitations),
            )
        )

    comparisons_t = tuple(comparisons)
    distributions_t = tuple(head_distributions)
    validate_capability_outputs(
        comparisons=comparisons_t,
        head_distributions=distributions_t,
        dataset_repository_ids=dataset_repos | eligible,
        visibility_policy=active.visibility_policy,
        repository_visibility=vis_map,
    )

    diagnostics = CapabilityComparisonDiagnostics(
        input_head_fact_count=len(aggregation.assessment_head_facts),
        comparison_count=len(comparisons_t),
        repository_snapshot_count=sum(len(item.repositories) for item in comparisons_t),
        comparable_snapshot_count=comparable_snap,
        limited_snapshot_count=limited_snap,
        unavailable_snapshot_count=unavailable_snap,
        empty_head_count=empty_head,
        missing_coverage_count=missing_coverage,
        missing_confidence_count=missing_confidence,
        excluded_repository_count=excluded_total,
        unresolved_reference_count=0,
        limitations=tuple(sorted(set(shared_limitations))),
    )
    return CapabilityComparisonResult(
        comparisons=comparisons_t,
        head_distributions=distributions_t,
        diagnostics=diagnostics,
        policy_token=active.policy_token,
    )


def populate_report_capability_comparisons(
    report: EngineeringIntelligenceReport,
    aggregation: CrossRepositoryAggregation,
    *,
    policy: CapabilityComparisonPolicy | None = None,
) -> EngineeringIntelligenceReport:
    """Return a new report with capability sections populated; preserve technology_distribution."""

    result = build_capability_comparisons(aggregation, policy=policy)
    return EngineeringIntelligenceReport.create(
        title=report.title,
        report_scope=report.report_scope,
        dataset=report.dataset,
        executive_summary=report.executive_summary,
        repository_population=report.repository_population,
        technology_distribution=report.technology_distribution,
        capability_comparisons=result.comparisons,
        recurring_patterns=report.recurring_patterns,
        assessment_head_distributions=result.head_distributions,
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
