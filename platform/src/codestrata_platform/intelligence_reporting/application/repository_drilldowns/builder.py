"""Build bounded RepositoryIntelligenceDrilldown objects."""

from __future__ import annotations

from dataclasses import replace

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    CrossRepositoryAggregation,
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.application.contracts import (
    WebsiteExportEligibility,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns.capabilities import (
    head_limitations,
    snapshots_for_repository,
    weakest_material_head_confidence,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns.diagnostics import (
    RepositoryDrilldownDiagnostics,
    RepositoryDrilldownResult,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns.entity_refs import (
    select_entity_refs,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns.modernization import (
    observation_ids_for_repository,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns.patterns import (
    pattern_ids_for_repository,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns.policy import (
    RepositoryDrilldownPolicy,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns.repository_index import (
    select_included_repositories,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns.technology import (
    build_technology_summary,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns.validation import (
    validate_repository_drilldowns,
)
from codestrata_platform.intelligence_reporting.domain.dataset import (
    RepositoryAssessmentReference,
)
from codestrata_platform.intelligence_reporting.domain.drilldown import (
    RepositoryIntelligenceDrilldown,
)
from codestrata_platform.intelligence_reporting.domain.enums import DataVisibility
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)


def build_repository_drilldowns(
    report: EngineeringIntelligenceReport,
    aggregation: CrossRepositoryAggregation,
    *,
    policy: RepositoryDrilldownPolicy | None = None,
) -> RepositoryDrilldownResult:
    """Build one bounded drill-down per included repository."""

    active = policy or RepositoryDrilldownPolicy(
        visibility_policy=_infer_visibility_scope(aggregation)
    )
    selected = select_included_repositories(
        report.dataset,
        aggregation,
        policy=active,
        report_scope=report.report_scope,
    )
    dataset_id = report.dataset.dataset_id.value
    drilldowns: list[RepositoryIntelligenceDrilldown] = []
    tech_count = 0
    head_count = 0
    finding_count = 0
    rec_count = 0
    pa_count = 0
    roadmap_count = 0
    corr_count = 0
    pattern_count = 0
    observation_count = 0
    truncated = 0
    legacy_count = 0
    export_eligible = 0
    anon_required = 0
    diag_limitations: list[str] = list(active.limitations)

    for item in selected:
        record = item.record
        ref = item.reference
        tech_summary, tech_limits = build_technology_summary(
            aggregation, repository_id=record.repository_id, policy=active
        )
        snaps = snapshots_for_repository(
            report.capability_comparisons,
            repository_id=record.repository_id,
            policy=active,
        )
        pattern_ids, pattern_limits = pattern_ids_for_repository(
            report.recurring_patterns,
            repository_id=record.repository_id,
            policy=active,
        )
        observation_ids, observation_limits = observation_ids_for_repository(
            report.modernization_observations,
            repository_id=record.repository_id,
            policy=active,
        )
        entities = select_entity_refs(
            aggregation,
            repository_id=record.repository_id,
            assessment_id=record.assessment_id,
            policy=active,
        )
        confidence = weakest_material_head_confidence(snaps)
        eligibility = _website_eligibility(ref)
        limitations = list(tech_limits)
        limitations.extend(pattern_limits)
        limitations.extend(observation_limits)
        limitations.extend(entities.limitations)
        limitations.extend(head_limitations(snaps))
        if item.legacy_limited:
            limitations.append("legacy_or_incomplete_source_assessment")
            legacy_count += 1
        if not (ref.pinned_revision or "").strip() and ref.visibility is DataVisibility.PUBLIC:
            limitations.append("missing_pinned_revision")
        if ref.visibility is DataVisibility.ANONYMIZED:
            limitations.append("anonymized_source_identity")
        if ref.visibility in {DataVisibility.CUSTOMER_PRIVATE, DataVisibility.INTERNAL}:
            limitations.append("private_or_internal_source")
        limitations.append("cross_sectional_snapshot_only")
        limitations.append("repository_drilldown_is_navigation_not_a_scorecard")
        limitations.append(
            "canonical_assessment_report_required_for_full_evidence_details"
        )
        for limitation in report.limitations:
            if (
                not limitation.affected_repository_ids
                or record.repository_id in limitation.affected_repository_ids
            ) and limitation.category.value in {
                "non_temporal_dataset",
                "selection_bias",
                "missing_revision",
                "legacy_source",
                "assessment_coverage",
                "assessment_confidence",
            }:
                limitations.append(f"report_limitation:{limitation.category.value}")

        if any("truncated" in note for note in limitations):
            truncated += 1

        canonical_ref = _opaque_canonical_ref(
            record.canonical_report_reference,
            assessment_id=record.assessment_id,
            digest=record.canonical_report_digest,
        )
        provisional = RepositoryIntelligenceDrilldown.create(
            repository_id=record.repository_id,
            assessment_id=record.assessment_id,
            display_name=item.display_name,
            source_type=record.source_type,
            visibility=record.visibility,
            technology_summary=tech_summary,
            assessment_head_snapshots=snaps,
            recurring_pattern_ids=pattern_ids,
            modernization_observation_ids=observation_ids,
            highest_priority_action_ids=entities.highest_priority_action_ids,
            finding_refs=entities.finding_refs,
            recommendation_refs=entities.recommendation_refs,
            confidence=confidence,
            limitations=tuple(sorted(set(limitations))),
            canonical_assessment_report_ref=canonical_ref,
            assessment_run_id=record.assessment_run_id,
            dataset_id=dataset_id,
            canonical_report_digest=record.canonical_report_digest,
            policy_id=active.policy_token,
            priority_action_refs=entities.priority_action_refs,
            roadmap_refs=entities.roadmap_refs,
            correlation_refs=entities.correlation_refs,
            public_export_eligible=eligibility.eligible,
            requires_anonymization=eligibility.requires_anonymization,
            website_export_blocking_reasons=eligibility.blocking_reasons,
        )
        bound_snaps = tuple(
            replace(snap, drilldown_ref=provisional.drilldown_id.value) for snap in snaps
        )
        drilldown = replace(provisional, assessment_head_snapshots=bound_snaps)
        drilldowns.append(drilldown)

        tech_count += len(tech_summary)
        head_count += len(bound_snaps)
        finding_count += len(entities.finding_refs)
        rec_count += len(entities.recommendation_refs)
        pa_count += len(entities.priority_action_refs)
        roadmap_count += len(entities.roadmap_refs)
        corr_count += len(entities.correlation_refs)
        pattern_count += len(pattern_ids)
        observation_count += len(observation_ids)
        if eligibility.eligible:
            export_eligible += 1
        if eligibility.requires_anonymization:
            anon_required += 1

    diagnostics = RepositoryDrilldownDiagnostics(
        included_repository_count=len(report.dataset.included_repository_ids),
        drilldown_count=len(drilldowns),
        technology_ref_count=tech_count,
        head_snapshot_count=head_count,
        finding_ref_count=finding_count,
        recommendation_ref_count=rec_count,
        priority_action_ref_count=pa_count,
        roadmap_ref_count=roadmap_count,
        correlation_ref_count=corr_count,
        pattern_membership_count=pattern_count,
        modernization_membership_count=observation_count,
        truncated_repository_count=truncated,
        legacy_limited_repository_count=legacy_count,
        public_export_eligible_count=export_eligible,
        anonymization_required_count=anon_required,
        unresolved_reference_count=0,
        limitations=tuple(sorted(set(diag_limitations))),
    )
    return RepositoryDrilldownResult(
        drilldowns=tuple(drilldowns),
        diagnostics=diagnostics,
        policy_token=active.policy_token,
    )


def populate_report_repository_drilldowns(
    report: EngineeringIntelligenceReport,
    aggregation: CrossRepositoryAggregation,
    *,
    policy: RepositoryDrilldownPolicy | None = None,
) -> EngineeringIntelligenceReport:
    """Populate repository_drilldowns; preserve prior EIR sections and quality."""

    result = build_repository_drilldowns(report, aggregation, policy=policy)
    populated = EngineeringIntelligenceReport.create(
        title=report.title,
        report_scope=report.report_scope,
        dataset=report.dataset,
        executive_summary=report.executive_summary,
        repository_population=report.repository_population,
        technology_distribution=report.technology_distribution,
        capability_comparisons=report.capability_comparisons,
        recurring_patterns=report.recurring_patterns,
        assessment_head_distributions=report.assessment_head_distributions,
        modernization_observations=report.modernization_observations,
        repository_drilldowns=result.drilldowns,
        confidence=report.confidence,
        limitations=report.limitations,
        methodology=report.methodology,
        generated_artifact_metadata=report.generated_artifact_metadata,
        report_policy_version=report.report_policy_version,
        schema_version=report.schema_version,
        interpretation_policy_bundle_id=report.interpretation_policy_bundle_id,
    )
    validate_repository_drilldowns(
        populated, aggregation, diagnostics=result.diagnostics
    )
    return populated


def _website_eligibility(ref: RepositoryAssessmentReference) -> WebsiteExportEligibility:
    """Local precheck mirroring Slice 6.2 rules without requiring AssessmentDatasetInput."""

    blocking: list[str] = []
    requires_anonymization = ref.visibility is not DataVisibility.PUBLIC
    if ref.visibility in {DataVisibility.CUSTOMER_PRIVATE, DataVisibility.INTERNAL}:
        blocking.append("private_repository_identity")
        requires_anonymization = True
    if ref.visibility is DataVisibility.PUBLIC and (
        not ref.source_reference_publication_permitted
    ):
        blocking.append("missing_publication_permission")
    source = ref.source_reference or ""
    if source.startswith("file://") or source.startswith("/") or source.startswith("\\"):
        blocking.append("unsafe_source_reference")
    eligible = not blocking and ref.visibility is DataVisibility.PUBLIC
    return WebsiteExportEligibility(
        eligible=eligible,
        requires_anonymization=requires_anonymization,
        blocking_reasons=tuple(sorted(set(blocking))),
        limitations=(),
    )


def _opaque_canonical_ref(
    reference: str | None,
    *,
    assessment_id: str,
    digest: str,
) -> str:
    raw = (reference or "").strip()
    lowered = raw.lower()
    if (
        raw
        and not lowered.startswith("file:")
        and "/users/" not in lowered
        and "/tmp/" not in lowered
        and "://" not in lowered
    ):
        base = raw
    else:
        base = f"artifact:{assessment_id}:report_json"
    digest_part = (digest or "").strip()
    if digest_part:
        return f"{base}#digest:{digest_part}"
    return base


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
