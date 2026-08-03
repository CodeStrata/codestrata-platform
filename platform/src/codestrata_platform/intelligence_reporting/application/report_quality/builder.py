"""Build report confidence, limitations, and interpretation-policy bundle."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    CrossRepositoryAggregation,
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.application.capability_comparison.policy import (
    CapabilityComparisonPolicy,
)
from codestrata_platform.intelligence_reporting.application.modernization_observations.policy import (
    ModernizationObservationPolicy,
)
from codestrata_platform.intelligence_reporting.application.recurring_patterns.policy import (
    RecurringPatternPolicy,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns.policy import (
    RepositoryDrilldownPolicy,
)
from codestrata_platform.intelligence_reporting.application.website_export.policy import (
    WebsiteExportBuildPolicy,
)
from codestrata_platform.intelligence_reporting.application.report_quality.comparability import (
    summarize_comparability,
)
from codestrata_platform.intelligence_reporting.application.report_quality.confidence import (
    derive_report_confidence,
    evaluate_material_sections,
    weakest_material_source_confidence,
)
from codestrata_platform.intelligence_reporting.application.report_quality.coverage import (
    summarize_dataset_coverage,
)
from codestrata_platform.intelligence_reporting.application.report_quality.diagnostics import (
    ReportQualityDiagnostics,
)
from codestrata_platform.intelligence_reporting.application.report_quality.limitations import (
    build_report_limitations,
    dedupe_limitations,
)
from codestrata_platform.intelligence_reporting.application.report_quality.policy import (
    CatalogVersions,
    IntelligenceInterpretationPolicyBundle,
    ReportQualityPolicy,
    build_interpretation_policy_bundle,
)
from codestrata_platform.intelligence_reporting.application.report_quality.validation import (
    validate_report_quality,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution.diagnostics import (
    TechnologyDistributionPolicy,
)
from codestrata_platform.intelligence_reporting.domain.confidence import (
    IntelligenceReportConfidence,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    LimitationSeverity,
)
from codestrata_platform.intelligence_reporting.domain.limitations import DatasetLimitation
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
    MethodologyNotes,
    ReportExecutiveSummary,
)


@dataclass(frozen=True, slots=True)
class ReportQualityResult:
    confidence: IntelligenceReportConfidence
    limitations: tuple[DatasetLimitation, ...]
    methodology: MethodologyNotes
    bundle: IntelligenceInterpretationPolicyBundle
    diagnostics: ReportQualityDiagnostics
    policy_token: str


def build_report_quality(
    report: EngineeringIntelligenceReport,
    aggregation: CrossRepositoryAggregation,
    *,
    policy: ReportQualityPolicy | None = None,
    technology_policy: TechnologyDistributionPolicy | None = None,
    capability_policy: CapabilityComparisonPolicy | None = None,
    recurring_pattern_policy: RecurringPatternPolicy | None = None,
    modernization_policy: ModernizationObservationPolicy | None = None,
    repository_drilldown_policy: RepositoryDrilldownPolicy | None = None,
    website_export_policy: WebsiteExportBuildPolicy | None = None,
    catalog_versions: CatalogVersions | None = None,
) -> ReportQualityResult:
    """Derive report confidence, limitations, and interpretation-policy bundle."""

    visibility = _infer_visibility_scope(aggregation)
    quality_policy = policy or ReportQualityPolicy(visibility_policy=visibility)
    tech_policy = technology_policy or TechnologyDistributionPolicy(
        visibility_policy=visibility
    )
    cap_policy = capability_policy or CapabilityComparisonPolicy(
        visibility_policy=visibility
    )
    pattern_policy = recurring_pattern_policy or RecurringPatternPolicy(
        visibility_policy=visibility
    )
    modern_policy = modernization_policy or ModernizationObservationPolicy(
        visibility_policy=visibility
    )
    drilldown_policy = repository_drilldown_policy or RepositoryDrilldownPolicy(
        visibility_policy=visibility
    )
    export_policy = website_export_policy or WebsiteExportBuildPolicy.for_report_scope(
        report.report_scope
    )

    bundle = build_interpretation_policy_bundle(
        technology_policy_token=tech_policy.policy_token,
        capability_policy_token=cap_policy.policy_token,
        recurring_pattern_policy_token=pattern_policy.policy_token,
        modernization_policy_token=modern_policy.policy_token,
        report_quality_policy_token=quality_policy.policy_token,
        repository_drilldown_policy_token=drilldown_policy.policy_token,
        website_export_policy_token=export_policy.policy_token,
        catalog_versions=catalog_versions,
    )

    coverage = summarize_dataset_coverage(report.capability_comparisons)
    comparability = summarize_comparability(report, aggregation)
    weakest = weakest_material_source_confidence(report)

    raw_limitations = build_report_limitations(
        report,
        aggregation,
        policy=quality_policy,
        coverage=coverage,
        comparability=comparability,
        weakest_material_confidence=weakest,
    )
    limitations = dedupe_limitations(raw_limitations)
    raw_count = len(raw_limitations)

    confidence = derive_report_confidence(
        report,
        policy=quality_policy,
        coverage=coverage,
        comparability=comparability,
        limitations=limitations,
    )

    (
        material_count,
        supported_material,
        unavailable_material,
        small_sample_sections,
        _,
    ) = evaluate_material_sections(report, policy=quality_policy, coverage=coverage)

    material_lim = sum(
        1 for item in limitations if item.severity is LimitationSeverity.MATERIAL
    )
    moderate_lim = sum(
        1 for item in limitations if item.severity is LimitationSeverity.MODERATE
    )

    schema_versions = comparability.schema_versions or ("1.2",)
    methodology = MethodologyNotes(
        notes=(
            "Report confidence uses weakest-material-support with explicit caps.",
            "Results must not be generalized beyond the selected dataset.",
            "Report confidence is not an accuracy percentage or repository score.",
        ),
        engine_assessment_schema_version=schema_versions[0],
        methodology_id="intelligence-report-methodology",
        methodology_version="v1",
        interpretation_policy_bundle_id=bundle.bundle_id,
        aggregation_policy_id=f"{aggregation.policy_id}:{aggregation.policy_version}",
    )

    diagnostics = ReportQualityDiagnostics(
        included_repository_count=comparability.included_repository_count,
        comparable_repository_count=comparability.comparable_repository_count,
        canonical_repository_count=comparability.canonical_repository_count,
        legacy_repository_count=comparability.legacy_repository_count,
        material_section_count=material_count,
        supported_material_section_count=supported_material,
        unavailable_material_section_count=unavailable_material,
        small_sample_section_count=small_sample_sections,
        limitation_count=len(limitations),
        material_limitation_count=material_lim,
        moderate_limitation_count=moderate_lim,
        report_confidence_level=confidence.level.value,
        policy_bundle_id=bundle.bundle_id,
        unresolved_reference_count=0,
        deduplicated_limitation_count=raw_count - len(limitations),
        limitations=tuple(item.limitation_id.value for item in limitations),
    )

    return ReportQualityResult(
        confidence=confidence,
        limitations=limitations,
        methodology=methodology,
        bundle=bundle,
        diagnostics=diagnostics,
        policy_token=quality_policy.policy_token,
    )


def populate_report_quality(
    report: EngineeringIntelligenceReport,
    aggregation: CrossRepositoryAggregation,
    *,
    policy: ReportQualityPolicy | None = None,
    technology_policy: TechnologyDistributionPolicy | None = None,
    capability_policy: CapabilityComparisonPolicy | None = None,
    recurring_pattern_policy: RecurringPatternPolicy | None = None,
    modernization_policy: ModernizationObservationPolicy | None = None,
    repository_drilldown_policy: RepositoryDrilldownPolicy | None = None,
    website_export_policy: WebsiteExportBuildPolicy | None = None,
    catalog_versions: CatalogVersions | None = None,
) -> EngineeringIntelligenceReport:
    """Populate confidence, limitations, methodology, and policy-bundle identity."""

    result = build_report_quality(
        report,
        aggregation,
        policy=policy,
        technology_policy=technology_policy,
        capability_policy=capability_policy,
        recurring_pattern_policy=recurring_pattern_policy,
        modernization_policy=modernization_policy,
        repository_drilldown_policy=repository_drilldown_policy,
        website_export_policy=website_export_policy,
        catalog_versions=catalog_versions,
    )

    executive = ReportExecutiveSummary(
        highlights=report.executive_summary.highlights,
        repository_count=report.dataset.repository_count,
        pattern_count=len(report.recurring_patterns),
        modernization_observation_count=len(report.modernization_observations),
        confidence_level=result.confidence.level,
        limitation_count=len(result.limitations),
    )

    populated = EngineeringIntelligenceReport.create(
        title=report.title,
        report_scope=report.report_scope,
        dataset=report.dataset,
        executive_summary=executive,
        repository_population=report.repository_population,
        technology_distribution=report.technology_distribution,
        capability_comparisons=report.capability_comparisons,
        recurring_patterns=report.recurring_patterns,
        assessment_head_distributions=report.assessment_head_distributions,
        modernization_observations=report.modernization_observations,
        repository_drilldowns=report.repository_drilldowns,
        confidence=result.confidence,
        limitations=result.limitations,
        methodology=result.methodology,
        generated_artifact_metadata=report.generated_artifact_metadata,
        report_policy_version=report.report_policy_version,
        schema_version=report.schema_version,
        interpretation_policy_bundle_id=result.bundle.bundle_id,
    )

    validate_report_quality(
        populated,
        diagnostics=result.diagnostics,
        bundle=result.bundle,
        raw_limitation_count=len(result.limitations)
        + result.diagnostics.deduplicated_limitation_count,
    )
    return populated


def _infer_visibility_scope(
    aggregation: CrossRepositoryAggregation,
) -> VisibilityAggregationScope:
    vis = {item.visibility for item in aggregation.repository_index}
    if vis == {DataVisibility.PUBLIC}:
        return VisibilityAggregationScope.PUBLIC_OSS
    if DataVisibility.CUSTOMER_PRIVATE in vis or DataVisibility.INTERNAL in vis:
        if DataVisibility.PUBLIC in vis:
            return VisibilityAggregationScope.MIXED_INTERNAL
        return VisibilityAggregationScope.CUSTOMER_PRIVATE
    return VisibilityAggregationScope.MIXED_INTERNAL
