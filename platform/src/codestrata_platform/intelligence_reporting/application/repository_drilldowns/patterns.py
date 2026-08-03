"""Recurring pattern membership for a repository."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.repository_drilldowns.policy import (
    RepositoryDrilldownPolicy,
)
from codestrata_platform.intelligence_reporting.domain.patterns import (
    RecurringIntelligencePattern,
)


def pattern_ids_for_repository(
    patterns: tuple[RecurringIntelligencePattern, ...],
    *,
    repository_id: str,
    policy: RepositoryDrilldownPolicy,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    ids = sorted(
        {
            item.pattern_id.value
            for item in patterns
            if repository_id in item.repository_ids
        }
    )
    total = len(ids)
    selected = ids[: policy.maximum_pattern_refs]
    limitations: list[str] = []
    if total > len(selected):
        limitations.append(f"pattern_refs_truncated:{len(selected)}/{total}")
    return tuple(selected), tuple(limitations)
