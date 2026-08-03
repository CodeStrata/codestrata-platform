"""Build RecurringIntelligencePattern list from CrossRepositoryAggregation."""

from __future__ import annotations

from collections import Counter

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    CrossRepositoryAggregation,
    DenominatorScope,
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.application.recurring_patterns.candidates import (
    PatternCandidate,
)
from codestrata_platform.intelligence_reporting.application.recurring_patterns.grouping import (
    collect_candidates,
    comparable_repositories,
    eligible_repositories,
    filter_threshold_candidates,
    head_evaluated_repositories,
)
from codestrata_platform.intelligence_reporting.application.recurring_patterns.policy import (
    RecurringPatternDiagnostics,
    RecurringPatternPolicy,
    RecurringPatternResult,
)
from codestrata_platform.intelligence_reporting.application.recurring_patterns.templates import (
    head_display_label,
    render_statement,
    render_title,
)
from codestrata_platform.intelligence_reporting.application.recurring_patterns.validation import (
    validate_patterns,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    DataVisibility,
    PatternType,
)
from codestrata_platform.intelligence_reporting.domain.patterns import (
    RecurringIntelligencePattern,
)
from codestrata_platform.intelligence_reporting.domain.report import EngineeringIntelligenceReport
from codestrata_platform.intelligence_reporting.domain.technology import Ratio


def build_recurring_patterns(
    aggregation: CrossRepositoryAggregation,
    *,
    policy: RecurringPatternPolicy | None = None,
) -> RecurringPatternResult:
    """Detect deterministic cross-repository recurring patterns (factual only)."""

    active = policy or RecurringPatternPolicy(
        visibility_policy=_infer_visibility_scope(aggregation)
    )
    eligible = eligible_repositories(aggregation, policy=active)
    comparable = comparable_repositories(aggregation) & eligible
    candidates, counters = collect_candidates(aggregation, policy=active)

    def denominator_for(candidate: PatternCandidate) -> set[str]:
        heads = candidate.subject.assessment_head_ids
        if candidate.pattern_type is PatternType.RECURRING_TECHNOLOGY_CONDITION:
            return _technology_denominator(aggregation, eligible=eligible)
        if not heads:
            return comparable or eligible
        head = heads[0]
        evaluated = head_evaluated_repositories(
            aggregation, head_id=head, eligible=eligible
        )
        # Prefer comparable ∩ evaluated; fall back to evaluated if none comparable.
        scoped = evaluated & comparable
        return scoped or evaluated

    accepted, rejected, unavailable_denom = filter_threshold_candidates(
        candidates,
        policy=active,
        denominator_for_candidate=denominator_for,
    )

    shared_limitations = list(active.limitations)
    shared_limitations.append(
        "Recurring patterns describe repeated deterministic conditions within the "
        "selected assessed dataset. They do not establish industry prevalence, "
        "organizational maturity, business impact, or a required portfolio action."
    )
    shared_limitations.append("pattern_identity_includes_repository_membership_per_slice_6_1")
    shared_limitations.append("recurrence_does_not_establish_causality_or_severity")
    shared_limitations.append("priority_action_patterns_deferred_without_stable_intent")
    shared_limitations.append("ordinary_technology_prevalence_belongs_in_technology_distribution")

    patterns: list[RecurringIntelligencePattern] = []
    for candidate in accepted:
        denom_ids = denominator_for(candidate)
        denom_count = len(denom_ids)
        repo_ids = candidate.repository_ids
        assessment_ids = tuple(sorted({item.assessment_id for item in candidate.occurrences}))
        finding_ids = tuple(
            sorted({fid for item in candidate.occurrences for fid in item.finding_ids})
        )
        recommendation_ids = tuple(
            sorted({rid for item in candidate.occurrences for rid in item.recommendation_ids})
        )
        evidence_ids = tuple(
            sorted({eid for item in candidate.occurrences for eid in item.evidence_ids})
        )
        limitations = set(shared_limitations)
        limitations.update(candidate.subject.limitations)
        for item in candidate.occurrences:
            limitations.update(item.limitations)
        if denom_count == 0:
            limitations.add("denominator_unavailable")
        confidence = _derive_pattern_confidence(candidate, denom_count=denom_count)
        if confidence in {ConfidenceLevel.LIMITED, ConfidenceLevel.UNAVAILABLE}:
            limitations.add(f"pattern_confidence:{confidence.value}")
        if any(item.legacy_limited for item in candidate.occurrences):
            limitations.add("includes_legacy_limited_occurrences")
        if len(repo_ids) == 2:
            limitations.add("minimum_recurrence_sample")

        title = render_title(candidate)
        statement = render_statement(
            candidate,
            repository_count=len(repo_ids),
            denominator_count=denom_count,
            head_label=head_display_label(candidate.subject.assessment_head_ids),
        )
        ratio = Ratio.of(len(repo_ids), denom_count) if denom_count else Ratio.of(len(repo_ids), 0)
        patterns.append(
            RecurringIntelligencePattern.create(
                pattern_type=candidate.pattern_type,
                title=title,
                statement=statement,
                repository_ids=repo_ids,
                normalized_subject=candidate.subject.normalized_subject,
                assessment_head_ids=candidate.subject.assessment_head_ids,
                rule_ids=candidate.subject.rule_ids,
                assessment_ids=assessment_ids,
                finding_ids=finding_ids,
                recommendation_ids=recommendation_ids,
                evidence_ids=evidence_ids,
                repository_ratio=ratio,
                confidence=confidence,
                limitations=sorted(limitations),
                policy_version=active.domain_policy_version,
                allow_single_repository=False,
            )
        )

    patterns_t = tuple(
        sorted(patterns, key=lambda item: item.pattern_id.value)
    )
    vis_map = {item.repository_id: item.visibility for item in aggregation.repository_index}
    dataset_repos = set(aggregation.repository_population.included_repository_ids) or {
        item.repository_id for item in aggregation.repository_index
    }
    assessment_ids_by_repo: dict[str, set[str]] = {}
    for item in aggregation.assessment_index:
        assessment_ids_by_repo.setdefault(item.repository_id, set()).add(item.assessment_id)
    finding_ids_by_assessment: dict[str, set[str]] = {}
    for item in aggregation.finding_facts:
        finding_ids_by_assessment.setdefault(item.assessment_id, set()).add(item.finding_id)
    recommendation_ids_by_assessment: dict[str, set[str]] = {}
    for item in aggregation.recommendation_facts:
        recommendation_ids_by_assessment.setdefault(item.assessment_id, set()).add(
            item.recommendation_id
        )

    validate_patterns(
        patterns_t,
        dataset_repository_ids=dataset_repos | eligible,
        assessment_ids_by_repo=assessment_ids_by_repo,
        finding_ids_by_assessment=finding_ids_by_assessment,
        recommendation_ids_by_assessment=recommendation_ids_by_assessment,
        visibility_policy=active.visibility_policy,
        repository_visibility=vis_map,
    )

    by_type = Counter(item.pattern_type.value for item in patterns_t)
    by_head = Counter(
        head for item in patterns_t for head in item.assessment_head_ids
    )
    diagnostics = RecurringPatternDiagnostics(
        finding_occurrence_count=counters.get("finding_occurrence_count", 0),
        recommendation_occurrence_count=counters.get("recommendation_occurrence_count", 0),
        priority_action_occurrence_count=counters.get("priority_action_occurrence_count", 0),
        candidate_count=len(candidates),
        accepted_pattern_count=len(patterns_t),
        rejected_candidate_count=counters.get("rejected_candidate_count", 0) + len(rejected),
        below_threshold_count=sum(
            1
            for item in rejected
            if item.rejection_reason
            in {"below_minimum_repository_count", "below_minimum_repository_ratio"}
        ),
        legacy_limited_count=counters.get("legacy_limited_count", 0),
        unavailable_denominator_count=unavailable_denom,
        unresolved_reference_count=0,
        patterns_by_type=tuple(sorted(by_type.items())),
        patterns_by_head=tuple(sorted(by_head.items())),
        limitations=tuple(sorted(set(shared_limitations))),
    )
    return RecurringPatternResult(
        patterns=patterns_t,
        diagnostics=diagnostics,
        policy_token=active.policy_token,
    )


