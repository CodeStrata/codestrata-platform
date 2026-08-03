"""Build the public OSS Engineering Intelligence demonstration report."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from codestrata_platform.domain.errors import InvalidValueError
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
from codestrata_platform.intelligence_reporting.application.oss_demonstration.catalog import (
    OssDemonstrationCatalog,
    load_oss_demonstration_catalog,
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
from codestrata_platform.intelligence_reporting.application.website_export import (
    ExportScope,
    RepositoryIdentityPolicy,
    WebsiteExportBuildPolicy,
    WebsiteExportBundle,
    build_website_safe_export,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    ReportScope,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)
from codestrata_platform.intelligence_reporting.infrastructure.assessment_report_source import (
    InMemoryAssessmentReportSource,
)
from codestrata_platform.intelligence_reporting.infrastructure.static_export_writer import (
    StaticIntelligenceExportWriter,
    WriteResult,
)


def default_demo_directory() -> Path:
    """Resolve ``platform/demo`` relative to this package location."""

    # .../platform/src/codestrata_platform/intelligence_reporting/application/oss_demonstration
    platform_src = Path(__file__).resolve().parents[4]
    return platform_src.parent / "demo"


@dataclass(frozen=True, slots=True)
class OssDemonstrationResult:
    catalog: OssDemonstrationCatalog
    report: EngineeringIntelligenceReport
    export_bundle: WebsiteExportBundle
    write_result: WriteResult | None = None


def build_oss_demonstration_report(
    *,
    catalog_path: str | Path | None = None,
) -> OssDemonstrationResult:
    """Run slices 6.2–6.10 against the curated public OSS assessment fixtures."""

    catalog = load_oss_demonstration_catalog(
        catalog_path or (default_demo_directory() / "catalog.json")
    )
    inputs, source = _load_inputs(catalog)

    ingest_result = ingest_assessment_dataset(
        inputs,
        name=catalog.title,
        policy=IntelligenceDatasetSelectionPolicy(
            schema_compatibility_policy=SchemaCompatibilityPolicy.ALLOW_LEGACY_LIMITED,
            require_pinned_revision_for_public_oss=True,
        ),
        report_source=source,
        dataset_tags=("public_oss_demonstration", catalog.catalog_id),
    )
    if ingest_result.dataset is None:
        raise InvalidValueError(
            "OSS demonstration ingestion produced no dataset",
            reason_code="oss_demo_ingestion_empty",
        )
    if len(ingest_result.included) != len(catalog.repositories):
        codes = [item.code for item in ingest_result.diagnostics]
        raise InvalidValueError(
            "OSS demonstration ingestion did not include all catalog repositories: "
            f"included={len(ingest_result.included)} expected={len(catalog.repositories)} "
            f"diagnostics={codes}",
            reason_code="oss_demo_ingestion_incomplete",
        )

    aggregation = aggregate_intelligence_dataset(
        dataset=ingest_result.dataset,
        snapshots=ingest_result.included,
        report_source=source,
        policy=IntelligenceAggregationPolicy(
            visibility_policy=VisibilityAggregationScope.PUBLIC_OSS
        ),
        comparability=ingest_result.comparability,
    )

    export_policy = WebsiteExportBuildPolicy(
        export_scope=ExportScope.PUBLIC_OSS,
        repository_identity_policy=RepositoryIdentityPolicy.PUBLIC_WHEN_PERMITTED,
        include_methodology=True,
        include_limitations=True,
        include_public_source_links=False,
    )

    report = EngineeringIntelligenceReport.create(
        title=catalog.title,
        report_scope=ReportScope.PUBLIC_OSS_DATASET,
        dataset=ingest_result.dataset,
    )
    report = populate_report_technology_distribution(report, aggregation)
    report = populate_report_capability_comparisons(report, aggregation)
    report = populate_report_recurring_patterns(report, aggregation)
    report = populate_report_modernization_observations(report, aggregation)
    report = populate_report_quality(
        report, aggregation, website_export_policy=export_policy
    )
    report = populate_report_repository_drilldowns(report, aggregation)

    if len(report.repository_drilldowns) != len(catalog.repositories):
        raise InvalidValueError(
            "OSS demonstration must produce one drill-down per repository",
            reason_code="oss_demo_drilldown_count_mismatch",
        )

    export_bundle = build_website_safe_export(report, policy=export_policy)
    return OssDemonstrationResult(
        catalog=catalog,
        report=report,
        export_bundle=export_bundle,
    )


def generate_oss_demonstration_artifacts(
    *,
    catalog_path: str | Path | None = None,
    output_directory: str | Path | None = None,
    overwrite: bool = True,
) -> OssDemonstrationResult:
    """Build the demonstration report and write JSON/HTML/manifest artifacts."""

    result = build_oss_demonstration_report(catalog_path=catalog_path)
    target = Path(output_directory) if output_directory else result.catalog.root_directory
    write_result = StaticIntelligenceExportWriter().write(
        result.export_bundle,
        target,
        overwrite=overwrite,
    )
    return OssDemonstrationResult(
        catalog=result.catalog,
        report=result.report,
        export_bundle=result.export_bundle,
        write_result=write_result,
    )


def _load_inputs(
    catalog: OssDemonstrationCatalog,
) -> tuple[list[AssessmentDatasetInput], InMemoryAssessmentReportSource]:
    source = InMemoryAssessmentReportSource()
    inputs: list[AssessmentDatasetInput] = []
    root = catalog.root_directory
    for entry in catalog.repositories:
        report_file = (root / entry.report_path).resolve()
        if not str(report_file).startswith(str(root.resolve())):
            raise InvalidValueError(
                f"report path escapes demo directory: {entry.report_path}",
                reason_code="oss_demo_path_traversal",
            )
        if not report_file.is_file():
            raise InvalidValueError(
                f"assessment fixture missing: {report_file}",
                reason_code="oss_demo_fixture_missing",
            )
        document = json.loads(report_file.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise InvalidValueError(
                f"assessment fixture must be a JSON object: {entry.report_path}",
                reason_code="oss_demo_fixture_invalid",
            )
        schema = str(document.get("schema_version") or "")
        if schema != "1.2":
            raise InvalidValueError(
                f"assessment fixture schema must be 1.2, got {schema!r}",
                reason_code="oss_demo_schema_mismatch",
            )
        ref = f"artifact:{entry.assessment_id}:report_json"
        source.put(ref, document)
        inputs.append(
            AssessmentDatasetInput(
                repository_id=entry.repository_id,
                assessment_id=entry.assessment_id,
                assessment_run_id=entry.assessment_run_id,
                report_document=document,
                report_reference=ref,
                source_type=SourceType.PUBLIC_OSS,
                visibility=DataVisibility.PUBLIC,
                pinned_revision=entry.pinned_revision,
                source_reference=entry.source_reference,
                source_reference_publication_permitted=True,
                display_name=entry.display_name,
                explicitly_selected=True,
                dataset_tags=("public_oss_demonstration", entry.language),
                limitations=(
                    "curated_validation_dataset",
                    "non_representative_oss_selection",
                ),
            )
        )
    return inputs, source
