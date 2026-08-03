"""Collect and group pattern candidates from aggregation facts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    CrossRepositoryAggregation,
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.application.aggregation.repository_projection import (
    classify_assessment_head,
)
from codestrata_platform.intelligence_reporting.application.recurring_patterns.candidates import (
    PatternCandidate,
    RecurringPatternOccurrence,
)
from codestrata_platform.intelligence_reporting.application.recurring_patterns.identities import (
    classify_rule_pattern_type,
    recommendation_subject,
    rule_subject,
    technology_conflict_subject,
)
from codestrata_platform.intelligence_reporting.application.recurring_patterns.policy import (
    LegacyPatternPolicy,
    RecurringPatternPolicy,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ActivationStatus,
    ConfidenceLevel,
    CoverageStatus,
    DataVisibility,
    PatternType,
    VersionState,
)


def eligible_repositories(
    aggregation: CrossRepositoryAggregation,
    *,
    policy: RecurringPatternPolicy,
) -> set[str]:
    included = set(aggregation.repository_population.included_repository_ids) or {
        item.repository_id for item in aggregation.repository_index
    }
    vis = {item.repository_id: item.visibility for item in aggregation.repository_index}
    if policy.visibility_policy is VisibilityAggregationScope.PUBLIC_OSS:
        return {
            repo_id
            for repo_id in included
            if vis.get(repo_id) is DataVisibility.PUBLIC
        }
    return included


def head_evaluated_repositories(
    aggregation: CrossRepositoryAggregation,
    *,
    head_id: str,
    eligible: set[str],
) -> set[str]:
    out: set[str] = set()
    for fact in aggregation.assessment_head_facts:
        if fact.assessment_head_id != head_id:
            continue
        if fact.repository_id not in eligible:
            continue
        if fact.activation_status is ActivationStatus.DISABLED:
            continue
        if fact.coverage_status in {
            CoverageStatus.UNAVAILABLE,
            CoverageStatus.DISABLED,
        }:
            continue
        if fact.activation_status is ActivationStatus.UNAVAILABLE:
            continue
        out.add(fact.repository_id)
    return out


def comparable_repositories(aggregation: CrossRepositoryAggregation) -> set[str]:
    return {
        item.repository_id
        for item in aggregation.repository_index
        if item.comparable and not item.legacy_or_incomplete
    }


def collect_candidates(
    aggregation: CrossRepositoryAggregation,
    *,
    policy: RecurringPatternPolicy,
) -> tuple[list[PatternCandidate], dict[str, int]]:
    """Return candidates and counters for diagnostics."""

    eligible = eligible_repositories(aggregation, policy=policy)
    repo_index = {item.repository_id: item for item in aggregation.repository_index}
    allowed_types = set(policy.included_pattern_types)
    allowed_heads = set(policy.included_assessment_heads)

    buckets: dict[tuple[PatternType, str], PatternCandidate] = {}
    counters = {
        "finding_occurrence_count": 0,
        "recommendation_occurrence_count": 0,
        "priority_action_occurrence_count": 0,
        "legacy_limited_count": 0,
        "rejected_candidate_count": 0,
    }

    # --- Finding / rule patterns ---
    if any(
        item
        in allowed_types
        for item in (
            PatternType.RECURRING_RULE,
            PatternType.RECURRING_CONFIGURATION_CONDITION,
            PatternType.RECURRING_DEPENDENCY_CONDITION,
            PatternType.RECURRING_ARCHITECTURE_CONDITION,
            PatternType.RECURRING_COMPLEXITY_CONDITION,
            PatternType.RECURRING_FINDING,
        )
    ):
        for finding in aggregation.finding_facts:
            if finding.repository_id not in eligible:
                continue
            if finding.unclassified or not finding.assessment_head_id:
                continue
            if not finding.rule_id.strip():
                continue
            if allowed_heads and finding.assessment_head_id not in allowed_heads:
                continue
            record = repo_index.get(finding.repository_id)
            legacy = bool(record and record.legacy_or_incomplete)
            if legacy and policy.legacy_policy is LegacyPatternPolicy.EXCLUDE:
                counters["rejected_candidate_count"] += 1
                continue
            if legacy and policy.legacy_policy is LegacyPatternPolicy.REJECT:
                raise ValueError(
                    f"legacy source materially affects pattern candidate: {finding.repository_id}"
                )
            pattern_type = classify_rule_pattern_type(finding.rule_id)
            if pattern_type not in allowed_types and PatternType.RECURRING_RULE in allowed_types:
                pattern_type = PatternType.RECURRING_RULE
            if pattern_type not in allowed_types:
                continue
            subject = rule_subject(
                rule_id=finding.rule_id,
                assessment_head_id=finding.assessment_head_id,
            )
            key = (pattern_type, subject.normalized_subject)
            candidate = buckets.get(key)
            if candidate is None:
                candidate = PatternCandidate(pattern_type=pattern_type, subject=subject)
                buckets[key] = candidate
            evidence = ()
            if finding.primary_evidence_id:
                evidence = (finding.primary_evidence_id,)
            conf = _map_finding_confidence(finding.finding_confidence)
            if legacy:
                counters["legacy_limited_count"] += 1
                conf = ConfidenceLevel.LIMITED
            candidate.occurrences.append(
                RecurringPatternOccurrence(
                    repository_id=finding.repository_id,
                    assessment_id=finding.assessment_id,
                    entity_type="finding",
                    entity_id=finding.finding_id,
                    rule_id=finding.rule_id,
                    assessment_head_id=finding.assessment_head_id,
                    normalized_subject=subject.normalized_subject,
                    evidence_ids=evidence,
                    finding_ids=(finding.finding_id,),
                    source_fact_ref=f"finding:{finding.repository_id}:{finding.finding_id}",
                    legacy_limited=legacy,
                    comparable=bool(record.comparable) if record else False,
                    confidence_support=conf,
                    limitations=(("legacy_or_incomplete_assessment",) if legacy else ()),
                )
            )
            counters["finding_occurrence_count"] += 1

    # Deduplicate prevalence: keep occurrences but repository presence uses unique repos.
    # Multiple findings same rule/repo remain as occurrences (for finding_ids), which is fine.

    # --- Recommendation patterns ---
    if PatternType.RECURRING_RECOMMENDATION in allowed_types:
        for rec in aggregation.recommendation_facts:
            if rec.repository_id not in eligible:
                continue
            head = classify_assessment_head(category=rec.category, rule_id=None)
            if head is None:
                continue
            if allowed_heads and head not in allowed_heads:
                continue
            subject = recommendation_subject(
                provider_id=rec.provider_id,
                category=rec.category,
                assessment_head_id=head,
            )
            if subject is None:
                counters["rejected_candidate_count"] += 1
                continue
            record = repo_index.get(rec.repository_id)
            legacy = bool(record and record.legacy_or_incomplete)
            if legacy and policy.legacy_policy is LegacyPatternPolicy.EXCLUDE:
                counters["rejected_candidate_count"] += 1
                continue
            key = (PatternType.RECURRING_RECOMMENDATION, subject.normalized_subject)
            candidate = buckets.get(key)
            if candidate is None:
                candidate = PatternCandidate(
                    pattern_type=PatternType.RECURRING_RECOMMENDATION,
                    subject=subject,
                )
                buckets[key] = candidate
            conf = ConfidenceLevel.MODERATE if not legacy else ConfidenceLevel.LIMITED
            if legacy:
                counters["legacy_limited_count"] += 1
            candidate.occurrences.append(
                RecurringPatternOccurrence(
                    repository_id=rec.repository_id,
                    assessment_id=rec.assessment_id,
                    entity_type="recommendation",
                    entity_id=rec.recommendation_id,
                    assessment_head_id=head,
                    normalized_subject=subject.normalized_subject,
                    finding_ids=tuple(rec.supporting_finding_ids),
                    recommendation_ids=(rec.recommendation_id,),
                    source_fact_ref=(
                        f"recommendation:{rec.repository_id}:{rec.recommendation_id}"
                    ),
                    legacy_limited=legacy,
                    comparable=bool(record.comparable) if record else False,
                    confidence_support=conf,
                    limitations=subject.limitations
                    + (("legacy_or_incomplete_assessment",) if legacy else ()),
                )
            )
            counters["recommendation_occurrence_count"] += 1

    # --- Priority Action patterns: deferred without stable intent ---
    # Count occurrences for diagnostics but do not create PA pattern candidates.
    counters["priority_action_occurrence_count"] = len(
        [
            item
            for item in aggregation.priority_action_facts
            if item.repository_id in eligible
        ]
    )

    # --- Technology conflict patterns only ---
    if PatternType.RECURRING_TECHNOLOGY_CONDITION in allowed_types:
        conflict_by_tech: dict[tuple[str, str], list] = defaultdict(list)
        for tech in aggregation.technology_facts:
            if tech.repository_id not in eligible:
                continue
            if tech.version_state is not VersionState.CONFLICTING:
                continue
            conflict_by_tech[(tech.category, tech.normalized_name)].append(tech)
        for (category, name), rows in conflict_by_tech.items():
            repos = {item.repository_id for item in rows}
            if len(repos) < 2:
                # Conflict within one repo is not cross-repo recurrence.
                continue
            subject = technology_conflict_subject(
                category=category, normalized_name=name
            )
            key = (PatternType.RECURRING_TECHNOLOGY_CONDITION, subject.normalized_subject)
            candidate = PatternCandidate(
                pattern_type=PatternType.RECURRING_TECHNOLOGY_CONDITION,
                subject=subject,
            )
            buckets[key] = candidate
            seen_repo: set[str] = set()
            for tech in rows:
                if tech.repository_id in seen_repo:
                    continue
                seen_repo.add(tech.repository_id)
                record = repo_index.get(tech.repository_id)
                candidate.occurrences.append(
                    RecurringPatternOccurrence(
                        repository_id=tech.repository_id,
                        assessment_id=tech.assessment_id,
                        entity_type="technology",
                        entity_id=tech.source_entity_ref.entity_id,
                        assessment_head_id="technology_inventory",
                        normalized_subject=subject.normalized_subject,
                        source_fact_ref=(
                            f"technology:{tech.repository_id}:"
                            f"{tech.source_entity_ref.entity_id}"
                        ),
                        legacy_limited=bool(record and record.legacy_or_incomplete),
                        comparable=bool(record.comparable) if record else False,
                        confidence_support=ConfidenceLevel.MODERATE,
                        limitations=subject.limitations,
                    )
                )

    return list(buckets.values()), counters


def filter_threshold_candidates(
    candidates: Sequence[PatternCandidate],
    *,
    policy: RecurringPatternPolicy,
    denominator_for_candidate,
) -> tuple[list[PatternCandidate], list[PatternCandidate], int]:
    """Split accepted vs below-threshold. Returns accepted, rejected, unavailable_denom_count."""

    accepted: list[PatternCandidate] = []
    rejected: list[PatternCandidate] = []
    unavailable_denom = 0
    for candidate in candidates:
        denom_ids = denominator_for_candidate(candidate)
        denom = len(denom_ids)
        if denom == 0:
            unavailable_denom += 1
            candidate.rejection_reason = "denominator_unavailable"
            rejected.append(candidate)
            continue
        # Prevalence uses distinct repositories among occurrences ∩ denominator.
        present = [item for item in candidate.occurrences if item.repository_id in denom_ids]
        repos = sorted({item.repository_id for item in present})
        if len(repos) < policy.minimum_repository_count:
            candidate.rejection_reason = "below_minimum_repository_count"
            # Replace occurrences with denom-filtered for diagnostics clarity.
            candidate.occurrences = present
            rejected.append(candidate)
            continue
        ratio = len(repos) / denom
        if ratio < policy.minimum_repository_ratio:
            candidate.rejection_reason = "below_minimum_repository_ratio"
            candidate.occurrences = present
            rejected.append(candidate)
            continue
        candidate.occurrences = present
        accepted.append(candidate)
    return accepted, rejected, unavailable_denom


def _map_finding_confidence(raw: str) -> ConfidenceLevel:
    text = str(raw or "").strip().lower()
    if text in {"high", "0.9", "0.95", "1", "1.0"}:
        return ConfidenceLevel.HIGH
    if text in {"moderate", "medium", "0.6", "0.7", "0.8"}:
        return ConfidenceLevel.MODERATE
    if text in {"limited", "low", "0.3", "0.4", "0.5"}:
        return ConfidenceLevel.LIMITED
    try:
        value = float(text)
        if value >= 0.85:
            return ConfidenceLevel.HIGH
        if value >= 0.55:
            return ConfidenceLevel.MODERATE
        if value > 0:
            return ConfidenceLevel.LIMITED
    except ValueError:
        pass
    return ConfidenceLevel.UNAVAILABLE
