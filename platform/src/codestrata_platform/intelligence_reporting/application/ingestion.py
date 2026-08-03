"""Ingest canonical Engine assessment reports into a validated IntelligenceDataset."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata.reporting.traceability.preservation import (
    CanonicalReportLoadError,
    classify_traceability_state,
    extract_assessment,
    schema_version_of,
    validate_canonical_assessment,
)
from codestrata_platform.intelligence_reporting.application.comparability import (
    evaluate_comparability,
)
from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentDatasetInput,
    DatasetIngestionDiagnostic,
    DatasetIngestionResult,
    FailedAssessmentBehavior,
    IngestionStatus,
    IntelligenceDatasetSelectionPolicy,
    NormalizedAssessmentSnapshot,
)
from codestrata_platform.intelligence_reporting.application.dataset_builder import (
    build_intelligence_dataset,
)
from codestrata_platform.intelligence_reporting.application.errors import (
    AmbiguousRepositoryAssessmentError,
    AssessmentTraceabilityError,
    DuplicateAssessmentConflictError,
    IntelligenceReportingIngestionError,
    MalformedAssessmentReportError,
    UnsafeAssessmentMetadataError,
    UnsupportedAssessmentSchemaError,
)
from codestrata_platform.intelligence_reporting.application.normalization import (
    build_normalized_snapshot,
    stable_canonical_report_digest,
)
from codestrata_platform.intelligence_reporting.application.validation import (
    require_input_identity,
    resolve_schema_version,
    validate_report_document,
    validate_source_reference_safety,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ExclusionReason,
    InclusionStatus,
    SourceType,
)
from codestrata_platform.intelligence_reporting.application.ports import (
    CanonicalAssessmentReportSource,
    InlineAssessmentReportSource,
)


def ingest_assessment_dataset(
    inputs: Sequence[AssessmentDatasetInput],
    *,
    name: str = "Intelligence dataset",
    policy: IntelligenceDatasetSelectionPolicy | None = None,
    report_source: CanonicalAssessmentReportSource | None = None,
    dataset_tags: Sequence[str] = (),
) -> DatasetIngestionResult:
    """Build one deterministic IntelligenceDataset from canonical report documents.

    Preserves canonical Engine assessment identities and relationships. Does not
    rerun analysis, infer missing relationships, or create portfolio conclusions.
    """

    active_policy = policy or IntelligenceDatasetSelectionPolicy()
    source = report_source or InlineAssessmentReportSource()
    diagnostics: list[DatasetIngestionDiagnostic] = []
    candidates: list[NormalizedAssessmentSnapshot] = []

    # Sort inputs for determinism without affecting identity material.
    ordered_inputs = sorted(
        inputs,
        key=lambda item: (
            item.repository_id,
            item.assessment_id,
            item.assessment_run_id,
        ),
    )

    for item in ordered_inputs:
        try:
            snapshot = _ingest_one(item, policy=active_policy, source=source)
            candidates.append(snapshot)
        except IntelligenceReportingIngestionError as error:
            if active_policy.failed_assessment_behavior is FailedAssessmentBehavior.FAIL_FAST:
                raise
            rejected = _rejected_stub(item, error)
            candidates.append(rejected)
            diagnostics.append(
                DatasetIngestionDiagnostic(
                    code=error.reason_code or "ingestion_error",
                    message=str(error),
                    repository_id=item.repository_id or None,
                    assessment_id=item.assessment_id or None,
                    assessment_run_id=item.assessment_run_id or None,
                )
            )

    selected, selection_diagnostics = _apply_selection_and_dedupe(
        candidates, policy=active_policy
    )
    diagnostics.extend(selection_diagnostics)
    diagnostics = _stable_diagnostics(diagnostics)

    comparability = evaluate_comparability(selected, policy=active_policy)
    included = tuple(
        item for item in selected if item.inclusion_status is InclusionStatus.INCLUDED
    )
    excluded = tuple(
        item
        for item in selected
        if item.inclusion_status
        in {
            InclusionStatus.EXCLUDED,
            InclusionStatus.LEGACY_LIMITED,
            InclusionStatus.PARTIAL,
            InclusionStatus.UNAVAILABLE,
        }
    )
    rejected = tuple(
        item for item in selected if item.inclusion_status is InclusionStatus.REJECTED
    )

    dataset = None
    if included or excluded or rejected:
        # Include rejected/excluded snapshots for metadata when they don't collide.
        dataset = build_intelligence_dataset(
            name=name,
            snapshots=selected,
            policy=active_policy,
            comparability=comparability,
            dataset_tags=dataset_tags,
        )

    return DatasetIngestionResult(
        dataset=dataset,
        included=included,
        excluded=excluded,
        rejected=rejected,
        comparability=comparability,
        diagnostics=tuple(diagnostics),
        selection_policy_token=active_policy.selection_policy_token,
    )


def _ingest_one(
    item: AssessmentDatasetInput,
    *,
    policy: IntelligenceDatasetSelectionPolicy,
    source: CanonicalAssessmentReportSource,
) -> NormalizedAssessmentSnapshot:
    require_input_identity(item)
    validate_source_reference_safety(
        source_reference=item.source_reference,
        visibility=item.visibility,
    )
    if item.inclusion_status is InclusionStatus.EXCLUDED:
        document = _load_document(item, source=source)
        return build_normalized_snapshot(
            item=item,
            document=document,
            schema_version=str(document.get("schema_version") or "unknown"),
            is_legacy=True,
            traceability_status="excluded",
            canonical_report_reference=item.report_reference
            or f"artifact:{item.assessment_id}:report_json",
            inclusion_status=InclusionStatus.EXCLUDED,
            ingestion_status=IngestionStatus.EXCLUDED,
            limitations=item.limitations + ("explicitly_excluded",),
            exclusion_reason=ExclusionReason.EXPLICITLY_EXCLUDED.value,
            diagnostics=("explicitly_excluded",),
        )

    if (
        policy.require_pinned_revision_for_public_oss
        and item.source_type is SourceType.PUBLIC_OSS
        and not item.pinned_revision
    ):
        raise UnsafeAssessmentMetadataError(
            "public OSS assessment requires pinned_revision under active policy",
            reason_code=ExclusionReason.MISSING_REVISION.value,
        )

    document = _load_document(item, source=source)
    schema_version, is_legacy = resolve_schema_version(
        document, policy=policy.schema_compatibility_policy
    )
    limitations = list(item.limitations)
    if is_legacy:
        limitations.append("legacy_or_incomplete_schema")
    if item.source_type is SourceType.PUBLIC_OSS and not item.pinned_revision:
        limitations.append("missing_pinned_revision")

    # Engine canonical traceability validation (fail closed). Do not require
    # Platform ReportJsonParser finding projection — real Engine reports may use
    # null evidence paths / non-string metadata that the projection parser rejects
    # even when the assessment document is schema-valid.
    try:
        assessment = extract_assessment(dict(document))
    except CanonicalReportLoadError:
        assessment = dict(document) if isinstance(document, Mapping) else {}
    reported = schema_version_of(document)
    if reported and schema_version in {None, "", "unknown"}:
        schema_version = reported
    try:
        traceability_status = validate_canonical_assessment(assessment)
    except CanonicalReportLoadError as error:
        raise AssessmentTraceabilityError(
            f"Canonical report traceability validation failed: {error}",
            reason_code=ExclusionReason.TRACEABILITY_FAILURE.value,
        ) from error
    if not traceability_status:
        traceability_status = classify_traceability_state(assessment) or "legacy"

    diagnostics = (
        f"traceability_status:{traceability_status}",
        "canonical_interchange:assessment_report_json",
        "ingestion_validation:engine_traceability",
    )

    if is_legacy or traceability_status in {"legacy", "incomplete"}:
        inclusion = InclusionStatus.LEGACY_LIMITED
        ingestion = IngestionStatus.LEGACY_LIMITED
        limitations.append(f"traceability_status:{traceability_status}")
        # Legacy may still be dataset-included for limited comparability when requested.
        if item.inclusion_status is InclusionStatus.INCLUDED:
            inclusion = InclusionStatus.INCLUDED
            limitations.append("included_with_legacy_limitations")
    else:
        inclusion = InclusionStatus.INCLUDED
        ingestion = IngestionStatus.NORMALIZED

    return build_normalized_snapshot(
        item=item,
        document=document,
        schema_version=schema_version
        if schema_version != "unknown"
        else ASSESSMENT_JSON_SCHEMA_VERSION,
        is_legacy=is_legacy,
        traceability_status=traceability_status,
        canonical_report_reference=item.report_reference
        or f"artifact:{item.assessment_id}:report_json",
        inclusion_status=inclusion,
        ingestion_status=ingestion,
        limitations=tuple(limitations),
        diagnostics=diagnostics,
    )


def _load_document(
    item: AssessmentDatasetInput,
    *,
    source: CanonicalAssessmentReportSource,
) -> Mapping[str, Any]:
    if item.report_document is not None:
        return validate_report_document(item.report_document)
    if item.report_reference:
        loaded = source.load(item.report_reference)
        return validate_report_document(loaded)
    raise MalformedAssessmentReportError(
        "report_document or report_reference is required",
        reason_code="missing_report",
    )


def _apply_selection_and_dedupe(
    candidates: Sequence[NormalizedAssessmentSnapshot],
    *,
    policy: IntelligenceDatasetSelectionPolicy,
) -> tuple[list[NormalizedAssessmentSnapshot], list[DatasetIngestionDiagnostic]]:
    diagnostics: list[DatasetIngestionDiagnostic] = []
    by_key: dict[tuple[str, str, str], NormalizedAssessmentSnapshot] = {}

    for item in candidates:
        key = (item.repository_id, item.assessment_id, item.assessment_run_id)
        prior = by_key.get(key)
        if prior is None:
            by_key[key] = item
            continue
        if prior.canonical_report_digest == item.canonical_report_digest:
            # Exact duplicate — keep one.
            diagnostics.append(
                DatasetIngestionDiagnostic(
                    code="exact_duplicate_deduped",
                    message="Exact duplicate assessment digest deduped",
                    repository_id=item.repository_id,
                    assessment_id=item.assessment_id,
                    assessment_run_id=item.assessment_run_id,
                )
            )
            continue
        raise DuplicateAssessmentConflictError(
            "same assessment/run ID supplied with conflicting canonical digests",
            reason_code=ExclusionReason.DUPLICATE_CONFLICT.value,
        )

    unique = list(by_key.values())
    by_repo: dict[str, list[NormalizedAssessmentSnapshot]] = {}
    for item in unique:
        by_repo.setdefault(item.repository_id, []).append(item)

    selected: list[NormalizedAssessmentSnapshot] = []
    for repository_id, rows in sorted(by_repo.items()):
        rows = sorted(rows, key=lambda row: (row.assessment_run_id, row.assessment_id))
        if len(rows) == 1:
            selected.append(rows[0])
            continue

        chosen_run = policy.selected_assessment_runs.get(repository_id)
        explicitly_selected = [
            row
            for row in rows
            if chosen_run and row.assessment_run_id == chosen_run
        ]
        # Also honor input-level explicitly_selected via digest match of included rows.
        if not explicitly_selected:
            # Prefer a single INCLUDED non-rejected row only when policy names the run.
            pass

        if explicitly_selected:
            winner = explicitly_selected[0]
            selected.append(winner)
            for row in rows:
                if row is winner:
                    continue
                selected.append(
                    _with_inclusion(
                        row,
                        inclusion=InclusionStatus.EXCLUDED,
                        reason=ExclusionReason.SUPERSEDED_ASSESSMENT.value,
                    )
                )
            diagnostics.append(
                DatasetIngestionDiagnostic(
                    code="explicit_run_selected",
                    message=f"Selected assessment run {winner.assessment_run_id}",
                    repository_id=repository_id,
                    assessment_id=winner.assessment_id,
                    assessment_run_id=winner.assessment_run_id,
                )
            )
            continue

        # Fail closed — do not silently keep first/latest.
        if policy.failed_assessment_behavior is FailedAssessmentBehavior.FAIL_FAST:
            raise AmbiguousRepositoryAssessmentError(
                f"multiple assessment runs for repository {repository_id} without explicit selection",
                reason_code=ExclusionReason.AMBIGUOUS_RUN_SELECTION.value,
            )
        for row in rows:
            selected.append(
                _with_inclusion(
                    row,
                    inclusion=InclusionStatus.REJECTED,
                    reason=ExclusionReason.AMBIGUOUS_RUN_SELECTION.value,
                )
            )
        diagnostics.append(
            DatasetIngestionDiagnostic(
                code=ExclusionReason.AMBIGUOUS_RUN_SELECTION.value,
                message="Multiple assessment runs require explicit selection",
                repository_id=repository_id,
            )
        )

    # Preserve deterministic ordering.
    selected.sort(key=lambda row: (row.repository_id, row.assessment_id, row.assessment_run_id))
    return selected, diagnostics


def _with_inclusion(
    snapshot: NormalizedAssessmentSnapshot,
    *,
    inclusion: InclusionStatus,
    reason: str,
) -> NormalizedAssessmentSnapshot:
    return NormalizedAssessmentSnapshot(
        repository_id=snapshot.repository_id,
        assessment_id=snapshot.assessment_id,
        assessment_run_id=snapshot.assessment_run_id,
        workspace_id=snapshot.workspace_id,
        organization_id=snapshot.organization_id,
        assessment_schema_version=snapshot.assessment_schema_version,
        assessment_timestamp=snapshot.assessment_timestamp,
        source_type=snapshot.source_type,
        source_reference=snapshot.source_reference,
        pinned_revision=snapshot.pinned_revision,
        visibility=snapshot.visibility,
        display_name=snapshot.display_name,
        source_reference_publication_permitted=snapshot.source_reference_publication_permitted,
        enabled_assessment_heads=snapshot.enabled_assessment_heads,
        available_assessment_heads=snapshot.available_assessment_heads,
        disabled_assessment_heads=snapshot.disabled_assessment_heads,
        unavailable_assessment_heads=snapshot.unavailable_assessment_heads,
        missing_assessment_heads=snapshot.missing_assessment_heads,
        assessment_head_confidence=snapshot.assessment_head_confidence,
        assessment_coverage=snapshot.assessment_coverage,
        technology_refs=snapshot.technology_refs,
        finding_refs=snapshot.finding_refs,
        recommendation_refs=snapshot.recommendation_refs,
        priority_action_refs=snapshot.priority_action_refs,
        roadmap_refs=snapshot.roadmap_refs,
        correlation_refs=snapshot.correlation_refs,
        evidence_refs=snapshot.evidence_refs,
        canonical_report_reference=snapshot.canonical_report_reference,
        canonical_report_digest=snapshot.canonical_report_digest,
        ingestion_status=(
            IngestionStatus.EXCLUDED
            if inclusion is InclusionStatus.EXCLUDED
            else IngestionStatus.REJECTED
        ),
        inclusion_status=inclusion,
        traceability_status=snapshot.traceability_status,
        available_canonical_sections=snapshot.available_canonical_sections,
        website_export_eligibility=snapshot.website_export_eligibility,
        limitations=tuple(sorted(set(snapshot.limitations + (f"exclusion_reason:{reason}",)))),
        exclusion_reason=reason,
        diagnostics=snapshot.diagnostics,
    )


def _rejected_stub(
    item: AssessmentDatasetInput,
    error: IntelligenceReportingIngestionError,
) -> NormalizedAssessmentSnapshot:
    reason = error.reason_code or ExclusionReason.OTHER.value
    digest = hashlib_placeholder(item)
    return NormalizedAssessmentSnapshot(
        repository_id=item.repository_id or "repository:unknown",
        assessment_id=item.assessment_id or "assessment:unknown",
        assessment_run_id=item.assessment_run_id or "run:unknown",
        workspace_id=item.workspace_id,
        organization_id=item.organization_id,
        assessment_schema_version="unknown",
        source_type=item.source_type,
        source_reference=None,
        pinned_revision=item.pinned_revision,
        visibility=item.visibility,
        inclusion_status=InclusionStatus.REJECTED,
        ingestion_status=IngestionStatus.REJECTED,
        canonical_report_digest=digest,
        canonical_report_reference=item.report_reference,
        limitations=(f"rejection:{reason}",),
        exclusion_reason=reason,
        diagnostics=(reason,),
    )


def hashlib_placeholder(item: AssessmentDatasetInput) -> str:
    material = json.dumps(
        {
            "repository_id": item.repository_id,
            "assessment_id": item.assessment_id,
            "assessment_run_id": item.assessment_run_id,
            "error": True,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    import hashlib

    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _stable_diagnostics(
    diagnostics: Sequence[DatasetIngestionDiagnostic],
) -> list[DatasetIngestionDiagnostic]:
    return sorted(
        diagnostics,
        key=lambda item: (
            item.code,
            item.repository_id or "",
            item.assessment_id or "",
            item.assessment_run_id or "",
            item.message,
        ),
    )
