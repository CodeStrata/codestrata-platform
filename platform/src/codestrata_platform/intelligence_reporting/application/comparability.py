"""Cross-repository assessment comparability evaluation (no aggregation)."""

from __future__ import annotations

from collections.abc import Sequence

from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentComparability,
    IntelligenceDatasetSelectionPolicy,
    NormalizedAssessmentSnapshot,
    SUPPORTED_ASSESSMENT_SCHEMA_VERSION,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ComparabilityStatus,
    InclusionStatus,
)


def evaluate_comparability(
    snapshots: Sequence[NormalizedAssessmentSnapshot],
    *,
    policy: IntelligenceDatasetSelectionPolicy,
) -> AssessmentComparability:
    included = [
        item
        for item in snapshots
        if item.inclusion_status is InclusionStatus.INCLUDED
    ]
    if not included:
        return AssessmentComparability(
            status=ComparabilityStatus.UNAVAILABLE,
            selection_policy_compatibility=policy.selection_policy_token,
            limitations=("no_included_assessments",),
        )

    schema_versions = tuple(sorted({item.assessment_schema_version for item in included}))
    compatible: list[str] = []
    incompatible: list[str] = []
    limitations: list[str] = []
    head_compat: dict[str, str] = {}

    complete_1_2 = [
        item
        for item in included
        if item.assessment_schema_version == SUPPORTED_ASSESSMENT_SCHEMA_VERSION
        and item.traceability_status == "complete"
    ]
    legacy = [
        item
        for item in included
        if item.traceability_status in {"legacy", "incomplete"}
        or item.assessment_schema_version != SUPPORTED_ASSESSMENT_SCHEMA_VERSION
    ]

    for item in included:
        if item.traceability_status == "complete" and item.assessment_schema_version == (
            SUPPORTED_ASSESSMENT_SCHEMA_VERSION
        ):
            compatible.append(item.repository_id)
        else:
            incompatible.append(item.repository_id)
            limitations.append(f"limited_comparability:{item.repository_id}")

    # Per-head: missing head does not invalidate unrelated head comparison.
    all_heads = sorted(
        {
            head
            for item in included
            for head in (
                item.enabled_assessment_heads
                + item.available_assessment_heads
                + item.disabled_assessment_heads
                + item.unavailable_assessment_heads
                + item.missing_assessment_heads
            )
        }
    )
    for head in all_heads:
        present = 0
        for item in included:
            if head in item.missing_assessment_heads:
                continue
            if head in item.disabled_assessment_heads:
                present += 1
                continue
            if head in item.unavailable_assessment_heads:
                present += 1
                continue
            if head in item.enabled_assessment_heads or head in item.available_assessment_heads:
                present += 1
                continue
            if head in item.assessment_coverage or head in item.assessment_head_confidence:
                present += 1
        if present == 0:
            head_compat[head] = "unavailable"
        elif present == len(included):
            head_compat[head] = "comparable"
        else:
            head_compat[head] = "partially_comparable"

    if len(included) == 1:
        status = ComparabilityStatus.COMPARABLE if complete_1_2 else ComparabilityStatus.PARTIALLY_COMPARABLE
        if legacy:
            limitations.append("single_repository_legacy_or_incomplete")
    elif complete_1_2 and len(complete_1_2) == len(included) and len(schema_versions) == 1:
        status = ComparabilityStatus.COMPARABLE
    elif complete_1_2 and legacy:
        status = ComparabilityStatus.PARTIALLY_COMPARABLE
        limitations.append("mixed_complete_and_legacy_reports")
    elif legacy and not complete_1_2:
        status = ComparabilityStatus.PARTIALLY_COMPARABLE
        limitations.append("legacy_or_incomplete_reports_only")
    else:
        status = ComparabilityStatus.NOT_COMPARABLE
        limitations.append("insufficient_comparability")

    if any(item.pinned_revision is None for item in included):
        limitations.append("missing_pinned_revision_reduces_comparability")

    return AssessmentComparability(
        status=status,
        compatible_repository_ids=tuple(sorted(set(compatible))),
        incompatible_repository_ids=tuple(sorted(set(incompatible))),
        schema_versions=schema_versions,
        methodology_versions=(),
        assessment_head_compatibility=dict(sorted(head_compat.items())),
        selection_policy_compatibility=policy.selection_policy_token,
        limitations=tuple(sorted(set(limitations))),
    )
