"""Repository and assessment entity indexes for cross-repository aggregation."""

from __future__ import annotations

from collections.abc import Sequence

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    AggregatedEntityRef,
    AggregatedRepositoryRecord,
    CrossRepositoryAggregation,
)
from codestrata_platform.intelligence_reporting.application.errors import (
    AggregationInvariantError,
)


def assert_unique_repositories(records: Sequence[AggregatedRepositoryRecord]) -> None:
    ids = [item.repository_id for item in records]
    if len(ids) != len(set(ids)):
        raise AggregationInvariantError(
            "duplicate repository IDs in aggregation repository index",
            reason_code="duplicate_repository_index",
        )


def assert_unique_entity_refs(refs: Sequence[AggregatedEntityRef]) -> None:
    seen: set[tuple[str, str, str, str]] = set()
    duplicates = 0
    for ref in refs:
        key = ref.composite_key
        if key in seen:
            duplicates += 1
        seen.add(key)
    if duplicates:
        raise AggregationInvariantError(
            f"duplicate composite entity refs: {duplicates}",
            reason_code="duplicate_entity_refs",
        )


def build_assessment_index(
    *,
    finding_facts: Sequence[object],
    recommendation_facts: Sequence[object],
    priority_action_facts: Sequence[object],
    roadmap_facts: Sequence[object],
    correlation_facts: Sequence[object],
    technology_facts: Sequence[object],
    evidence_refs: Sequence[AggregatedEntityRef] = (),
    canonical_report_references: dict[str, str] | None = None,
) -> tuple[AggregatedEntityRef, ...]:
    """Flatten entity facts into a composite assessment index."""

    refs: list[AggregatedEntityRef] = list(evidence_refs)
    report_refs = canonical_report_references or {}

    for item in finding_facts:
        refs.append(
            AggregatedEntityRef(
                repository_id=item.repository_id,  # type: ignore[attr-defined]
                assessment_id=item.assessment_id,  # type: ignore[attr-defined]
                entity_type="finding",
                entity_id=item.finding_id,  # type: ignore[attr-defined]
                assessment_head_id=item.assessment_head_id,  # type: ignore[attr-defined]
                canonical_report_reference=report_refs.get(item.repository_id),  # type: ignore[attr-defined]
                rule_id=item.rule_id,  # type: ignore[attr-defined]
                severity=item.severity,  # type: ignore[attr-defined]
                confidence=item.finding_confidence,  # type: ignore[attr-defined]
            )
        )
    for item in recommendation_facts:
        refs.append(
            AggregatedEntityRef(
                repository_id=item.repository_id,  # type: ignore[attr-defined]
                assessment_id=item.assessment_id,  # type: ignore[attr-defined]
                entity_type="recommendation",
                entity_id=item.recommendation_id,  # type: ignore[attr-defined]
                canonical_report_reference=report_refs.get(item.repository_id),  # type: ignore[attr-defined]
                provider_id=item.provider_id,  # type: ignore[attr-defined]
                category=item.category,  # type: ignore[attr-defined]
                priority=item.priority,  # type: ignore[attr-defined]
                confidence=item.recommendation_confidence,  # type: ignore[attr-defined]
            )
        )
    for item in priority_action_facts:
        refs.append(
            AggregatedEntityRef(
                repository_id=item.repository_id,  # type: ignore[attr-defined]
                assessment_id=item.assessment_id,  # type: ignore[attr-defined]
                entity_type="priority_action",
                entity_id=item.priority_action_id,  # type: ignore[attr-defined]
                canonical_report_reference=report_refs.get(item.repository_id),  # type: ignore[attr-defined]
                priority=item.priority,  # type: ignore[attr-defined]
            )
        )
    for item in roadmap_facts:
        refs.append(
            AggregatedEntityRef(
                repository_id=item.repository_id,  # type: ignore[attr-defined]
                assessment_id=item.assessment_id,  # type: ignore[attr-defined]
                entity_type="roadmap_initiative",
                entity_id=item.initiative_id,  # type: ignore[attr-defined]
                canonical_report_reference=report_refs.get(item.repository_id),  # type: ignore[attr-defined]
                phase=item.phase,  # type: ignore[attr-defined]
            )
        )
    for item in correlation_facts:
        refs.append(
            AggregatedEntityRef(
                repository_id=item.repository_id,  # type: ignore[attr-defined]
                assessment_id=item.assessment_id,  # type: ignore[attr-defined]
                entity_type="finding_correlation",
                entity_id=item.correlation_id,  # type: ignore[attr-defined]
                canonical_report_reference=report_refs.get(item.repository_id),  # type: ignore[attr-defined]
                confidence=item.confidence,  # type: ignore[attr-defined]
            )
        )
    for item in technology_facts:
        refs.append(item.source_entity_ref)  # type: ignore[attr-defined]

    ordered = tuple(
        sorted(
            refs,
            key=lambda ref: (
                ref.repository_id,
                ref.assessment_id,
                ref.entity_type,
                ref.entity_id,
            ),
        )
    )
    assert_unique_entity_refs(ordered)
    return ordered


def index_lookup(
    aggregation: CrossRepositoryAggregation,
    *,
    repository_id: str,
    assessment_id: str,
    entity_type: str,
    entity_id: str,
) -> AggregatedEntityRef | None:
    key = (repository_id, assessment_id, entity_type, entity_id)
    for ref in aggregation.assessment_index:
        if ref.composite_key == key:
            return ref
    return None
