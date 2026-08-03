"""Collect Recommendation / PA / roadmap / pattern support for candidates."""

from __future__ import annotations

from collections import defaultdict

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    CrossRepositoryAggregation,
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.application.aggregation.repository_projection import (
    classify_assessment_head,
)
from codestrata_platform.intelligence_reporting.application.modernization_observations.candidates import (
    ModernizationObservationCandidate,
    SupportRef,
)
from codestrata_platform.intelligence_reporting.application.modernization_observations.identities import (
    build_action_identity,
    pattern_support_mappings,
)
from codestrata_platform.intelligence_reporting.application.modernization_observations.policy import (
    LegacyObservationPolicy,
    ModernizationObservationPolicy,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ActivationStatus,
    ConfidenceLevel,
    CoverageStatus,
    DataVisibility,
    PatternType,
)
from codestrata_platform.intelligence_reporting.domain.patterns import (
    RecurringIntelligencePattern,
)


def eligible_repositories(
    aggregation: CrossRepositoryAggregation,
    *,
    policy: ModernizationObservationPolicy,
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


def comparable_repositories(aggregation: CrossRepositoryAggregation) -> set[str]:
    return {
        item.repository_id
        for item in aggregation.repository_index
        if item.comparable and not item.legacy_or_incomplete
    }


def head_evaluated_repositories(
    aggregation: CrossRepositoryAggregation,
    *,
    head_id: str,
    eligible: set[str],
) -> set[str]:
    out: set[str] = set()
    for fact in aggregation.assessment_head_facts:
        if fact.assessment_head_id != head_id or fact.repository_id not in eligible:
            continue
        if fact.activation_status in {
            ActivationStatus.DISABLED,
            ActivationStatus.UNAVAILABLE,
        }:
            continue
        if fact.coverage_status in {
            CoverageStatus.UNAVAILABLE,
            CoverageStatus.DISABLED,
        }:
            continue
        out.add(fact.repository_id)
    return out


def _map_confidence(raw: str) -> ConfidenceLevel:
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


def collect_candidates(
    aggregation: CrossRepositoryAggregation,
    *,
    patterns: tuple[RecurringIntelligencePattern, ...],
    policy: ModernizationObservationPolicy,
) -> tuple[list[ModernizationObservationCandidate], dict[str, int]]:
    eligible = eligible_repositories(aggregation, policy=policy)
    repo_index = {item.repository_id: item for item in aggregation.repository_index}
    allowed_categories = set(policy.included_categories)
    allowed_heads = set(policy.included_assessment_heads)
    counters = {
        "input_recommendation_count": 0,
        "input_priority_action_count": 0,
        "input_roadmap_count": 0,
        "recurring_pattern_support_count": 0,
        "rejected_candidate_count": 0,
        "legacy_limited_count": 0,
        "incomplete_support_chain_count": 0,
    }

    findings_by_id = {
        (item.repository_id, item.finding_id): item for item in aggregation.finding_facts
    }
    recs_by_id = {
        (item.repository_id, item.recommendation_id): item
        for item in aggregation.recommendation_facts
    }

    buckets: dict[str, ModernizationObservationCandidate] = {}

    # Recommendation authority
    for rec in aggregation.recommendation_facts:
        if rec.repository_id not in eligible:
            continue
        counters["input_recommendation_count"] += 1
        head = classify_assessment_head(category=rec.category, rule_id=None)
        if head is None:
            counters["rejected_candidate_count"] += 1
            continue
        if allowed_heads and head not in allowed_heads:
            continue
        action = build_action_identity(
            provider_id=rec.provider_id,
            recommendation_category=rec.category,
            assessment_head_id=head,
        )
        if action is None:
            counters["rejected_candidate_count"] += 1
            continue
        if action.observation_category not in allowed_categories:
            continue
        record = repo_index.get(rec.repository_id)
        legacy = bool(record and record.legacy_or_incomplete)
        if legacy and policy.legacy_policy is LegacyObservationPolicy.EXCLUDE:
            counters["rejected_candidate_count"] += 1
            continue
        if legacy and policy.legacy_policy is LegacyObservationPolicy.REJECT:
            raise ValueError(
                f"legacy source materially affects observation candidate: {rec.repository_id}"
            )
        candidate = buckets.get(action.action_identity)
        if candidate is None:
            candidate = ModernizationObservationCandidate(
                action=action,
                category=action.observation_category,
            )
            candidate.limitations.update(action.limitations)
            buckets[action.action_identity] = candidate

        evidence_ids: list[str] = []
        for fid in rec.supporting_finding_ids:
            finding = findings_by_id.get((rec.repository_id, fid))
            if finding is None:
                continue
            candidate.supporting_finding_ids.add(fid)
            if finding.primary_evidence_id:
                evidence_ids.append(finding.primary_evidence_id)
                candidate.supporting_evidence_ids.add(finding.primary_evidence_id)
        if not evidence_ids and not rec.supporting_finding_ids:
            counters["incomplete_support_chain_count"] += 1
            candidate.limitations.add("incomplete_finding_evidence_chain")

        conf = _map_confidence(rec.recommendation_confidence)
        if legacy:
            counters["legacy_limited_count"] += 1
            conf = ConfidenceLevel.LIMITED
            candidate.limitations.add("legacy_or_incomplete_assessment")
        candidate.recommendation_refs.append(
            SupportRef(
                repository_id=rec.repository_id,
                assessment_id=rec.assessment_id,
                entity_type="recommendation",
                entity_id=rec.recommendation_id,
                confidence=conf,
                legacy_limited=legacy,
                comparable=bool(record.comparable) if record else False,
                finding_ids=tuple(rec.supporting_finding_ids),
                evidence_ids=tuple(sorted(set(evidence_ids))),
                limitations=(("legacy_or_incomplete_assessment",) if legacy else ()),
            )
        )

    # Map recommendation → action identity for PA/roadmap joins
    rec_action: dict[tuple[str, str], str] = {}
    for key, candidate in buckets.items():
        for ref in candidate.recommendation_refs:
            rec_action[(ref.repository_id, ref.entity_id)] = key

    # Priority Action support via primary recommendation identity
    for action in aggregation.priority_action_facts:
        if action.repository_id not in eligible:
            continue
        counters["input_priority_action_count"] += 1
        mapped_keys: set[str] = set()
        for rid in action.supporting_recommendation_ids:
            identity = rec_action.get((action.repository_id, rid))
            if identity:
                mapped_keys.add(identity)
        if not mapped_keys:
            continue
        record = repo_index.get(action.repository_id)
        legacy = bool(record and record.legacy_or_incomplete)
        for identity in mapped_keys:
            candidate = buckets[identity]
            candidate.priority_action_refs.append(
                SupportRef(
                    repository_id=action.repository_id,
                    assessment_id=action.assessment_id,
                    entity_type="priority_action",
                    entity_id=action.priority_action_id,
                    confidence=ConfidenceLevel.MODERATE,
                    legacy_limited=legacy,
                    comparable=bool(record.comparable) if record else False,
                    finding_ids=tuple(action.supporting_finding_ids),
                )
            )
            candidate.supporting_finding_ids.update(action.supporting_finding_ids)

    # Roadmap support: PA-backed only
    pa_to_identity: dict[tuple[str, str], set[str]] = defaultdict(set)
    for key, candidate in buckets.items():
        for ref in candidate.priority_action_refs:
            pa_to_identity[(ref.repository_id, ref.entity_id)].add(key)

    for initiative in aggregation.roadmap_facts:
        if initiative.repository_id not in eligible:
            continue
        counters["input_roadmap_count"] += 1
        initiative_type = (initiative.initiative_type or "").strip().lower()
        if initiative_type and initiative_type != "priority_action_backed":
            # Legacy/non-PA-backed cannot create or independently authorize.
            continue
        if not initiative.supporting_priority_action_ids:
            continue
        mapped: set[str] = set()
        for paid in initiative.supporting_priority_action_ids:
            mapped.update(pa_to_identity.get((initiative.repository_id, paid), ()))
        if not mapped:
            continue
        record = repo_index.get(initiative.repository_id)
        for identity in mapped:
            candidate = buckets[identity]
            candidate.roadmap_refs.append(
                SupportRef(
                    repository_id=initiative.repository_id,
                    assessment_id=initiative.assessment_id,
                    entity_type="roadmap_initiative",
                    entity_id=initiative.initiative_id,
                    confidence=ConfidenceLevel.MODERATE,
                    legacy_limited=bool(record and record.legacy_or_incomplete),
                    comparable=bool(record.comparable) if record else False,
                    finding_ids=tuple(initiative.supporting_finding_ids),
                )
            )

    # Recurring pattern support (reviewed catalog only) — attach pattern IDs
    for pattern in patterns:
        for mapping in pattern_support_mappings():
            if pattern.pattern_type.value != mapping["source_pattern_type"]:
                continue
            source_rules = set(mapping["source_rule_ids"])  # type: ignore[arg-type]
            if source_rules and not source_rules.intersection(pattern.rule_ids):
                continue
            target_category = str(mapping["target_category"])
            for candidate in buckets.values():
                if candidate.category.value != target_category:
                    continue
                # Overlapping repositories required
                overlap = set(candidate.repository_ids).intersection(pattern.repository_ids)
                if len(overlap) < 2 and set(candidate.repository_ids) != set(
                    pattern.repository_ids
                ):
                    # Still attach if any overlap with recommendation-backed repos
                    if not overlap:
                        continue
                candidate.recurring_pattern_ids.append(pattern.pattern_id.value)
                candidate.supporting_finding_ids.update(pattern.finding_ids)
                candidate.supporting_evidence_ids.update(pattern.evidence_ids)
                counters["recurring_pattern_support_count"] += 1

    # Drop candidates without recommendation authority if required
    kept: list[ModernizationObservationCandidate] = []
    for candidate in buckets.values():
        if "recommendation" in policy.required_support_types and not candidate.recommendation_refs:
            candidate.rejection_reason = "missing_recommendation_support"
            counters["rejected_candidate_count"] += 1
            continue
        # Pattern alone without recommendations already excluded above.
        kept.append(candidate)
    return kept, counters
