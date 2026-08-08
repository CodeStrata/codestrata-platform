"""Central cohort suppression and percentage helpers."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.insights.models import MetricGroup
from codestrata_platform.community_cloud_api.insights.policy import (
    MINIMUM_GROUP_COUNT,
    SUPPRESSED_GROUP_LABEL,
)


def suppress_groups(
    counts: dict[str, int],
    *,
    dimension: str,
    minimum: int = MINIMUM_GROUP_COUNT,
) -> tuple[tuple[MetricGroup, ...], bool]:
    """Suppress groups with count < minimum into other_suppressed.

    Returns groups (sorted by key, suppressed last) and whether any suppression occurred.
    Does not leak original suppressed category labels or individual counts.
    """

    kept: list[tuple[str, int]] = []
    suppressed_total = 0
    suppressed_any = False
    for key, count in counts.items():
        if count < minimum:
            suppressed_total += count
            suppressed_any = True
        else:
            kept.append((key, count))

    groups: list[MetricGroup] = []
    denominator = sum(c for _, c in kept) + suppressed_total
    for key, count in sorted(kept, key=lambda x: x[0]):
        share = (count / denominator) if denominator else None
        groups.append(
            MetricGroup(
                dimension=dimension,
                key=key,
                count=count,
                share=share,
                suppressed=False,
            )
        )
    if suppressed_total:
        share = (suppressed_total / denominator) if denominator else None
        groups.append(
            MetricGroup(
                dimension=dimension,
                key=SUPPRESSED_GROUP_LABEL,
                count=suppressed_total,
                share=share,
                suppressed=True,
            )
        )
    return tuple(groups), suppressed_any


def share(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator
