"""Build ModernizationObservation list from aggregation + recurring patterns."""

from __future__ import annotations

from collections import Counter

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    CrossRepositoryAggregation,
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.application.modernization_observations.candidates import (
    ModernizationObservationCandidate,
)
from codestrata_platform.intelligence_reporting.application.modernization_observations.grouping import (
    filter_threshold_candidates,
)
from codestrata_platform.intelligence_reporting.application.modernization_observations.policy import (
    ModernizationObservationDiagnostics,
    ModernizationObservationPolicy,
    ModernizationObservationResult,
)
from codestrata_platform.intelligence_reporting.application.modernization_observations.support import (
    collect_candidates,
    comparable_repositories,
    eligible_repositories,
    head_evaluated_repositories,
)
from codestrata_platform.intelligence_reporting.application.modernization_observations.templates import (
    head_display_label,
    render_statement,
    render_title,
)
from codestrata_platform.intelligence_reporting.application.modernization_observations.validation import (
    validate_observations,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    DataVisibility,
)
from codestrata_platform.intelligence_reporting.domain.modernization import (
    ModernizationObservation,
)
from codestrata_platform.intelligence_reporting.domain.patterns import (
    RecurringIntelligencePattern,
)
from codestrata_platform.intelligence_reporting.domain.report import EngineeringIntelligenceReport


def build_modernization_observations(
    aggregation: CrossRepositoryAggregation,
    *,
    recurring_patterns: tuple[RecurringIntelligencePattern, ...] = (),
    policy: ModernizationObservationPolicy | None = None,
) -> ModernizationObservationResult:
    """Synthesize evidence-backed portfolio modernization observations."""

    active = policy or ModernizationObservationPolicy(
        visibility_policy=_infer_visibility_scope(aggregation)
    )
    eligible = eligible_repositories(aggregation, policy=active)
    comparable = comparable_repositories(aggregation) & eligible
    candidates, counters = collect_candidates(
        aggregation, patterns=recurring_patterns, policy=active
    )

    def denominator_for(candidate: ModernizationObservationCandidate) -> set[str]:
        head = candidate.action.assessment_head_id
        evaluated = head_evaluated_repositories(
            aggregation, head_id=head, eligible=eligible
        )
        scoped = evaluated & comparable
        return scoped or evaluated

    accepted, rejected, unavailable_denom = filter_threshold_candidates(
        candidates,
        policy=active,
        denominator_for_candidate=denominator_for,
    )

    shared_limitations = list(active.limitations)
    shared_limitations.append(
        "Modernization observations summarize repeated deterministic repository-level "
        "actions within the selected assessed dataset. They are not portfolio "
        "Recommendations, delivery commitments, ROI claims, or transformation plans."
    )
    shared_limitations.append(
        "observation_identity_includes_repository_and_action_membership_per_slice_6_1"
    )
    shared_limitations.append("observations_do_not_create_portfolio_recommendations")
    shared_limitations.append("technology_prevalence_alone_does_not_create_observations")

    observations: list[ModernizationObservation] = []
    for candidate in accepted:
        denom_ids = denominator_for(candidate)
        denom_count = len(denom_ids)
        repo_ids = candidate.repository_ids
        rec_ids = tuple(
            sorted({ref.entity_id for ref in candidate.recommendation_refs})
        )
        pa_ids = tuple(
            sorted({ref.entity_id for ref in candidate.priority_action_refs})
        )
        roadmap_ids = tuple(sorted({ref.entity_id for ref in candidate.roadmap_refs}))
        limitations = set(shared_limitations)
        limitations.update(candidate.limitations)
        limitations.update(candidate.action.limitations)
        for ref in candidate.recommendation_refs:
            limitations.update(ref.limitations)
        confidence = _derive_confidence(candidate, denom_count=denom_count)
        if confidence in {ConfidenceLevel.LIMITED, ConfidenceLevel.UNAVAILABLE}:
            limitations.add(f"observation_confidence:{confidence.value}")
        if len(repo_ids) == 2:
            limitations.add("small_sample_two_repositories")
        if any(ref.legacy_limited for ref in candidate.recommendation_refs):
            limitations.add("includes_legacy_limited_support")
        if not candidate.supporting_evidence_ids:
            limitations.add("supporting_evidence_unavailable_or_incomplete")

        title = render_title(candidate.category)
        statement = render_statement(
            category=candidate.category,
            repository_count=len(repo_ids),
            denominator_count=denom_count,
            head_label=head_display_label(candidate.assessment_head_ids),
        )
        observations.append(
            ModernizationObservation.create(
                title=title,
                statement=statement,
                category=candidate.category,
                repository_ids=repo_ids,
                recommendation_ids=rec_ids,
                priority_action_ids=pa_ids,
                assessment_head_ids=candidate.assessment_head_ids,
                roadmap_initiative_ids=roadmap_ids,
                supporting_finding_ids=tuple(sorted(candidate.supporting_finding_ids)),
                supporting_evidence_ids=tuple(sorted(candidate.supporting_evidence_ids)),
                confidence=confidence,
                limitations=sorted(limitations),
                normalized_subject=candidate.action.normalized_subject,
                policy_version=active.domain_policy_version,
            )
        )

    observations_t = tuple(
        sorted(observations, key=lambda item: item.observation_id.value)
    )
    vis_map = {item.repository_id: item.visibility for item in aggregation.repository_index}
    dataset_repos = set(aggregation.repository_population.included_repository_ids) or {
        item.repository_id for item in aggregation.repository_index
    }
    validate_observations(
        observations_t,
        dataset_repository_ids=dataset_repos | eligible,
        recommendation_ids={item.recommendation_id for item in aggregation.recommendation_facts},
        priority_action_ids={
            item.priority_action_id for item in aggregation.priority_action_facts
        },
        roadmap_ids={item.initiative_id for item in aggregation.roadmap_facts},
        finding_ids={item.finding_id for item in aggregation.finding_facts},
        visibility_policy=active.visibility_policy,
        repository_visibility=vis_map,
    )

    by_category = Counter(item.category.value for item in observations_t)
    by_head = Counter(head for item in observations_t for head in item.assessment_head_ids)
    diagnostics = ModernizationObservationDiagnostics(
        input_recommendation_count=counters.get("input_recommendation_count", 0),
        input_priority_action_count=counters.get("input_priority_action_count", 0),
        input_roadmap_count=counters.get("input_roadmap_count", 0),
        recurring_pattern_support_count=counters.get("recurring_pattern_support_count", 0),
        candidate_count=len(candidates),
        accepted_observation_count=len(observations_t),
        below_threshold_count=sum(
            1
            for item in rejected
            if item.rejection_reason
            in {"below_minimum_repository_count", "below_minimum_repository_ratio"}
        ),
        rejected_candidate_count=counters.get("rejected_candidate_count", 0) + len(rejected),
        legacy_limited_count=counters.get("legacy_limited_count", 0),
        incomplete_support_chain_count=counters.get("incomplete_support_chain_count", 0),
        unavailable_denominator_count=unavailable_denom,
        unresolved_reference_count=0,
        observations_by_category=tuple(sorted(by_category.items())),
        observations_by_head=tuple(sorted(by_head.items())),
        limitations=tuple(sorted(set(shared_limitations))),
    )
    return ModernizationObservationResult(
        observations=observations_t,
        diagnostics=diagnostics,
        policy_token=active.policy_token,
    )