def populate_report_recurring_patterns(
    report: EngineeringIntelligenceReport,
    aggregation: CrossRepositoryAggregation,
    *,
    policy: RecurringPatternPolicy | None = None,
) -> EngineeringIntelligenceReport:
    """Populate recurring_patterns; preserve technology and capability sections."""

    result = build_recurring_patterns(aggregation, policy=policy)
    return EngineeringIntelligenceReport.create(
        title=report.title,
        report_scope=report.report_scope,
        dataset=report.dataset,
        executive_summary=report.executive_summary,
        repository_population=report.repository_population,
        technology_distribution=report.technology_distribution,
        capability_comparisons=report.capability_comparisons,
        recurring_patterns=result.patterns,
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


def _technology_denominator(
    aggregation: CrossRepositoryAggregation,
    *,
    eligible: set[str],
) -> set[str]:
    for denom in aggregation.denominators:
        if denom.scope is DenominatorScope.TECHNOLOGY_INVENTORY_AVAILABLE:
            return set(denom.eligible_repository_ids) & eligible
    return set(eligible)


def _derive_pattern_confidence(
    candidate: PatternCandidate,
    *,
    denom_count: int,
) -> ConfidenceLevel:
    repos = candidate.repository_ids
    if len(repos) < 2 or denom_count == 0:
        return ConfidenceLevel.UNAVAILABLE
    supports = [item.confidence_support for item in candidate.occurrences]
    if any(item.legacy_limited for item in candidate.occurrences):
        return ConfidenceLevel.LIMITED
    if not all(item.comparable for item in candidate.occurrences):
        return ConfidenceLevel.LIMITED
    weakest = min(
        supports or [ConfidenceLevel.UNAVAILABLE],
        key=lambda level: {
            ConfidenceLevel.UNAVAILABLE: 0,
            ConfidenceLevel.LIMITED: 1,
            ConfidenceLevel.MODERATE: 2,
            ConfidenceLevel.HIGH: 3,
        }.get(level, 0),
    )
    # Repository count alone does not produce High.
    if weakest is ConfidenceLevel.HIGH and len(repos) >= 2 and denom_count >= 2:
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
