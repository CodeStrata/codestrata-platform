"""Group AggregatedTechnologyFact rows into distribution observations."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    AggregatedTechnologyFact,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution.normalization import (
    normalize_technology_name,
    technology_id,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    VersionState,
)


@dataclass
class _VersionBucket:
    version: str | None
    state: VersionState
    repository_ids: set[str] = field(default_factory=set)
    assessment_ids: set[str] = field(default_factory=set)
    occurrence_count: int = 0
    limitations: set[str] = field(default_factory=set)


@dataclass
class _TechGroup:
    category: str
    normalized_name: str
    technology_id: str
    source_names: set[str] = field(default_factory=set)
    repository_ids: set[str] = field(default_factory=set)
    assessment_ids: set[str] = field(default_factory=set)
    occurrence_count: int = 0
    confidences: list[ConfidenceLevel] = field(default_factory=list)
    limitations: set[str] = field(default_factory=set)
    versions: dict[tuple[str | None, VersionState], _VersionBucket] = field(
        default_factory=dict
    )
    alias_applied: bool = False


def group_technology_facts(
    facts: Sequence[AggregatedTechnologyFact],
    *,
    eligible_repository_ids: set[str],
) -> tuple[list[_TechGroup], int]:
    """Group facts by (category, normalized_name). Returns groups + alias count."""

    groups: dict[tuple[str, str], _TechGroup] = {}
    alias_count = 0
    for fact in facts:
        if fact.repository_id not in eligible_repository_ids:
            continue
        normalized, aliased = normalize_technology_name(fact.normalized_name)
        if aliased:
            alias_count += 1
        category = (fact.category or "other").strip().lower().replace(" ", "_")
        key = (category, normalized.lower())
        group = groups.get(key)
        if group is None:
            group = _TechGroup(
                category=category,
                normalized_name=normalized,
                technology_id=technology_id(category=category, normalized_name=normalized),
            )
            groups[key] = group
        group.source_names.add(fact.normalized_name)
        group.repository_ids.add(fact.repository_id)
        group.assessment_ids.add(fact.assessment_id)
        group.occurrence_count += 1
        group.confidences.append(fact.confidence)
        group.limitations.update(fact.limitations)
        if aliased:
            group.alias_applied = True
        state = fact.version_state
        version = fact.version
        # Cross-repo diversity is not conflict; only explicit CONFLICTING state is.
        vkey = (version, state)
        bucket = group.versions.get(vkey)
        if bucket is None:
            bucket = _VersionBucket(version=version, state=state)
            group.versions[vkey] = bucket
        bucket.repository_ids.add(fact.repository_id)
        bucket.assessment_ids.add(fact.assessment_id)
        bucket.occurrence_count += 1
        if state is VersionState.CONFLICTING:
            bucket.limitations.add("conflicting_declarations")
            group.limitations.add("conflicting_declarations")
        if state is VersionState.UNAVAILABLE:
            bucket.limitations.add("version_unavailable")
    return list(groups.values()), alias_count


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


def collect_by_category(groups: Sequence[_TechGroup]) -> dict[str, list[_TechGroup]]:
    out: dict[str, list[_TechGroup]] = defaultdict(list)
    for group in groups:
        out[group.category].append(group)
    return dict(out)
