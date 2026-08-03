"""Bounded repository technology summary strings."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    CrossRepositoryAggregation,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns.policy import (
    RepositoryDrilldownPolicy,
)
from codestrata_platform.intelligence_reporting.domain.enums import VersionState


def build_technology_summary(
    aggregation: CrossRepositoryAggregation,
    *,
    repository_id: str,
    policy: RepositoryDrilldownPolicy,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return (summary_lines, limitations). Safe names/categories/versions only."""

    facts = [
        item
        for item in aggregation.technology_facts
        if item.repository_id == repository_id
    ]
    facts.sort(
        key=lambda item: (
            item.category.lower(),
            item.normalized_name.lower(),
            item.version or "",
            item.version_state.value,
        )
    )
    lines: list[str] = []
    limitations: list[str] = []
    for fact in facts:
        version = ""
        if fact.version_state is VersionState.KNOWN and fact.version:
            version = f"@{fact.version}"
        elif fact.version_state is VersionState.CONFLICTING:
            version = "@conflicting"
            limitations.append("technology_version_conflicting")
        elif fact.version_state is VersionState.UNAVAILABLE:
            version = "@unavailable"
        line = f"{fact.category}:{fact.normalized_name}{version}"
        # Reject path-like content implicitly via domain safety later.
        if "/" in line or "\\" in line:
            limitations.append("technology_path_like_name_omitted")
            continue
        lines.append(line)
    total = len(lines)
    limited = lines[: policy.maximum_technology_refs]
    if total > len(limited):
        limitations.append(
            f"technology_refs_truncated:{len(limited)}/{total}"
        )
    return tuple(sorted(set(limited))), tuple(sorted(set(limitations)))
