"""Construct IntelligenceDataset from normalized assessment snapshots."""

from __future__ import annotations

from collections.abc import Sequence

from codestrata_platform.domain.errors import InvariantViolationError
from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentComparability,
    IntelligenceDatasetSelectionPolicy,
    NormalizedAssessmentSnapshot,
)
from codestrata_platform.intelligence_reporting.application.errors import DatasetInvariantError
from codestrata_platform.intelligence_reporting.domain.dataset import (
    ExcludedRepository,
    IntelligenceDataset,
    RepositoryAssessmentReference,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    InclusionStatus,
)


def snapshot_to_reference(snapshot: NormalizedAssessmentSnapshot) -> RepositoryAssessmentReference:
    """Map a normalized snapshot to a domain reference — never embeds the report."""

    coverage_refs = tuple(
        sorted(f"coverage:{head}:{status}" for head, status in snapshot.assessment_coverage.items())
    )
    confidence_refs = tuple(
        sorted(
            f"confidence:{head}:{status}"
            for head, status in snapshot.assessment_head_confidence.items()
        )
    )
    limitations = list(snapshot.limitations)
    if snapshot.exclusion_reason:
        limitations.append(f"exclusion_reason:{snapshot.exclusion_reason}")
    # Unpublished public URLs remain on the snapshot for eligibility precheck only.
    source_reference = snapshot.source_reference
    if (
        snapshot.visibility is DataVisibility.PUBLIC
        and source_reference
        and not snapshot.source_reference_publication_permitted
    ):
        source_reference = None
        limitations.append("source_reference_omitted_without_publication_permission")
    return RepositoryAssessmentReference(
        repository_id=snapshot.repository_id,
        assessment_id=snapshot.assessment_id,
        assessment_run_id=snapshot.assessment_run_id,
        workspace_id=snapshot.workspace_id,
        source_type=snapshot.source_type,
        source_reference=source_reference,
        pinned_revision=snapshot.pinned_revision,
        assessment_schema_version=snapshot.assessment_schema_version,
        assessment_timestamp=snapshot.assessment_timestamp,
        enabled_assessment_heads=snapshot.enabled_assessment_heads,
        available_assessment_heads=snapshot.available_assessment_heads,
        assessment_coverage_refs=coverage_refs,
        assessment_confidence_refs=confidence_refs,
        canonical_report_reference=snapshot.canonical_report_reference,
        inclusion_status=snapshot.inclusion_status,
        visibility=snapshot.visibility,
        display_name=snapshot.display_name,
        source_reference_publication_permitted=snapshot.source_reference_publication_permitted,
        limitations=tuple(sorted(set(limitations))),
    )


def build_intelligence_dataset(
    *,
    name: str,
    snapshots: Sequence[NormalizedAssessmentSnapshot],
    policy: IntelligenceDatasetSelectionPolicy,
    comparability: AssessmentComparability,
    dataset_tags: Sequence[str] = (),
) -> IntelligenceDataset:
    """Build a validated IntelligenceDataset from selected snapshots."""

    # Domain dataset currently allows one assessment row per repository_id.
    # Include only included + non-included that don't collide on repository_id.
    included = [
        item for item in snapshots if item.inclusion_status is InclusionStatus.INCLUDED
    ]
    non_included = [
        item for item in snapshots if item.inclusion_status is not InclusionStatus.INCLUDED
    ]
    included_ids = {item.repository_id for item in included}
    # Keep excluded/rejected rows only when repository is not already included.
    extras = [item for item in non_included if item.repository_id not in included_ids]
    # Prefer a single row per repository among extras (deterministic: lowest run id).
    extras_by_repo: dict[str, NormalizedAssessmentSnapshot] = {}
    for item in sorted(
        extras,
        key=lambda row: (row.repository_id, row.assessment_run_id, row.assessment_id),
    ):
        extras_by_repo.setdefault(item.repository_id, item)

    ordered = tuple(
        sorted(
            [*included, *extras_by_repo.values()],
            key=lambda row: (row.repository_id, row.assessment_id, row.assessment_run_id),
        )
    )
    references = tuple(snapshot_to_reference(item) for item in ordered)
    excluded = tuple(
        ExcludedRepository(
            repository_id=item.repository_id,
            reason=item.exclusion_reason or item.inclusion_status.value,
        )
        for item in sorted(
            [row for row in snapshots if row.inclusion_status is not InclusionStatus.INCLUDED],
            key=lambda row: (row.repository_id, row.assessment_run_id),
        )
    )
    try:
        return IntelligenceDataset.create(
            name=name,
            selection_method=policy.assessment_selection.value,
            repository_assessments=references,
            excluded_repositories=excluded,
            dataset_tags=tuple(dataset_tags),
            comparability_status=comparability.status,
            selection_policy_version=policy.selection_policy_token,
        )
    except InvariantViolationError as error:
        raise DatasetInvariantError(
            str(error),
            reason_code=getattr(error, "reason_code", "dataset_invariant"),
        ) from error
