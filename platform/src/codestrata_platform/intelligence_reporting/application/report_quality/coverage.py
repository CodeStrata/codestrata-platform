"""Dataset coverage status from canonical Assessment Coverage facts."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.intelligence_reporting.domain.capability import (
    CapabilityComparison,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ActivationStatus,
    CoverageStatus,
)


@dataclass(frozen=True, slots=True)
class DatasetCoverageSummary:
    """Structured dataset coverage — not Finding Severity or area averages."""

    status: CoverageStatus
    complete_material_head_count: int = 0
    partial_material_head_count: int = 0
    insufficient_material_head_count: int = 0
    unavailable_material_head_count: int = 0
    disabled_head_count: int = 0
    material_head_ids: tuple[str, ...] = ()
    partial_head_ids: tuple[str, ...] = ()
    unavailable_head_ids: tuple[str, ...] = ()


def summarize_dataset_coverage(
    comparisons: tuple[CapabilityComparison, ...],
) -> DatasetCoverageSummary:
    """Derive dataset coverage from head distributions without averaging ratios."""

    material_heads: list[str] = []
    complete = 0
    partial = 0
    insufficient = 0
    disabled = 0
    partial_ids: list[str] = []
    unavailable_ids: list[str] = []

    for comparison in comparisons:
        dist = comparison.distribution
        # Material contribution requires evaluated coverage (not disabled/unavailable-only).
        evaluated = (
            dist.complete_count
            + dist.partial_count
            + dist.insufficient_evidence_count
        )
        if evaluated == 0:
            if dist.disabled_count > 0:
                disabled += 1
            elif dist.unavailable_count > 0:
                unavailable_ids.append(comparison.assessment_head_id)
            continue
        material_heads.append(comparison.assessment_head_id)
        if dist.insufficient_evidence_count > 0 and dist.complete_count == 0:
            insufficient += 1
            partial_ids.append(comparison.assessment_head_id)
        elif dist.partial_count > 0 or dist.insufficient_evidence_count > 0:
            partial += 1
            partial_ids.append(comparison.assessment_head_id)
        elif dist.complete_count > 0:
            complete += 1
            if dist.unavailable_count > 0:
                # Mixed complete + unavailable within head → partial disclosure.
                partial += 1
                complete -= 1
                partial_ids.append(comparison.assessment_head_id)

    material_count = len(material_heads)
    if material_count == 0:
        status = CoverageStatus.UNAVAILABLE
    elif insufficient > 0:
        status = CoverageStatus.INSUFFICIENT_EVIDENCE
    elif partial > 0:
        # Substantially complete maps to COMPLETE when most heads are complete.
        if complete > 0 and partial <= max(1, material_count // 4):
            status = CoverageStatus.COMPLETE
        else:
            status = CoverageStatus.PARTIAL
    else:
        status = CoverageStatus.COMPLETE

    return DatasetCoverageSummary(
        status=status,
        complete_material_head_count=complete,
        partial_material_head_count=partial,
        insufficient_material_head_count=insufficient,
        unavailable_material_head_count=len(set(unavailable_ids)),
        disabled_head_count=disabled,
        material_head_ids=tuple(sorted(material_heads)),
        partial_head_ids=tuple(sorted(set(partial_ids))),
        unavailable_head_ids=tuple(sorted(set(unavailable_ids))),
    )


def material_snapshots(comparison: CapabilityComparison) -> tuple:
    """Snapshots that contribute material support (ignore disabled/not-applicable)."""

    rows = []
    for snap in comparison.repositories:
        if snap.activation_status in {
            ActivationStatus.DISABLED,
            ActivationStatus.UNAVAILABLE,
        }:
            continue
        if snap.coverage_status in {
            CoverageStatus.DISABLED,
            CoverageStatus.UNAVAILABLE,
        }:
            # Unavailable/disabled heads do not contribute material support.
            continue
        rows.append(snap)
    return tuple(rows)
