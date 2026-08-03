"""Modernization observation membership for a repository."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.repository_drilldowns.policy import (
    RepositoryDrilldownPolicy,
)
from codestrata_platform.intelligence_reporting.domain.modernization import (
    ModernizationObservation,
)


def observation_ids_for_repository(
    observations: tuple[ModernizationObservation, ...],
    *,
    repository_id: str,
    policy: RepositoryDrilldownPolicy,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    ids = sorted(
        {
            item.observation_id.value
            for item in observations
            if repository_id in item.repository_ids
        }
    )
    total = len(ids)
    selected = ids[: policy.maximum_observation_refs]
    limitations: list[str] = []
    if total > len(selected):
        limitations.append(f"observation_refs_truncated:{len(selected)}/{total}")
    return tuple(selected), tuple(limitations)