def populate_report_modernization_observations(
    report: EngineeringIntelligenceReport,
    aggregation: CrossRepositoryAggregation,
    *,
    recurring_patterns: tuple[RecurringIntelligencePattern, ...] | None = None,
    policy: ModernizationObservationPolicy | None = None,
) -> EngineeringIntelligenceReport:
    """Populate modernization_observations; preserve prior EIR sections."""

    patterns = recurring_patterns if recurring_patterns is not None else report.recurring_patterns
    result = build_modernization_observations(
        aggregation, recurring_patterns=patterns, policy=policy
    )
    return EngineeringIntelligenceReport.create(
        title=report.title,
        report_scope=report.report_scope,
        dataset=report.dataset,
        executive_summary=report.executive_summary,
        repository_population=report.repository_population,
        technology_distribution=report.technology_distribution,
        capability_comparisons=report.capability_comparisons,
        recurring_patterns=report.recurring_patterns,
        assessment_head_distributions=report.assessment_head_distributions,
        modernization_observations=result.observations,
        repository_drilldowns=report.repository_drilldowns,
        confidence=report.confidence,
        limitations=report.limitations,
        methodology=report.methodology,
        generated_artifact_metadata=report.generated_artifact_metadata,
        report_policy_version=report.report_policy_version,
        schema_version=report.schema_version,
        interpretation_policy_bundle_id=report.interpretation_policy_bundle_id,
    )


def _derive_confidence(
    candidate: ModernizationObservationCandidate,
    *,
    denom_count: int,
) -> ConfidenceLevel:
    repos = candidate.repository_ids
    if len(repos) < 2 or denom_count == 0 or not candidate.recommendation_refs:
        return ConfidenceLevel.UNAVAILABLE
    supports = [ref.confidence for ref in candidate.recommendation_refs]
    if any(ref.legacy_limited for ref in candidate.recommendation_refs):
        return ConfidenceLevel.LIMITED
    if not all(ref.comparable for ref in candidate.recommendation_refs):
        return ConfidenceLevel.LIMITED
    if not candidate.supporting_evidence_ids:
        return ConfidenceLevel.LIMITED
    order = {
        ConfidenceLevel.UNAVAILABLE: 0,
        ConfidenceLevel.LIMITED: 1,
        ConfidenceLevel.MODERATE: 2,
        ConfidenceLevel.HIGH: 3,
    }
    weakest = min(supports, key=lambda level: order.get(level, 0))
    # Missing Recommendation Confidence with a complete action chain is Limited,
    # not unavailable — support was established, quality is bounded.
    if weakest is ConfidenceLevel.UNAVAILABLE:
        if candidate.supporting_finding_ids:
            return ConfidenceLevel.LIMITED
        return ConfidenceLevel.UNAVAILABLE
    # Repository count alone does not produce High.
    if weakest is ConfidenceLevel.HIGH and len(repos) >= 2 and denom_count >= 2:
        if len(repos) == 2:
            return ConfidenceLevel.MODERATE  # small-sample cap
        return ConfidenceLevel.HIGH
    if weakest in {ConfidenceLevel.HIGH, ConfidenceLevel.MODERATE}:
        return ConfidenceLevel.MODERATE
    if weakest is ConfidenceLevel.LIMITED:
        return ConfidenceLevel.LIMITED
    return ConfidenceLevel.UNAVAILABLE


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
