"""Project EngineeringIntelligenceReport → WebsiteSafeExportDocument."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.website_export.models import (
    SafeCapabilityRow,
    SafeConfidenceBlock,
    SafeDrilldownSection,
    SafeEntityItem,
    SafeExportMetadata,
    SafeHeadDistributionRow,
    SafeLimitationItem,
    SafeMethodologyBlock,
    SafeObservationItem,
    SafePatternItem,
    SafeTechnologyRow,
    WebsiteSafeExportDocument,
)
from codestrata_platform.intelligence_reporting.application.website_export.policy import (
    ExportScope,
    RepositoryIdentityPolicy,
    WebsiteExportBuildPolicy,
)
from codestrata_platform.intelligence_reporting.domain._safety import reject_unsafe_text
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    ReportScope,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)


def build_export_id(
    *,
    source_report_id: str,
    interpretation_policy_bundle_id: str,
    export_policy_token: str,
    export_schema_version: str,
    artifact_template_version: str,
) -> str:
    material = json.dumps(
        {
            "source_report_id": source_report_id.strip(),
            "interpretation_policy_bundle_id": interpretation_policy_bundle_id.strip(),
            "export_policy_token": export_policy_token.strip(),
            "export_schema_version": export_schema_version.strip(),
            "artifact_template_version": artifact_template_version.strip(),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
    return f"eir-export:{digest}"


def project_website_safe_export(
    report: EngineeringIntelligenceReport,
    *,
    policy: WebsiteExportBuildPolicy,
    generated_at: str | None = None,
) -> WebsiteSafeExportDocument:
    """Allowlisted projection — never serialize the internal EIR directly."""

    _assert_scope_compatible(report.report_scope, policy.export_scope)
    aliases = _build_repository_aliases(report, policy=policy)
    classification = _classification_label(policy.export_scope)

    tech_rows = _project_technology(report, policy=policy)
    capability_rows = _project_capability(report, aliases=aliases, policy=policy)
    head_rows = _project_head_distributions(report, policy=policy)
    patterns = _project_patterns(report, aliases=aliases, policy=policy)
    observations = _project_observations(report, aliases=aliases, policy=policy)
    confidence = _project_confidence(report)
    limitations = _project_limitations(report, aliases=aliases, policy=policy)
    drilldowns = _project_drilldowns(report, aliases=aliases, policy=policy)

    empty_notes: list[str] = []
    if not patterns:
        empty_notes.append(
            "No recurring patterns met the configured multi-repository threshold."
        )
    if not observations:
        empty_notes.append(
            "No modernization observations met the deterministic support policy."
        )

    export_id = build_export_id(
        source_report_id=report.report_id.value,
        interpretation_policy_bundle_id=report.interpretation_policy_bundle_id,
        export_policy_token=policy.policy_token,
        export_schema_version=policy.export_schema_version,
        artifact_template_version=policy.artifact_template_version,
    )

    methodology = None
    if policy.include_methodology:
        schema_versions = tuple(
            sorted(
                {
                    item.assessment_schema_version
                    for item in report.dataset.repository_assessments
                    if item.repository_id in report.dataset.included_repository_ids
                }
            )
        )
        methodology = SafeMethodologyBlock(
            assessment_schema_versions=schema_versions or ("1.2",),
            interpretation_policy_bundle_id=report.interpretation_policy_bundle_id,
            export_policy_id=policy.policy_token,
            aggregation_policy_id=report.methodology.aggregation_policy_id or "aggregation:v1",
            notes=tuple(report.methodology.notes)
            + (
                "Static analysis of selected assessed repositories only.",
                "This report is a cross-sectional snapshot, not a temporal trend.",
                "Results must not be generalized beyond the selected dataset.",
            ),
            limitations=(
                "website_export_is_sanitized_projection",
                "canonical_assessment_reports_remain_source_of_truth",
            ),
        )

    population = tuple(
        sorted(
            (alias, _source_type_for_alias(report, alias, aliases))
            for alias in aliases.values()
        )
    )

    orientation = (
        f"Repository count: {len(aliases)}",
        f"Report confidence: {report.confidence.level.value}",
        f"Recurring patterns: {len(patterns)}",
        f"Modernization observations: {len(observations)}",
        f"Classification: {classification}",
    )

    metadata = SafeExportMetadata(
        export_id=export_id,
        export_schema_version=policy.export_schema_version,
        source_report_id=report.report_id.value,
        source_eir_schema_version=report.schema_version,
        interpretation_policy_bundle_id=report.interpretation_policy_bundle_id,
        export_policy_id=policy.policy_token,
        classification=classification,
        html_template_version=policy.html_template_version,
        json_projection_version=policy.json_projection_version,
        generated_at=generated_at,
    )

    document = WebsiteSafeExportDocument(
        report_id=report.report_id.value,
        export_schema_version=policy.export_schema_version,
        report_schema_version=report.schema_version,
        title=_safe_text(report.title, label="title"),
        scope=policy.export_scope.value,
        classification=classification,
        dataset_summary={
            "repository_count": len(aliases),
            "pattern_count": len(patterns),
            "observation_count": len(observations),
            "limitation_count": len(limitations),
            "drilldown_count": len(drilldowns),
            "report_scope": report.report_scope.value,
        },
        methodology=methodology,
        repository_population=population,
        technology_distribution=tech_rows,
        capability_comparisons=capability_rows,
        assessment_head_distributions=head_rows,
        recurring_patterns=patterns,
        modernization_observations=observations,
        confidence=confidence,
        limitations=limitations,
        repository_drilldowns=drilldowns,
        export_metadata=metadata,
        orientation=orientation,
        empty_section_notes=tuple(empty_notes),
        export_limitations=tuple(policy.limitations)
        + (
            "website_safe_export_is_sanitized_projection",
            "public_exports_are_not_industry_benchmarks",
        ),
    )
    _assert_no_private_identity_leak(document, report, aliases=aliases, policy=policy)
    return document


def export_document_to_stable_dict(document: WebsiteSafeExportDocument) -> dict[str, object]:
    from codestrata_platform.intelligence_reporting.domain.serialization import (
        to_stable_dict,
    )

    return to_stable_dict(document)


def _assert_scope_compatible(report_scope: ReportScope, export_scope: ExportScope) -> None:
    expected = {
        ReportScope.PUBLIC_OSS_DATASET: {ExportScope.PUBLIC_OSS, ExportScope.ANONYMIZED_EXTERNAL},
        ReportScope.CUSTOMER_PORTFOLIO: {
            ExportScope.CUSTOMER_PRIVATE,
            ExportScope.ANONYMIZED_EXTERNAL,
        },
        ReportScope.CUSTOMER_WORKSPACE: {
            ExportScope.CUSTOMER_PRIVATE,
            ExportScope.ANONYMIZED_EXTERNAL,
        },
        ReportScope.INTERNAL_VALIDATION_DATASET: {
            ExportScope.INTERNAL,
            ExportScope.ANONYMIZED_EXTERNAL,
        },
        ReportScope.DESIGN_PARTNER_DATASET: {
            ExportScope.CUSTOMER_PRIVATE,
            ExportScope.ANONYMIZED_EXTERNAL,
        },
        ReportScope.OTHER: {ExportScope.ANONYMIZED_EXTERNAL, ExportScope.INTERNAL},
    }
    allowed = expected.get(report_scope, {ExportScope.ANONYMIZED_EXTERNAL})
    if export_scope not in allowed:
        raise InvalidValueError(
            f"export scope {export_scope.value} incompatible with report scope {report_scope.value}",
            reason_code="export_scope_mismatch",
        )


def _classification_label(scope: ExportScope) -> str:
    return {
        ExportScope.PUBLIC_OSS: "Public OSS report",
        ExportScope.CUSTOMER_PRIVATE: "Customer-private report — not for public distribution",
        ExportScope.INTERNAL: "Internal report — not for public distribution",
        ExportScope.ANONYMIZED_EXTERNAL: "Anonymized external report",
    }[scope]


def _build_repository_aliases(
    report: EngineeringIntelligenceReport,
    *,
    policy: WebsiteExportBuildPolicy,
) -> dict[str, str]:
    included = list(report.dataset.included_repository_ids)
    refs = {
        item.repository_id: item
        for item in report.dataset.repository_assessments
        if item.repository_id in included
    }
    aliases: dict[str, str] = {}
    for index, repository_id in enumerate(sorted(included), start=1):
        ref = refs[repository_id]
        if policy.repository_identity_policy is RepositoryIdentityPolicy.ANONYMIZE_ALWAYS:
            aliases[repository_id] = _stable_alias(repository_id)
            continue
        if policy.export_scope is ExportScope.PUBLIC_OSS:
            if ref.visibility is not DataVisibility.PUBLIC:
                continue  # omit non-public from public export population
            if not ref.source_reference_publication_permitted:
                aliases[repository_id] = _stable_alias(repository_id)
            elif (
                policy.repository_identity_policy
                is RepositoryIdentityPolicy.PUBLIC_WHEN_PERMITTED
                and (ref.display_name or "").strip()
            ):
                aliases[repository_id] = _safe_text(
                    ref.display_name or repository_id, label="display_name"
                )
            else:
                aliases[repository_id] = _stable_alias(repository_id)
            continue
        if (
            policy.repository_identity_policy
            is RepositoryIdentityPolicy.PRIVATE_DISPLAY_ALLOWED
        ):
            aliases[repository_id] = _safe_text(
                (ref.display_name or "").strip() or _stable_alias(repository_id),
                label="display_name",
            )
        else:
            aliases[repository_id] = _stable_alias(repository_id)
    if not aliases and included:
        # Fall back to aliases for all when public filter emptied unexpectedly.
        for repository_id in sorted(included):
            aliases[repository_id] = _stable_alias(repository_id)
    return aliases


def _stable_alias(repository_id: str) -> str:
    digest = hashlib.sha256(repository_id.encode("utf-8")).hexdigest()[:8]
    return f"repository-{digest}"


def _source_type_for_alias(
    report: EngineeringIntelligenceReport,
    alias: str,
    aliases: Mapping[str, str],
) -> str:
    reverse = {value: key for key, value in aliases.items()}
    repository_id = reverse.get(alias)
    if repository_id is None:
        return "unknown"
    for item in report.dataset.repository_assessments:
        if item.repository_id == repository_id:
            return item.source_type.value
    return "unknown"


def _project_technology(
    report: EngineeringIntelligenceReport,
    *,
    policy: WebsiteExportBuildPolicy,
) -> tuple[SafeTechnologyRow, ...]:
    rows: list[SafeTechnologyRow] = []
    denom = report.technology_distribution.repository_denominator
    for obs in report.technology_distribution.observations:
        states = tuple(sorted({version.state.value for version in obs.versions}))
        rows.append(
            SafeTechnologyRow(
                category=_safe_text(obs.category, label="category"),
                technology=_safe_text(obs.normalized_name, label="technology"),
                repository_count=obs.repository_count,
                denominator=denom,
                ratio=obs.repository_ratio.value or "unavailable",
                version_states=states,
                limitations=tuple(obs.limitations),
            )
        )
    return tuple(rows)


def _project_capability(
    report: EngineeringIntelligenceReport,
    *,
    aliases: Mapping[str, str],
    policy: WebsiteExportBuildPolicy,
) -> tuple[SafeCapabilityRow, ...]:
    rows: list[SafeCapabilityRow] = []
    for comparison in report.capability_comparisons:
        for snap in comparison.repositories:
            alias = aliases.get(snap.repository_id)
            if alias is None:
                continue
            rows.append(
                SafeCapabilityRow(
                    assessment_head_id=snap.assessment_head_id,
                    repository_alias=alias,
                    activation_status=snap.activation_status.value,
                    coverage_status=snap.coverage_status.value,
                    confidence_level=snap.confidence_level.value,
                    finding_count=snap.finding_count,
                    recommendation_count=snap.recommendation_count,
                    priority_action_count=snap.priority_action_count,
                    highest_severity=snap.highest_severity,
                )
            )
            if len(rows) >= policy.maximum_capability_rows:
                return tuple(rows)
    return tuple(rows)


def _project_head_distributions(
    report: EngineeringIntelligenceReport,
    *,
    policy: WebsiteExportBuildPolicy,
) -> tuple[SafeHeadDistributionRow, ...]:
    rows: list[SafeHeadDistributionRow] = []
    for head in report.assessment_head_distributions:
        rows.append(
            SafeHeadDistributionRow(
                assessment_head_id=head.assessment_head_id,
                repository_count=head.repository_count,
                activated_count=head.activated_count,
                complete_coverage_count=head.complete_coverage_count,
                partial_coverage_count=head.partial_coverage_count,
                insufficient_evidence_count=head.insufficient_evidence_count,
                unavailable_count=head.unavailable_count,
                disabled_count=head.disabled_count,
                finding_count=head.finding_count,
                recommendation_count=head.recommendation_count,
                priority_action_count=head.priority_action_count,
                severity_distribution=tuple(head.severity_distribution),
                confidence_distribution=tuple(head.confidence_distribution),
            )
        )
    return tuple(rows)


def _project_patterns(
    report: EngineeringIntelligenceReport,
    *,
    aliases: Mapping[str, str],
    policy: WebsiteExportBuildPolicy,
) -> tuple[SafePatternItem, ...]:
    items: list[SafePatternItem] = []
    for pattern in report.recurring_patterns[: policy.maximum_pattern_items]:
        member_aliases = tuple(
            sorted(
                aliases[repo_id]
                for repo_id in pattern.repository_ids
                if repo_id in aliases
            )
        )
        denom = (
            pattern.repository_ratio.denominator
            if pattern.repository_ratio is not None
            else pattern.repository_count
        )
        items.append(
            SafePatternItem(
                pattern_id=pattern.pattern_id.value,
                title=_safe_text(pattern.title, label="pattern_title"),
                statement=_safe_text(pattern.statement, label="pattern_statement"),
                assessment_head_ids=tuple(pattern.assessment_head_ids),
                repository_count=pattern.repository_count,
                denominator=denom,
                confidence=pattern.confidence.value,
                repository_aliases=member_aliases,
                limitations=tuple(pattern.limitations),
            )
        )
    return tuple(items)


def _project_observations(
    report: EngineeringIntelligenceReport,
    *,
    aliases: Mapping[str, str],
    policy: WebsiteExportBuildPolicy,
) -> tuple[SafeObservationItem, ...]:
    items: list[SafeObservationItem] = []
    for observation in report.modernization_observations[
        : policy.maximum_observation_items
    ]:
        member_aliases = tuple(
            sorted(
                aliases[repo_id]
                for repo_id in observation.repository_ids
                if repo_id in aliases
            )
        )
        items.append(
            SafeObservationItem(
                observation_id=observation.observation_id.value,
                title=_safe_text(observation.title, label="observation_title"),
                statement=_safe_text(observation.statement, label="observation_statement"),
                category=observation.category.value,
                repository_count=observation.repository_count,
                denominator=len(report.dataset.included_repository_ids),
                confidence=observation.confidence.value,
                repository_aliases=member_aliases,
                limitations=tuple(observation.limitations),
            )
        )
    return tuple(items)


def _project_confidence(report: EngineeringIntelligenceReport) -> SafeConfidenceBlock:
    conf = report.confidence
    return SafeConfidenceBlock(
        level=conf.level.value,
        basis=tuple(conf.basis),
        repository_sample_count=conf.repository_sample_count,
        comparable_repository_count=conf.comparable_repository_count,
        dataset_coverage_status=conf.dataset_coverage_status.value,
        weakest_material_source_confidence=conf.weakest_material_source_confidence.value,
        limitations=tuple(conf.limitations),
    )


def _project_limitations(
    report: EngineeringIntelligenceReport,
    *,
    aliases: Mapping[str, str],
    policy: WebsiteExportBuildPolicy,
) -> tuple[SafeLimitationItem, ...]:
    if not policy.include_limitations:
        return ()
    items: list[SafeLimitationItem] = []
    for limitation in report.limitations:
        if not limitation.customer_visible and policy.export_scope is ExportScope.PUBLIC_OSS:
            continue
        scope_aliases = tuple(
            sorted(
                aliases[repo_id]
                for repo_id in limitation.affected_repository_ids
                if repo_id in aliases
            )
        )
        items.append(
            SafeLimitationItem(
                category=limitation.category.value,
                interpretation_severity=limitation.severity.value,
                statement=_safe_text(limitation.statement, label="limitation_statement"),
                affected_scope=scope_aliases,
                remediation_or_interpretation=(
                    _safe_text(
                        limitation.remediation_or_interpretation,
                        label="limitation_remediation",
                    )
                    if limitation.remediation_or_interpretation
                    else None
                ),
            )
        )
    return tuple(items)


def _project_drilldowns(
    report: EngineeringIntelligenceReport,
    *,
    aliases: Mapping[str, str],
    policy: WebsiteExportBuildPolicy,
) -> tuple[SafeDrilldownSection, ...]:
    sections: list[SafeDrilldownSection] = []
    for drilldown in report.repository_drilldowns:
        if drilldown.repository_id not in aliases:
            continue
        if (
            policy.export_scope is ExportScope.PUBLIC_OSS
            and not drilldown.public_export_eligible
            and drilldown.visibility is not DataVisibility.PUBLIC
        ):
            continue
        alias = aliases[drilldown.repository_id]
        finding_refs = tuple(
            SafeEntityItem(
                entity_kind=_safe_text(ref.entity_kind, label="entity_kind"),
                entity_id=_safe_text(ref.entity_id, label="entity_id"),
                label=(
                    _safe_text(ref.label, label="entity_label") if ref.label else None
                ),
            )
            for ref in drilldown.finding_refs[
                : policy.maximum_finding_refs_per_drilldown
            ]
        )
        recommendation_refs = tuple(
            SafeEntityItem(
                entity_kind=_safe_text(ref.entity_kind, label="entity_kind"),
                entity_id=_safe_text(ref.entity_id, label="entity_id"),
                label=(
                    _safe_text(ref.label, label="entity_label") if ref.label else None
                ),
            )
            for ref in drilldown.recommendation_refs[
                : policy.maximum_recommendation_refs_per_drilldown
            ]
        )
        head_rows = tuple(
            SafeCapabilityRow(
                assessment_head_id=snap.assessment_head_id,
                repository_alias=alias,
                activation_status=snap.activation_status.value,
                coverage_status=snap.coverage_status.value,
                confidence_level=snap.confidence_level.value,
                finding_count=snap.finding_count,
                recommendation_count=snap.recommendation_count,
                priority_action_count=snap.priority_action_count,
                highest_severity=snap.highest_severity,
            )
            for snap in drilldown.assessment_head_snapshots
        )
        truncation = None
        notes = " ".join(drilldown.limitations)
        if "truncated" in notes:
            truncation = (
                "Drill-down includes a bounded navigation subset of entities; "
                "use the canonical assessment report for the complete result."
            )
        sections.append(
            SafeDrilldownSection(
                drilldown_id=drilldown.drilldown_id.value,
                repository_alias=alias,
                source_type=drilldown.source_type.value,
                technology_summary=tuple(
                    _safe_text(item, label="technology_summary")
                    for item in drilldown.technology_summary
                ),
                head_snapshots=head_rows,
                recurring_pattern_ids=tuple(drilldown.recurring_pattern_ids),
                modernization_observation_ids=tuple(
                    drilldown.modernization_observation_ids
                ),
                finding_refs=finding_refs,
                recommendation_refs=recommendation_refs,
                priority_action_ids=tuple(drilldown.highest_priority_action_ids),
                roadmap_ids=tuple(ref.entity_id for ref in drilldown.roadmap_refs),
                confidence=drilldown.confidence.value,
                limitations=tuple(drilldown.limitations),
                canonical_assessment_availability=(
                    "Detailed assessment available to authorized users."
                ),
                truncation_note=truncation,
            )
        )
        if len(sections) >= policy.maximum_repository_drilldowns:
            break
    return tuple(sections)


def _assert_no_private_identity_leak(
    document: WebsiteSafeExportDocument,
    report: EngineeringIntelligenceReport,
    *,
    aliases: Mapping[str, str],
    policy: WebsiteExportBuildPolicy,
) -> None:
    if policy.export_scope not in {
        ExportScope.PUBLIC_OSS,
        ExportScope.ANONYMIZED_EXTERNAL,
    }:
        return
    blob = json.dumps(export_document_to_stable_dict(document), ensure_ascii=True)
    for repository_id in report.dataset.included_repository_ids:
        if repository_id in aliases.values():
            continue
        if repository_id in blob and aliases.get(repository_id) != repository_id:
            raise InvalidValueError(
                f"private/original repository identity leaked into export: {repository_id}",
                reason_code="export_identity_leak",
            )
        ref = next(
            (
                item
                for item in report.dataset.repository_assessments
                if item.repository_id == repository_id
            ),
            None,
        )
        if ref and ref.display_name and ref.display_name != aliases.get(repository_id):
            if ref.display_name in blob and policy.repository_identity_policy is (
                RepositoryIdentityPolicy.ANONYMIZE_ALWAYS
            ):
                raise InvalidValueError(
                    "original display name leaked into anonymized export",
                    reason_code="export_display_name_leak",
                )


def _safe_text(value: str, *, label: str) -> str:
    return reject_unsafe_text(str(value).strip(), label=label)
