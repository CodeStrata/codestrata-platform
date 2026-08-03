"""Build RepositoryCapabilitySnapshot rows from aggregation facts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    AggregatedFindingFact,
    AggregatedPriorityActionFact,
    AggregatedRecommendationFact,
    AggregatedRepositoryRecord,
    CrossRepositoryAggregation,
)
from codestrata_platform.intelligence_reporting.application.aggregation.repository_projection import (
    classify_assessment_head,
)
from codestrata_platform.intelligence_reporting.application.capability_comparison.policy import (
    CapabilityComparisonPolicy,
    LegacyCapabilityPolicy,
    PriorityActionOwnershipPolicy,
)
from codestrata_platform.intelligence_reporting.domain.capability import (
    RepositoryCapabilitySnapshot,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ActivationStatus,
    ComparabilityStatus,
    ConfidenceLevel,
    CoverageStatus,
    DataVisibility,
)


def primary_head_for_priority_action(
    action: AggregatedPriorityActionFact,
    *,
    recommendations: Mapping[str, AggregatedRecommendationFact],
    findings: Mapping[str, AggregatedFindingFact],
) -> str | None:
    """Primary-head ownership: first supporting recommendation category, else finding head."""

    for rec_id in action.supporting_recommendation_ids:
        rec = recommendations.get(rec_id)
        if rec is None:
            continue
        head = classify_assessment_head(category=rec.category, rule_id=None)
        if head:
            return head
    for finding_id in action.supporting_finding_ids:
        finding = findings.get(finding_id)
        if finding is None:
            continue
        if finding.assessment_head_id:
            return finding.assessment_head_id
    return None


def build_primary_pa_counts(
    aggregation: CrossRepositoryAggregation,
) -> dict[tuple[str, str], int]:
    """(repository_id, assessment_head_id) → PA count under primary-head ownership."""

    recs = {
        item.recommendation_id: item for item in aggregation.recommendation_facts
    }
    findings = {item.finding_id: item for item in aggregation.finding_facts}
    counts: dict[tuple[str, str], int] = defaultdict(int)
    seen: set[tuple[str, str, str]] = set()
    for action in aggregation.priority_action_facts:
        key = (action.repository_id, action.assessment_id, action.priority_action_id)
        if key in seen:
            continue
        seen.add(key)
        head = primary_head_for_priority_action(
            action, recommendations=recs, findings=findings
        )
        if head is None:
            continue
        counts[(action.repository_id, head)] += 1
    return dict(counts)


def repository_visibility_map(
    aggregation: CrossRepositoryAggregation,
) -> dict[str, DataVisibility]:
    return {item.repository_id: item.visibility for item in aggregation.repository_index}


def eligible_repositories_for_visibility(
    aggregation: CrossRepositoryAggregation,
    *,
    policy: CapabilityComparisonPolicy,
) -> set[str]:
    from codestrata_platform.intelligence_reporting.application.aggregation.models import (
        VisibilityAggregationScope,
    )

    vis = repository_visibility_map(aggregation)
    included = set(aggregation.repository_population.included_repository_ids) or {
        item.repository_id for item in aggregation.repository_index
    }
    if policy.visibility_policy is VisibilityAggregationScope.PUBLIC_OSS:
        return {
            repo_id
            for repo_id in included
            if vis.get(repo_id) is DataVisibility.PUBLIC
        }
    return included


def head_comparability(
    aggregation: CrossRepositoryAggregation,
    head_id: str,
) -> ComparabilityStatus:
    raw = {}
    if aggregation.comparability is not None:
        raw = dict(aggregation.comparability.assessment_head_compatibility)
    value = str(raw.get(head_id) or "").strip().lower()
    if not value:
        return ComparabilityStatus.UNAVAILABLE
    try:
        return ComparabilityStatus(value)
    except ValueError:
        return ComparabilityStatus.UNAVAILABLE


def build_snapshots_for_head(
    aggregation: CrossRepositoryAggregation,
    *,
    head_id: str,
    policy: CapabilityComparisonPolicy,
    eligible_repos: set[str],
    pa_counts: Mapping[tuple[str, str], int],
) -> tuple[
    list[RepositoryCapabilitySnapshot],
    list[str],
    list[str],
    list[str],
]:
    """Return snapshots, comparable IDs, limited IDs, excluded IDs for one head."""

    repo_index: dict[str, AggregatedRepositoryRecord] = {
        item.repository_id: item for item in aggregation.repository_index
    }
    facts = [
        item
        for item in aggregation.assessment_head_facts
        if item.assessment_head_id == head_id and item.repository_id in eligible_repos
    ]
    facts_by_repo = {item.repository_id: item for item in facts}

    head_compat = head_comparability(aggregation, head_id)
    comparable_ids: list[str] = []
    limited_ids: list[str] = []
    excluded_ids: list[str] = []
    snapshots: list[RepositoryCapabilitySnapshot] = []

    for repo_id in sorted(eligible_repos):
        record = repo_index.get(repo_id)
        fact = facts_by_repo.get(repo_id)
        if fact is None:
            excluded_ids.append(repo_id)
            continue
        if (
            record is not None
            and record.legacy_or_incomplete
            and policy.legacy_policy is LegacyCapabilityPolicy.EXCLUDE
        ):
            excluded_ids.append(repo_id)
            continue

        legacy = bool(record.legacy_or_incomplete) if record else False
        repo_comparable = bool(record.comparable) if record else False
        if head_compat is ComparabilityStatus.COMPARABLE and repo_comparable and not legacy:
            is_comparable = True
        elif head_compat is ComparabilityStatus.UNAVAILABLE:
            is_comparable = False
        elif fact.coverage_status in {
            CoverageStatus.UNAVAILABLE,
            CoverageStatus.DISABLED,
        }:
            is_comparable = False
        elif fact.activation_status is ActivationStatus.DISABLED:
            is_comparable = False
        else:
            is_comparable = repo_comparable and head_compat in {
                ComparabilityStatus.COMPARABLE,
                ComparabilityStatus.PARTIALLY_COMPARABLE,
            }

        limitations = set(fact.limitations)
        if legacy:
            limitations.add("legacy_or_incomplete_assessment")
            limited_ids.append(repo_id)
        elif not is_comparable:
            limitations.add("not_comparable_for_head")
            limited_ids.append(repo_id)
        else:
            comparable_ids.append(repo_id)

        if fact.finding_count == 0 and fact.coverage_status is CoverageStatus.COMPLETE:
            limitations.add("zero_findings_do_not_certify_absence_of_risk")

        pa_count = fact.priority_action_count
        if policy.priority_action_ownership_policy is PriorityActionOwnershipPolicy.PRIMARY_HEAD:
            pa_count = int(pa_counts.get((repo_id, head_id), 0))

        highest = fact.highest_severity
        if (
            fact.coverage_status
            in {CoverageStatus.UNAVAILABLE, CoverageStatus.DISABLED}
            or fact.activation_status
            in {ActivationStatus.UNAVAILABLE, ActivationStatus.DISABLED}
        ):
            if fact.finding_count == 0:
                highest = None
                limitations.add("highest_severity_unavailable_for_unevaluated_head")

        snapshots.append(
            RepositoryCapabilitySnapshot(
                repository_id=repo_id,
                assessment_id=fact.assessment_id,
                assessment_head_id=head_id,
                activation_status=fact.activation_status,
                coverage_status=fact.coverage_status,
                confidence_level=fact.confidence_level,
                finding_count=fact.finding_count,
                recommendation_count=fact.recommendation_count,
                priority_action_count=pa_count,
                highest_severity=highest,
                limitations=tuple(sorted(limitations)),
                drilldown_ref=None,
                comparable=is_comparable,
                legacy_limited=legacy,
                assessment_run_id=record.assessment_run_id if record else None,
            )
        )

    return snapshots, comparable_ids, limited_ids, excluded_ids


def collect_heads(
    aggregation: CrossRepositoryAggregation,
    *,
    policy: CapabilityComparisonPolicy,
) -> list[str]:
    from codestrata_platform.intelligence_reporting.application.capability_comparison.head_catalog import (
        COMMERCIAL_HEAD_CATALOG,
        catalog_order_key,
        try_canonicalize_assessment_head,
    )
    from codestrata_platform.intelligence_reporting.application.capability_comparison.policy import (
        UnknownHeadPolicy,
    )

    raw_heads = {item.assessment_head_id for item in aggregation.assessment_head_facts}
    if policy.included_assessment_heads:
        wanted = {
            try_canonicalize_assessment_head(item) or item
            for item in policy.included_assessment_heads
        }
        raw_heads = {head for head in raw_heads if head in wanted}

    resolved: list[str] = []
    for head in raw_heads:
        canonical = try_canonicalize_assessment_head(head)
        if canonical is None:
            if policy.unknown_head_policy is UnknownHeadPolicy.REJECT:
                raise ValueError(f"unknown assessment head in aggregation: {head}")
            continue
        if canonical in COMMERCIAL_HEAD_CATALOG:
            resolved.append(canonical)
    return sorted(set(resolved), key=catalog_order_key)


def weakest_confidence(levels: Sequence[ConfidenceLevel]) -> ConfidenceLevel:
    order = {
        ConfidenceLevel.UNAVAILABLE: 0,
        ConfidenceLevel.LIMITED: 1,
        ConfidenceLevel.MODERATE: 2,
        ConfidenceLevel.HIGH: 3,
    }
    if not levels:
        return ConfidenceLevel.UNAVAILABLE
    return min(levels, key=lambda item: order.get(item, 0))
