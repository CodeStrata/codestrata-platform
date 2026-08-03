"""Shared fixtures for commercial intelligence reporting domain tests."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.domain.dataset import (
    IntelligenceDataset,
    RepositoryAssessmentReference,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    InclusionStatus,
    ReportScope,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)


def make_ref(
    *,
    repository_id: str,
    assessment_id: str,
    assessment_run_id: str,
    visibility: DataVisibility = DataVisibility.ANONYMIZED,
    inclusion_status: InclusionStatus = InclusionStatus.INCLUDED,
    pinned_revision: str | None = "abc123",
    source_type: SourceType = SourceType.PUBLIC_OSS,
    source_reference: str | None = None,
    publication_permitted: bool = False,
    display_name: str | None = None,
) -> RepositoryAssessmentReference:
    return RepositoryAssessmentReference(
        repository_id=repository_id,
        assessment_id=assessment_id,
        assessment_run_id=assessment_run_id,
        source_type=source_type,
        assessment_schema_version="1.2",
        inclusion_status=inclusion_status,
        visibility=visibility,
        pinned_revision=pinned_revision,
        source_reference=source_reference,
        source_reference_publication_permitted=publication_permitted,
        display_name=display_name,
        canonical_report_reference=f"artifact:{assessment_id}:report_json",
    )


def make_dataset(
    refs: tuple[RepositoryAssessmentReference, ...] | None = None,
) -> IntelligenceDataset:
    assessments = refs or (
        make_ref(
            repository_id="repo:one",
            assessment_id="assessment:one",
            assessment_run_id="run:one",
        ),
        make_ref(
            repository_id="repo:two",
            assessment_id="assessment:two",
            assessment_run_id="run:two",
        ),
    )
    return IntelligenceDataset.create(
        name="Fixture dataset",
        selection_method="explicit_fixture",
        repository_assessments=assessments,
    )


def make_report(
    dataset: IntelligenceDataset | None = None,
    *,
    scope: ReportScope = ReportScope.INTERNAL_VALIDATION_DATASET,
) -> EngineeringIntelligenceReport:
    return EngineeringIntelligenceReport.create(
        title="Fixture Engineering Intelligence Report",
        report_scope=scope,
        dataset=dataset or make_dataset(),
    )
