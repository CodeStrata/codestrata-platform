"""Deterministic stable serialization for commercial intelligence reports."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, fields, is_dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.domain._safety import reject_unsafe_text
from codestrata_platform.intelligence_reporting.domain.capability import (
    AssessmentHeadDistribution,
    CapabilityComparison,
    CapabilityDistribution,
    RepositoryCapabilitySnapshot,
)
from codestrata_platform.intelligence_reporting.domain.confidence import (
    IntelligenceReportConfidence,
)
from codestrata_platform.intelligence_reporting.domain.dataset import (
    AssessmentTimeRange,
    ExcludedRepository,
    IntelligenceDataset,
    RepositoryAssessmentReference,
)
from codestrata_platform.intelligence_reporting.domain.drilldown import (
    RepositoryIntelligenceDrilldown,
    SafeEntityRef,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ActivationStatus,
    ComparabilityStatus,
    ConfidenceLevel,
    CoverageStatus,
    DataVisibility,
    DerivationStatus,
    InclusionStatus,
    LimitationCategory,
    LimitationSeverity,
    ModernizationObservationCategory,
    PatternType,
    RatioStatus,
    ReportScope,
    SourceType,
    VersionState,
)
from codestrata_platform.intelligence_reporting.domain.identifiers import (
    DatasetId,
    DrilldownId,
    EngineeringIntelligenceReportId,
    LimitationId,
    ObservationId,
    PatternId,
)
from codestrata_platform.intelligence_reporting.domain.limitations import DatasetLimitation
from codestrata_platform.intelligence_reporting.domain.modernization import (
    ModernizationObservation,
)
from codestrata_platform.intelligence_reporting.domain.patterns import (
    RecurringIntelligencePattern,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
    EngineeringIntelligenceReport,
    GeneratedArtifactMetadata,
    MethodologyNotes,
    ReportExecutiveSummary,
)
from codestrata_platform.intelligence_reporting.domain.repository_snapshot import (
    RepositoryPopulation,
)
from codestrata_platform.intelligence_reporting.domain.technology import (
    Ratio,
    TechnologyDistribution,
    TechnologyDistributionObservation,
    TechnologyVersionObservation,
)


def to_stable_dict(value: object) -> Any:
    """Convert domain objects to JSON-safe, key-sorted structures."""

    if value is None or isinstance(value, (bool, int, float, str)):
        if isinstance(value, str) and value != "":
            # Empty strings are allowed for additive optional identity fields
            # (e.g. pre-6.8 reports without an interpretation-policy bundle).
            reject_unsafe_text(value, label="serialized_string")
        return value
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): to_stable_dict(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [to_stable_dict(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        # Opaque id wrappers (single `value: str` field) serialize as bare strings.
        dataclass_fields = fields(value)
        if (
            len(dataclass_fields) == 1
            and dataclass_fields[0].name == "value"
            and isinstance(getattr(value, "value"), str)
        ):
            return str(getattr(value, "value"))
        payload = {
            item.name: to_stable_dict(getattr(value, item.name)) for item in dataclass_fields
        }
        return {key: payload[key] for key in sorted(payload)}
    if hasattr(value, "value") and isinstance(getattr(value, "value"), str):
        return str(value.value)
    raise InvalidValueError(
        f"unsupported serialization type: {type(value)!r}",
        reason_code="unsupported_serialization_type",
    )


def from_stable_dict(payload: Mapping[str, Any]) -> EngineeringIntelligenceReport:
    """Round-trip EngineeringIntelligenceReport from a stable dictionary."""

    if not isinstance(payload, Mapping):
        raise InvalidValueError(
            "payload must be a mapping",
            reason_code="invalid_serialization_payload",
        )
    schema = str(payload.get("schema_version", ""))
    if schema != ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION:
        raise InvalidValueError(
            f"unsupported schema_version for round-trip: {schema}",
            reason_code="unsupported_eir_schema_version",
        )
    dataset = _dataset_from_dict(payload["dataset"])
    return EngineeringIntelligenceReport(
        report_id=EngineeringIntelligenceReportId(str(payload["report_id"])),
        schema_version=schema,
        title=str(payload["title"]),
        report_scope=ReportScope(str(payload["report_scope"])),
        dataset=dataset,
        executive_summary=_executive_from_dict(payload.get("executive_summary") or {}),
        repository_population=_population_from_dict(payload.get("repository_population") or {}),
        technology_distribution=_technology_from_dict(
            payload.get("technology_distribution") or {}
        ),
        capability_comparisons=tuple(
            _capability_from_dict(item)
            for item in (payload.get("capability_comparisons") or ())
        ),
        recurring_patterns=tuple(
            _pattern_from_dict(item) for item in (payload.get("recurring_patterns") or ())
        ),
        assessment_head_distributions=tuple(
            _head_dist_from_dict(item)
            for item in (payload.get("assessment_head_distributions") or ())
        ),
        modernization_observations=tuple(
            _observation_from_dict(item)
            for item in (payload.get("modernization_observations") or ())
        ),
        repository_drilldowns=tuple(
            _drilldown_from_dict(item) for item in (payload.get("repository_drilldowns") or ())
        ),
        confidence=_confidence_from_dict(payload.get("confidence") or {}),
        limitations=tuple(
            _limitation_from_dict(item) for item in (payload.get("limitations") or ())
        ),
        methodology=_methodology_from_dict(payload.get("methodology") or {}),
        generated_artifact_metadata=_artifact_meta_from_dict(
            payload.get("generated_artifact_metadata") or {}
        ),
        report_policy_version=str(
            payload.get("report_policy_version") or "intelligence-report-policy-v1"
        ),
        interpretation_policy_bundle_id=str(
            payload.get("interpretation_policy_bundle_id") or ""
        ),
    )


def report_to_stable_dict(report: EngineeringIntelligenceReport) -> dict[str, Any]:
    return to_stable_dict(report)


def _dataset_from_dict(payload: Mapping[str, Any]) -> IntelligenceDataset:
    assessments = tuple(
        RepositoryAssessmentReference(
            repository_id=str(item["repository_id"]),
            assessment_id=str(item["assessment_id"]),
            assessment_run_id=str(item["assessment_run_id"]),
            source_type=SourceType(str(item["source_type"])),
            assessment_schema_version=str(item["assessment_schema_version"]),
            inclusion_status=InclusionStatus(str(item["inclusion_status"])),
            visibility=DataVisibility(str(item["visibility"])),
            workspace_id=item.get("workspace_id"),
            source_reference=item.get("source_reference"),
            pinned_revision=item.get("pinned_revision"),
            assessment_timestamp=item.get("assessment_timestamp"),
            enabled_assessment_heads=tuple(item.get("enabled_assessment_heads") or ()),
            available_assessment_heads=tuple(item.get("available_assessment_heads") or ()),
            assessment_coverage_refs=tuple(item.get("assessment_coverage_refs") or ()),
            assessment_confidence_refs=tuple(item.get("assessment_confidence_refs") or ()),
            canonical_report_reference=item.get("canonical_report_reference"),
            display_name=item.get("display_name"),
            source_reference_publication_permitted=bool(
                item.get("source_reference_publication_permitted", False)
            ),
            path_exposure_permitted=bool(item.get("path_exposure_permitted", False)),
            evidence_exposure_permitted=bool(item.get("evidence_exposure_permitted", False)),
            limitations=tuple(item.get("limitations") or ()),
        )
        for item in (payload.get("repository_assessments") or ())
    )
    excluded = tuple(
        ExcludedRepository(repository_id=str(item["repository_id"]), reason=str(item["reason"]))
        for item in (payload.get("excluded_repositories") or ())
    )
    time_range = payload.get("assessment_time_range") or {}
    return IntelligenceDataset(
        dataset_id=DatasetId(str(payload["dataset_id"])),
        name=str(payload["name"]),
        selection_method=str(payload["selection_method"]),
        repository_count=int(payload["repository_count"]),
        repository_assessments=assessments,
        included_repository_ids=tuple(payload.get("included_repository_ids") or ()),
        excluded_repositories=excluded,
        assessment_schema_versions=tuple(payload.get("assessment_schema_versions") or ()),
        assessment_time_range=AssessmentTimeRange(
            earliest_assessment_timestamp=time_range.get("earliest_assessment_timestamp"),
            latest_assessment_timestamp=time_range.get("latest_assessment_timestamp"),
        ),
        source_type_distribution=dict(payload.get("source_type_distribution") or {}),
        dataset_tags=tuple(payload.get("dataset_tags") or ()),
        limitations=tuple(
            _limitation_from_dict(item) for item in (payload.get("limitations") or ())
        ),
        comparability_status=ComparabilityStatus(
            str(payload.get("comparability_status") or ComparabilityStatus.UNKNOWN.value)
        ),
        selection_policy_version=str(
            payload.get("selection_policy_version") or "intelligence-dataset-selection-v1"
        ),
    )


def _limitation_from_dict(payload: Mapping[str, Any]) -> DatasetLimitation:
    return DatasetLimitation(
        limitation_id=LimitationId(str(payload["limitation_id"])),
        category=LimitationCategory(str(payload["category"])),
        severity=LimitationSeverity(str(payload["severity"])),
        statement=str(payload["statement"]),
        affected_repository_ids=tuple(payload.get("affected_repository_ids") or ()),
        affected_assessment_head_ids=tuple(payload.get("affected_assessment_head_ids") or ()),
        affected_observation_ids=tuple(payload.get("affected_observation_ids") or ()),
        remediation_or_interpretation=payload.get("remediation_or_interpretation"),
        customer_visible=bool(payload.get("customer_visible", True)),
    )


def _executive_from_dict(payload: Mapping[str, Any]) -> ReportExecutiveSummary:
    return ReportExecutiveSummary(
        highlights=tuple(payload.get("highlights") or ()),
        repository_count=int(payload.get("repository_count") or 0),
        pattern_count=int(payload.get("pattern_count") or 0),
        modernization_observation_count=int(
            payload.get("modernization_observation_count") or 0
        ),
        confidence_level=ConfidenceLevel(
            str(payload.get("confidence_level") or ConfidenceLevel.UNAVAILABLE.value)
        ),
        limitation_count=int(payload.get("limitation_count") or 0),
    )


def _population_from_dict(payload: Mapping[str, Any]) -> RepositoryPopulation:
    return RepositoryPopulation(
        repository_count=int(payload.get("repository_count") or 0),
        source_type_counts=dict(payload.get("source_type_counts") or {}),
        language_presence_counts=dict(payload.get("language_presence_counts") or {}),
        ecosystem_presence_counts=dict(payload.get("ecosystem_presence_counts") or {}),
        size_tier_counts=dict(payload.get("size_tier_counts") or {}),
        assessment_head_availability_counts=dict(
            payload.get("assessment_head_availability_counts") or {}
        ),
        assessment_schema_version_counts=dict(
            payload.get("assessment_schema_version_counts") or {}
        ),
        included_repository_ids=tuple(payload.get("included_repository_ids") or ()),
        limitations=tuple(payload.get("limitations") or ()),
    )


def _ratio_from_dict(payload: Mapping[str, Any] | None) -> Ratio | None:
    if not payload:
        return None
    return Ratio(
        numerator=int(payload["numerator"]),
        denominator=int(payload["denominator"]),
        status=RatioStatus(str(payload["status"])),
        value=payload.get("value"),
    )


def _technology_from_dict(payload: Mapping[str, Any]) -> TechnologyDistribution:
    from codestrata_platform.intelligence_reporting.domain.technology import (
        TechnologyCategoryDistribution,
    )

    observations = []
    for item in payload.get("observations") or ():
        versions = tuple(
            TechnologyVersionObservation(
                version=row.get("version"),
                state=VersionState(str(row["state"])),
                repository_ids=tuple(row.get("repository_ids") or ()),
                occurrence_count=int(row.get("occurrence_count") or 0),
                source_assessment_ids=tuple(row.get("source_assessment_ids") or ()),
                limitations=tuple(row.get("limitations") or ()),
            )
            for row in (item.get("versions") or ())
        )
        observations.append(
            TechnologyDistributionObservation(
                technology_id=str(item["technology_id"]),
                normalized_name=str(item["normalized_name"]),
                category=str(item["category"]),
                repository_count=int(item["repository_count"]),
                repository_ratio=_ratio_from_dict(item["repository_ratio"]),  # type: ignore[arg-type]
                occurrence_count=int(item["occurrence_count"]),
                versions=versions,
                repository_ids=tuple(item.get("repository_ids") or ()),
                source_assessment_ids=tuple(item.get("source_assessment_ids") or ()),
                confidence=ConfidenceLevel(
                    str(item.get("confidence") or ConfidenceLevel.UNAVAILABLE.value)
                ),
                limitations=tuple(item.get("limitations") or ()),
                source_names=tuple(item.get("source_names") or ()),
            )
        )
    categories = tuple(
        TechnologyCategoryDistribution(
            category=str(item["category"]),
            technology_count=int(item.get("technology_count") or 0),
            repository_count=int(item.get("repository_count") or 0),
            observations=tuple(item.get("observations") or ()),
            denominator=int(item.get("denominator") or 0),
            limitations=tuple(item.get("limitations") or ()),
        )
        for item in (payload.get("category_distributions") or ())
    )
    return TechnologyDistribution(
        observations=tuple(observations),
        repository_denominator=int(payload.get("repository_denominator") or 0),
        limitations=tuple(payload.get("limitations") or ()),
        category_distributions=categories,
        policy_id=payload.get("policy_id"),
        eligible_repository_ids=tuple(payload.get("eligible_repository_ids") or ()),
        unavailable_repository_ids=tuple(payload.get("unavailable_repository_ids") or ()),
    )


def _capability_from_dict(payload: Mapping[str, Any]) -> CapabilityComparison:
    repos = tuple(
        RepositoryCapabilitySnapshot(
            repository_id=str(item["repository_id"]),
            assessment_id=str(item["assessment_id"]),
            assessment_head_id=str(item["assessment_head_id"]),
            activation_status=ActivationStatus(str(item["activation_status"])),
            coverage_status=CoverageStatus(str(item["coverage_status"])),
            confidence_level=ConfidenceLevel(str(item["confidence_level"])),
            finding_count=int(item.get("finding_count") or 0),
            recommendation_count=int(item.get("recommendation_count") or 0),
            priority_action_count=int(item.get("priority_action_count") or 0),
            highest_severity=item.get("highest_severity"),
            limitations=tuple(item.get("limitations") or ()),
            drilldown_ref=item.get("drilldown_ref"),
            comparable=bool(item.get("comparable", True)),
            legacy_limited=bool(item.get("legacy_limited", False)),
            assessment_run_id=item.get("assessment_run_id"),
        )
        for item in (payload.get("repositories") or ())
    )
    dist_payload = payload.get("distribution") or {}
    distribution = CapabilityDistribution(
        complete_count=int(dist_payload.get("complete_count") or 0),
        partial_count=int(dist_payload.get("partial_count") or 0),
        insufficient_evidence_count=int(dist_payload.get("insufficient_evidence_count") or 0),
        unavailable_count=int(dist_payload.get("unavailable_count") or 0),
        disabled_count=int(dist_payload.get("disabled_count") or 0),
        high_confidence_count=int(dist_payload.get("high_confidence_count") or 0),
        moderate_confidence_count=int(dist_payload.get("moderate_confidence_count") or 0),
        limited_confidence_count=int(dist_payload.get("limited_confidence_count") or 0),
        unavailable_confidence_count=int(
            dist_payload.get("unavailable_confidence_count") or 0
        ),
        not_applicable_count=int(dist_payload.get("not_applicable_count") or 0),
        missing_count=int(dist_payload.get("missing_count") or 0),
        legacy_limited_count=int(dist_payload.get("legacy_limited_count") or 0),
        comparable_count=int(dist_payload.get("comparable_count") or 0),
    )
    return CapabilityComparison(
        assessment_head_id=str(payload["assessment_head_id"]),
        repositories=repos,
        distribution=distribution,
        confidence=ConfidenceLevel(
            str(payload.get("confidence") or ConfidenceLevel.UNAVAILABLE.value)
        ),
        limitations=tuple(payload.get("limitations") or ()),
        comparable_repository_ids=tuple(payload.get("comparable_repository_ids") or ()),
        limited_repository_ids=tuple(payload.get("limited_repository_ids") or ()),
        excluded_repository_ids=tuple(payload.get("excluded_repository_ids") or ()),
        policy_id=payload.get("policy_id"),
        repositories_with_findings_count=int(
            payload.get("repositories_with_findings_count") or 0
        ),
    )


def _pattern_from_dict(payload: Mapping[str, Any]) -> RecurringIntelligencePattern:
    return RecurringIntelligencePattern(
        pattern_id=PatternId(str(payload["pattern_id"])),
        pattern_type=PatternType(str(payload["pattern_type"])),
        title=str(payload["title"]),
        statement=str(payload["statement"]),
        assessment_head_ids=tuple(payload.get("assessment_head_ids") or ()),
        rule_ids=tuple(payload.get("rule_ids") or ()),
        repository_ids=tuple(payload.get("repository_ids") or ()),
        assessment_ids=tuple(payload.get("assessment_ids") or ()),
        finding_ids=tuple(payload.get("finding_ids") or ()),
        recommendation_ids=tuple(payload.get("recommendation_ids") or ()),
        evidence_ids=tuple(payload.get("evidence_ids") or ()),
        repository_count=int(payload.get("repository_count") or 0),
        repository_ratio=_ratio_from_dict(payload.get("repository_ratio")),
        confidence=ConfidenceLevel(
            str(payload.get("confidence") or ConfidenceLevel.UNAVAILABLE.value)
        ),
        limitations=tuple(payload.get("limitations") or ()),
        drilldown_refs=tuple(payload.get("drilldown_refs") or ()),
        normalized_subject=str(payload.get("normalized_subject") or ""),
        policy_version=str(payload.get("policy_version") or "intelligence-pattern-policy-v1"),
        allow_single_repository=bool(payload.get("allow_single_repository", False)),
    )


def _observation_from_dict(payload: Mapping[str, Any]) -> ModernizationObservation:
    return ModernizationObservation(
        observation_id=ObservationId(str(payload["observation_id"])),
        title=str(payload["title"]),
        statement=str(payload["statement"]),
        category=ModernizationObservationCategory(str(payload["category"])),
        assessment_head_ids=tuple(payload.get("assessment_head_ids") or ()),
        repository_ids=tuple(payload.get("repository_ids") or ()),
        recommendation_ids=tuple(payload.get("recommendation_ids") or ()),
        priority_action_ids=tuple(payload.get("priority_action_ids") or ()),
        roadmap_initiative_ids=tuple(payload.get("roadmap_initiative_ids") or ()),
        supporting_finding_ids=tuple(payload.get("supporting_finding_ids") or ()),
        supporting_evidence_ids=tuple(payload.get("supporting_evidence_ids") or ()),
        repository_count=int(payload.get("repository_count") or 0),
        confidence=ConfidenceLevel(
            str(payload.get("confidence") or ConfidenceLevel.UNAVAILABLE.value)
        ),
        limitations=tuple(payload.get("limitations") or ()),
        drilldown_refs=tuple(payload.get("drilldown_refs") or ()),
        normalized_subject=str(payload.get("normalized_subject") or ""),
        policy_version=str(
            payload.get("policy_version") or "intelligence-modernization-observation-v1"
        ),
    )


def _head_dist_from_dict(payload: Mapping[str, Any]) -> AssessmentHeadDistribution:
    return AssessmentHeadDistribution(
        assessment_head_id=str(payload["assessment_head_id"]),
        repository_count=int(payload.get("repository_count") or 0),
        activated_count=int(payload.get("activated_count") or 0),
        complete_coverage_count=int(payload.get("complete_coverage_count") or 0),
        partial_coverage_count=int(payload.get("partial_coverage_count") or 0),
        insufficient_evidence_count=int(payload.get("insufficient_evidence_count") or 0),
        unavailable_count=int(payload.get("unavailable_count") or 0),
        disabled_count=int(payload.get("disabled_count") or 0),
        finding_count=int(payload.get("finding_count") or 0),
        recommendation_count=int(payload.get("recommendation_count") or 0),
        priority_action_count=int(payload.get("priority_action_count") or 0),
        repositories_with_findings_count=int(
            payload.get("repositories_with_findings_count") or 0
        ),
        severity_distribution=tuple(
            (str(k), int(v)) for k, v in (payload.get("severity_distribution") or ())
        ),
        confidence_distribution=tuple(
            (str(k), int(v)) for k, v in (payload.get("confidence_distribution") or ())
        ),
        limitations=tuple(payload.get("limitations") or ()),
    )


def _safe_entity_refs_from_dict(items: object) -> tuple[SafeEntityRef, ...]:
    return tuple(
        SafeEntityRef(
            entity_id=str(item["entity_id"]),
            assessment_id=str(item["assessment_id"]),
            entity_kind=str(item["entity_kind"]),
            label=item.get("label"),
        )
        for item in (items or ())
    )


def _drilldown_from_dict(payload: Mapping[str, Any]) -> RepositoryIntelligenceDrilldown:
    finding_refs = _safe_entity_refs_from_dict(payload.get("finding_refs"))
    recommendation_refs = _safe_entity_refs_from_dict(payload.get("recommendation_refs"))
    priority_action_refs = _safe_entity_refs_from_dict(payload.get("priority_action_refs"))
    roadmap_refs = _safe_entity_refs_from_dict(payload.get("roadmap_refs"))
    correlation_refs = _safe_entity_refs_from_dict(payload.get("correlation_refs"))
    snaps = tuple(
        RepositoryCapabilitySnapshot(
            repository_id=str(item["repository_id"]),
            assessment_id=str(item["assessment_id"]),
            assessment_head_id=str(item["assessment_head_id"]),
            activation_status=ActivationStatus(str(item["activation_status"])),
            coverage_status=CoverageStatus(str(item["coverage_status"])),
            confidence_level=ConfidenceLevel(str(item["confidence_level"])),
            finding_count=int(item.get("finding_count") or 0),
            recommendation_count=int(item.get("recommendation_count") or 0),
            priority_action_count=int(item.get("priority_action_count") or 0),
            highest_severity=item.get("highest_severity"),
            limitations=tuple(item.get("limitations") or ()),
            drilldown_ref=item.get("drilldown_ref"),
            comparable=bool(item.get("comparable", True)),
            legacy_limited=bool(item.get("legacy_limited", False)),
            assessment_run_id=item.get("assessment_run_id"),
        )
        for item in (payload.get("assessment_head_snapshots") or ())
    )
    return RepositoryIntelligenceDrilldown(
        drilldown_id=DrilldownId(str(payload["drilldown_id"])),
        repository_id=str(payload["repository_id"]),
        assessment_id=str(payload["assessment_id"]),
        display_name=str(payload["display_name"]),
        source_type=SourceType(str(payload["source_type"])),
        visibility=DataVisibility(str(payload["visibility"])),
        technology_summary=tuple(payload.get("technology_summary") or ()),
        assessment_head_snapshots=snaps,
        recurring_pattern_ids=tuple(payload.get("recurring_pattern_ids") or ()),
        modernization_observation_ids=tuple(
            payload.get("modernization_observation_ids") or ()
        ),
        highest_priority_action_ids=tuple(payload.get("highest_priority_action_ids") or ()),
        finding_refs=finding_refs,
        recommendation_refs=recommendation_refs,
        confidence=ConfidenceLevel(
            str(payload.get("confidence") or ConfidenceLevel.UNAVAILABLE.value)
        ),
        limitations=tuple(payload.get("limitations") or ()),
        canonical_assessment_report_ref=payload.get("canonical_assessment_report_ref"),
        assessment_run_id=str(payload.get("assessment_run_id") or ""),
        dataset_id=str(payload.get("dataset_id") or ""),
        canonical_report_digest=str(payload.get("canonical_report_digest") or ""),
        policy_id=str(payload.get("policy_id") or ""),
        priority_action_refs=priority_action_refs,
        roadmap_refs=roadmap_refs,
        correlation_refs=correlation_refs,
        public_export_eligible=bool(payload.get("public_export_eligible", False)),
        requires_anonymization=bool(payload.get("requires_anonymization", False)),
        website_export_blocking_reasons=tuple(
            payload.get("website_export_blocking_reasons") or ()
        ),
    )


def _confidence_from_dict(payload: Mapping[str, Any]) -> IntelligenceReportConfidence:
    return IntelligenceReportConfidence(
        level=ConfidenceLevel(str(payload.get("level") or ConfidenceLevel.UNAVAILABLE.value)),
        basis=tuple(payload.get("basis") or ()),
        repository_sample_count=int(payload.get("repository_sample_count") or 0),
        comparable_repository_count=int(payload.get("comparable_repository_count") or 0),
        assessment_schema_compatibility=ComparabilityStatus(
            str(
                payload.get("assessment_schema_compatibility")
                or ComparabilityStatus.UNKNOWN.value
            )
        ),
        dataset_coverage_status=CoverageStatus(
            str(payload.get("dataset_coverage_status") or CoverageStatus.UNAVAILABLE.value)
        ),
        weakest_material_source_confidence=ConfidenceLevel(
            str(
                payload.get("weakest_material_source_confidence")
                or ConfidenceLevel.UNAVAILABLE.value
            )
        ),
        limitations=tuple(payload.get("limitations") or ()),
        derivation_status=DerivationStatus(
            str(payload.get("derivation_status") or DerivationStatus.DEFERRED.value)
        ),
    )


def _methodology_from_dict(payload: Mapping[str, Any]) -> MethodologyNotes:
    return MethodologyNotes(
        notes=tuple(payload.get("notes") or ()),
        engine_assessment_schema_version=str(
            payload.get("engine_assessment_schema_version") or "1.2"
        ),
        report_schema_version=str(
            payload.get("report_schema_version")
            or ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION
        ),
        methodology_id=str(
            payload.get("methodology_id") or "intelligence-report-methodology"
        ),
        methodology_version=str(payload.get("methodology_version") or "v1"),
        interpretation_policy_bundle_id=str(
            payload.get("interpretation_policy_bundle_id") or ""
        ),
        aggregation_policy_id=str(payload.get("aggregation_policy_id") or ""),
        oss_disclaimer=str(
            payload.get("oss_disclaimer")
            or MethodologyNotes().oss_disclaimer
        ),
    )


def _artifact_meta_from_dict(payload: Mapping[str, Any]) -> GeneratedArtifactMetadata:
    return GeneratedArtifactMetadata(
        artifact_kinds=tuple(payload.get("artifact_kinds") or ()),
        content_hashes=tuple(payload.get("content_hashes") or ()),
        generator_version=payload.get("generator_version"),
    )


# Silence unused import lint for asdict if unused
_ = asdict
