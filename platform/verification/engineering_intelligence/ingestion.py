"""Build IntelligenceDataset / EIR from prepared assessments (no Engine re-analysis)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.intelligence_reporting.application.aggregation import (
    IntelligenceAggregationPolicy,
    VisibilityAggregationScope,
    aggregate_intelligence_dataset,
)
from codestrata_platform.intelligence_reporting.application.capability_comparison import (
    populate_report_capability_comparisons,
)
from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentDatasetInput,
    IntelligenceDatasetSelectionPolicy,
    SchemaCompatibilityPolicy,
)
from codestrata_platform.intelligence_reporting.application.ingestion import (
    ingest_assessment_dataset,
)
from codestrata_platform.intelligence_reporting.application.modernization_observations import (
    populate_report_modernization_observations,
)
from codestrata_platform.intelligence_reporting.application.recurring_patterns import (
    populate_report_recurring_patterns,
)
from codestrata_platform.intelligence_reporting.application.report_quality import (
    populate_report_quality,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns import (
    populate_report_repository_drilldowns,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution import (
    populate_report_technology_distribution,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    ReportScope,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)
from codestrata_platform.intelligence_reporting.domain.serialization import (
    report_to_stable_dict,
)
from codestrata_platform.intelligence_reporting.infrastructure.assessment_report_source import (
    InMemoryAssessmentReportSource,
)

from verification.engineering_intelligence.assessment_inputs import PreparedAssessment


@dataclass(frozen=True, slots=True)
class PipelineArtifacts:
    ingest_result: Any
    aggregation: Any
    report: EngineeringIntelligenceReport
    report_payload: dict[str, Any]
    source: InMemoryAssessmentReportSource


def assessments_to_inputs(
    assessments: list[PreparedAssessment] | tuple[PreparedAssessment, ...],
    *,
    source: InMemoryAssessmentReportSource | None = None,
    visibility: DataVisibility = DataVisibility.PUBLIC,
) -> tuple[list[AssessmentDatasetInput], InMemoryAssessmentReportSource]:
    report_source = source or InMemoryAssessmentReportSource()
    inputs: list[AssessmentDatasetInput] = []
    # Engine customer-safe projection — same authority as report serialization.
    try:
        from codestrata.security.customer_safe_text import (
            ensure_customer_safe_report_document,
        )
    except ImportError:  # pragma: no cover - monorepo layout required for SV runs
        ensure_customer_safe_report_document = None  # type: ignore[assignment]

    for item in assessments:
        document = item.report_document
        if ensure_customer_safe_report_document is not None:
            document = ensure_customer_safe_report_document(document)
        ref = f"artifact:{item.repository_id}:{item.qualified_revision[:12]}:report_json"
        report_source.put(ref, document)
        inputs.append(
            AssessmentDatasetInput(
                repository_id=f"repo:{item.repository_id}",
                assessment_id=f"assessment:{item.repository_id}:{item.qualified_revision[:8]}",
                assessment_run_id=f"run:{item.repository_id}:{item.report_digest[:8]}",
                report_document=document,
                report_reference=ref,
                source_type=SourceType.PUBLIC_OSS,
                visibility=visibility,
                pinned_revision=item.qualified_revision,
                source_reference=f"https://github.com/{item.github_repository}",
                source_reference_publication_permitted=visibility is DataVisibility.PUBLIC,
                display_name=item.project_name,
                explicitly_selected=True,
            )
        )
    return inputs, report_source


def build_pipeline_from_inputs(
    inputs: list[AssessmentDatasetInput],
    *,
    report_source: InMemoryAssessmentReportSource,
    title: str = "SV.6 Engineering Intelligence Verification",
    name: str = "sv6-verification-dataset",
) -> PipelineArtifacts:
    ingest = ingest_assessment_dataset(
        inputs,
        name=name,
        policy=IntelligenceDatasetSelectionPolicy(
            schema_compatibility_policy=SchemaCompatibilityPolicy.REQUIRE_1_2_COMPLETE,
            require_pinned_revision_for_public_oss=True,
        ),
        report_source=report_source,
        dataset_tags=("sv6_verification", "public_oss"),
    )
    if ingest.dataset is None:
        raise RuntimeError("ingestion produced no dataset")

    aggregation = aggregate_intelligence_dataset(
        dataset=ingest.dataset,
        snapshots=ingest.included,
        report_source=report_source,
        policy=IntelligenceAggregationPolicy(
            visibility_policy=VisibilityAggregationScope.PUBLIC_OSS
        ),
        comparability=ingest.comparability,
    )

    report = EngineeringIntelligenceReport.create(
        title=title,
        report_scope=ReportScope.PUBLIC_OSS_DATASET,
        dataset=ingest.dataset,
    )
    report = populate_report_technology_distribution(report, aggregation)
    report = populate_report_capability_comparisons(report, aggregation)
    report = populate_report_recurring_patterns(report, aggregation)
    report = populate_report_modernization_observations(report, aggregation)
    report = populate_report_quality(report, aggregation)
    report = populate_report_repository_drilldowns(report, aggregation)
    payload = report_to_stable_dict(report)
    return PipelineArtifacts(
        ingest_result=ingest,
        aggregation=aggregation,
        report=report,
        report_payload=payload,
        source=report_source,
    )


def build_pipeline_from_assessments(
    assessments: list[PreparedAssessment] | tuple[PreparedAssessment, ...],
    *,
    title: str = "SV.6 Engineering Intelligence Verification",
) -> PipelineArtifacts:
    inputs, source = assessments_to_inputs(assessments)
    return build_pipeline_from_inputs(inputs, report_source=source, title=title)
