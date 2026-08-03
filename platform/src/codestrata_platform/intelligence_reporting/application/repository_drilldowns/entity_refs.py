"""Bounded SafeEntityRef selection from aggregation facts."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    CrossRepositoryAggregation,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns.policy import (
    RepositoryDrilldownPolicy,
)
from codestrata_platform.intelligence_reporting.domain.drilldown import SafeEntityRef

_SEVERITY_RANK = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "moderate": 3,
    "low": 2,
    "info": 1,
    "informational": 1,
    "unknown": 0,
    "": 0,
}

_PRIORITY_RANK = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "moderate": 3,
    "low": 2,
    "deferred": 1,
    "unknown": 0,
    "": 0,
}

_CONFIDENCE_RANK = {
    "high": 3,
    "moderate": 2,
    "limited": 1,
    "unavailable": 0,
    "": 0,
}


@dataclass(frozen=True, slots=True)
class SelectedEntityBundle:
    finding_refs: tuple[SafeEntityRef, ...]
    recommendation_refs: tuple[SafeEntityRef, ...]
    priority_action_refs: tuple[SafeEntityRef, ...]
    roadmap_refs: tuple[SafeEntityRef, ...]
    correlation_refs: tuple[SafeEntityRef, ...]
    highest_priority_action_ids: tuple[str, ...]
    limitations: tuple[str, ...]
    finding_total: int
    recommendation_total: int
    priority_action_total: int
    roadmap_total: int
    correlation_total: int


def select_entity_refs(
    aggregation: CrossRepositoryAggregation,
    *,
    repository_id: str,
    assessment_id: str,
    policy: RepositoryDrilldownPolicy,
) -> SelectedEntityBundle:
    allowed = set(policy.included_entity_types)
    limitations: list[str] = []

    finding_refs: tuple[SafeEntityRef, ...] = ()
    finding_total = 0
    if "finding" in allowed:
        findings = [
            item
            for item in aggregation.finding_facts
            if item.repository_id == repository_id and item.assessment_id == assessment_id
        ]
        finding_total = len(findings)
        findings.sort(
            key=lambda item: (
                -_SEVERITY_RANK.get(item.severity.lower(), 0),
                -_CONFIDENCE_RANK.get(str(item.finding_confidence).lower(), 0),
                (item.assessment_head_id or "").lower(),
                item.rule_id.lower(),
                item.finding_id,
            )
        )
        selected = findings[: policy.maximum_finding_refs]
        finding_refs = tuple(
            SafeEntityRef(
                entity_id=item.finding_id,
                assessment_id=assessment_id,
                entity_kind="finding",
                label=_safe_label(item.severity, item.rule_id),
            )
            for item in selected
        )
        if finding_total > len(finding_refs):
            limitations.append(
                f"finding_refs_truncated:{len(finding_refs)}/{finding_total}"
            )

    recommendation_refs: tuple[SafeEntityRef, ...] = ()
    recommendation_total = 0
    if "recommendation" in allowed:
        recs = [
            item
            for item in aggregation.recommendation_facts
            if item.repository_id == repository_id and item.assessment_id == assessment_id
        ]
        recommendation_total = len(recs)
        recs.sort(
            key=lambda item: (
                -_PRIORITY_RANK.get(item.priority.lower(), 0),
                -_score_key(item.priority_score),
                -_CONFIDENCE_RANK.get(str(item.recommendation_confidence).lower(), 0),
                (item.provider_id or "").lower(),
                item.category.lower(),
                item.recommendation_id,
            )
        )
        selected_recs = recs[: policy.maximum_recommendation_refs]
        recommendation_refs = tuple(
            SafeEntityRef(
                entity_id=item.recommendation_id,
                assessment_id=assessment_id,
                entity_kind="recommendation",
                label=_safe_label(item.priority, item.category),
            )
            for item in selected_recs
        )
        if recommendation_total > len(recommendation_refs):
            limitations.append(
                f"recommendation_refs_truncated:{len(recommendation_refs)}/{recommendation_total}"
            )
        if any(item.limitations for item in selected_recs):
            limitations.append("recommendation_legacy_or_limited_present")

    priority_action_refs: tuple[SafeEntityRef, ...] = ()
    highest_priority_action_ids: tuple[str, ...] = ()
    priority_action_total = 0
    if "priority_action" in allowed:
        actions = [
            item
            for item in aggregation.priority_action_facts
            if item.repository_id == repository_id and item.assessment_id == assessment_id
        ]
        priority_action_total = len(actions)
        actions.sort(
            key=lambda item: (
                -_PRIORITY_RANK.get(item.priority.lower(), 0),
                -_score_key(item.priority_score),
                (item.presentation_bucket or "").lower(),
                item.priority_action_id,
            )
        )
        selected_pas = actions[: policy.maximum_priority_action_refs]
        priority_action_refs = tuple(
            SafeEntityRef(
                entity_id=item.priority_action_id,
                assessment_id=assessment_id,
                entity_kind="priority_action",
                label=_safe_label(item.priority, item.presentation_bucket or "action"),
            )
            for item in selected_pas
        )
        highest_priority_action_ids = tuple(
            item.priority_action_id for item in selected_pas[:3]
        )
        if priority_action_total > len(priority_action_refs):
            limitations.append(
                f"priority_action_refs_truncated:{len(priority_action_refs)}/{priority_action_total}"
            )

    roadmap_refs: tuple[SafeEntityRef, ...] = ()
    roadmap_total = 0
    if "roadmap_initiative" in allowed:
        initiatives = [
            item
            for item in aggregation.roadmap_facts
            if item.repository_id == repository_id and item.assessment_id == assessment_id
        ]
        roadmap_total = len(initiatives)
        initiatives.sort(
            key=lambda item: (
                (item.phase or "").lower(),
                (item.initiative_type or "").lower(),
                item.initiative_id,
            )
        )
        selected_rm = initiatives[: policy.maximum_roadmap_refs]
        roadmap_refs = tuple(
            SafeEntityRef(
                entity_id=item.initiative_id,
                assessment_id=assessment_id,
                entity_kind="roadmap_initiative",
                label=_safe_label(item.phase or "phase", item.initiative_type or "initiative"),
            )
            for item in selected_rm
        )
        if roadmap_total > len(roadmap_refs):
            limitations.append(
                f"roadmap_refs_truncated:{len(roadmap_refs)}/{roadmap_total}"
            )
        if any("legacy" in " ".join(item.limitations).lower() for item in selected_rm):
            limitations.append("roadmap_legacy_items_present")

    correlation_refs: tuple[SafeEntityRef, ...] = ()
    correlation_total = 0
    if "correlation" in allowed:
        correlations = [
            item
            for item in aggregation.correlation_facts
            if item.repository_id == repository_id and item.assessment_id == assessment_id
        ]
        correlation_total = len(correlations)
        correlations.sort(
            key=lambda item: (
                item.correlation_type.lower(),
                item.correlation_id,
            )
        )
        selected_corr = correlations[: policy.maximum_correlation_refs]
        correlation_refs = tuple(
            SafeEntityRef(
                entity_id=item.correlation_id,
                assessment_id=assessment_id,
                entity_kind="correlation",
                label=_safe_label(item.correlation_type, item.confidence or "correlation"),
            )
            for item in selected_corr
        )
        if correlation_total > len(correlation_refs):
            limitations.append(
                f"correlation_refs_truncated:{len(correlation_refs)}/{correlation_total}"
            )

    if finding_total > len(finding_refs) or recommendation_total > len(recommendation_refs):
        limitations.append(
            "canonical_assessment_report_required_for_complete_entity_list"
        )

    return SelectedEntityBundle(
        finding_refs=finding_refs,
        recommendation_refs=recommendation_refs,
        priority_action_refs=priority_action_refs,
        roadmap_refs=roadmap_refs,
        correlation_refs=correlation_refs,
        highest_priority_action_ids=highest_priority_action_ids,
        limitations=tuple(sorted(set(limitations))),
        finding_total=finding_total,
        recommendation_total=recommendation_total,
        priority_action_total=priority_action_total,
        roadmap_total=roadmap_total,
        correlation_total=correlation_total,
    )


def _score_key(score: str | None) -> float:
    if score is None:
        return 0.0
    try:
        return float(score)
    except (TypeError, ValueError):
        return 0.0


def _safe_label(primary: str, secondary: str) -> str:
    left = (primary or "unknown").strip().lower()[:40]
    right = (secondary or "item").strip().lower()[:40]
    return f"{left}:{right}"
