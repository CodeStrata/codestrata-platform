"""Reuse CapabilityComparison repository snapshots for drill-downs."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.repository_drilldowns.policy import (
    RepositoryDrilldownPolicy,
)
from codestrata_platform.intelligence_reporting.domain.capability import (
    CapabilityComparison,
    RepositoryCapabilitySnapshot,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ActivationStatus,
    ConfidenceLevel,
    CoverageStatus,
)

_LEVEL_RANK = {
    ConfidenceLevel.UNAVAILABLE: 0,
    ConfidenceLevel.LIMITED: 1,
    ConfidenceLevel.MODERATE: 2,
    ConfidenceLevel.HIGH: 3,
}


def snapshots_for_repository(
    comparisons: tuple[CapabilityComparison, ...],
    *,
    repository_id: str,
    policy: RepositoryDrilldownPolicy,
) -> tuple[RepositoryCapabilitySnapshot, ...]:
    allowed = set(policy.included_assessment_heads)
    rows: list[RepositoryCapabilitySnapshot] = []
    for comparison in comparisons:
        if allowed and comparison.assessment_head_id not in allowed:
            continue
        for snap in comparison.repositories:
            if snap.repository_id == repository_id:
                rows.append(snap)
    return tuple(sorted(rows, key=lambda item: item.assessment_head_id))


def weakest_material_head_confidence(
    snapshots: tuple[RepositoryCapabilitySnapshot, ...],
) -> ConfidenceLevel:
    levels: list[ConfidenceLevel] = []
    for snap in snapshots:
        if snap.activation_status in {
            ActivationStatus.DISABLED,
            ActivationStatus.UNAVAILABLE,
        }:
            continue
        if snap.coverage_status in {
            CoverageStatus.DISABLED,
            CoverageStatus.UNAVAILABLE,
        }:
            continue
        if snap.legacy_limited:
            levels.append(ConfidenceLevel.LIMITED)
            continue
        levels.append(snap.confidence_level)
    if not levels:
        return ConfidenceLevel.UNAVAILABLE
    return min(levels, key=lambda level: _LEVEL_RANK[level])


def head_limitations(
    snapshots: tuple[RepositoryCapabilitySnapshot, ...],
) -> tuple[str, ...]:
    notes: list[str] = []
    for snap in snapshots:
        if snap.coverage_status is CoverageStatus.PARTIAL:
            notes.append(f"coverage_partial:{snap.assessment_head_id}")
        if snap.coverage_status is CoverageStatus.INSUFFICIENT_EVIDENCE:
            notes.append(f"coverage_insufficient:{snap.assessment_head_id}")
        if snap.coverage_status is CoverageStatus.UNAVAILABLE:
            notes.append(f"coverage_unavailable:{snap.assessment_head_id}")
        if snap.coverage_status is CoverageStatus.DISABLED:
            notes.append(f"coverage_disabled:{snap.assessment_head_id}")
        if snap.confidence_level is ConfidenceLevel.LIMITED:
            notes.append(f"confidence_limited:{snap.assessment_head_id}")
        if snap.confidence_level is ConfidenceLevel.UNAVAILABLE and snap.coverage_status in {
            CoverageStatus.COMPLETE,
            CoverageStatus.PARTIAL,
            CoverageStatus.INSUFFICIENT_EVIDENCE,
        }:
            notes.append(f"confidence_unavailable:{snap.assessment_head_id}")
        if snap.legacy_limited:
            notes.append(f"legacy_limited_head:{snap.assessment_head_id}")
        notes.extend(snap.limitations)
    return tuple(sorted(set(notes)))
