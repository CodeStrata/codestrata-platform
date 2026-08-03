"""Fail-closed validation for repository drill-downs."""

from __future__ import annotations

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    CrossRepositoryAggregation,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns.diagnostics import (
    RepositoryDrilldownDiagnostics,
)
from codestrata_platform.intelligence_reporting.domain.drilldown import (
    RepositoryIntelligenceDrilldown,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    DataVisibility,
    ReportScope,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)

_FORBIDDEN = (
    "maturity score",
    "health score",
    "readiness score",
    "healthy repository",
    "no risk",
    "no modernization needed",
    "repository ranking",
    "precision/recall",
    "false positive",
)


def validate_repository_drilldowns(
    report: EngineeringIntelligenceReport,
    aggregation: CrossRepositoryAggregation,
    *,
    diagnostics: RepositoryDrilldownDiagnostics,
) -> None:
    included = list(report.dataset.included_repository_ids)
    drilldowns = report.repository_drilldowns
    if len(drilldowns) != diagnostics.drilldown_count:
        raise InvalidValueError(
            "diagnostics drilldown_count mismatch",
            reason_code="drilldown_diagnostics_mismatch",
        )
    if diagnostics.unresolved_reference_count != 0:
        raise InvalidValueError(
            "unresolved drilldown references present",
            reason_code="unresolved_drilldown_refs",
        )

    seen_repos: set[str] = set()
    finding_ids = {
        (item.repository_id, item.assessment_id, item.finding_id)
        for item in aggregation.finding_facts
    }
    rec_ids = {
        (item.repository_id, item.assessment_id, item.recommendation_id)
        for item in aggregation.recommendation_facts
    }
    pa_ids = {
        (item.repository_id, item.assessment_id, item.priority_action_id)
        for item in aggregation.priority_action_facts
    }
    roadmap_ids = {
        (item.repository_id, item.assessment_id, item.initiative_id)
        for item in aggregation.roadmap_facts
    }
    corr_ids = {
        (item.repository_id, item.assessment_id, item.correlation_id)
        for item in aggregation.correlation_facts
    }
    pattern_ids = {item.pattern_id.value for item in report.recurring_patterns}
    observation_ids = {item.observation_id.value for item in report.modernization_observations}
    pattern_members = {
        item.pattern_id.value: set(item.repository_ids) for item in report.recurring_patterns
    }
    observation_members = {
        item.observation_id.value: set(item.repository_ids)
        for item in report.modernization_observations
    }

    for drilldown in drilldowns:
        _validate_one(
            drilldown,
            report=report,
            included=included,
            seen_repos=seen_repos,
            finding_ids=finding_ids,
            rec_ids=rec_ids,
            pa_ids=pa_ids,
            roadmap_ids=roadmap_ids,
            corr_ids=corr_ids,
            pattern_ids=pattern_ids,
            observation_ids=observation_ids,
            pattern_members=pattern_members,
            observation_members=observation_members,
        )

    # Excluded repositories must not appear.
    excluded = {
        item.repository_id
        for item in report.dataset.repository_assessments
        if item.repository_id not in included
    }
    leaked = seen_repos & excluded
    if leaked:
        raise InvalidValueError(
            f"drilldown exists for excluded repository: {sorted(leaked)}",
            reason_code="excluded_repository_has_drilldown",
        )


def _validate_one(
    drilldown: RepositoryIntelligenceDrilldown,
    *,
    report: EngineeringIntelligenceReport,
    included: list[str],
    seen_repos: set[str],
    finding_ids: set[tuple[str, str, str]],
    rec_ids: set[tuple[str, str, str]],
    pa_ids: set[tuple[str, str, str]],
    roadmap_ids: set[tuple[str, str, str]],
    corr_ids: set[tuple[str, str, str]],
    pattern_ids: set[str],
    observation_ids: set[str],
    pattern_members: dict[str, set[str]],
    observation_members: dict[str, set[str]],
) -> None:
    if drilldown.repository_id not in included:
        raise InvalidValueError(
            "drilldown repository not included in dataset",
            reason_code="drilldown_repo_not_in_dataset",
        )
    if drilldown.repository_id in seen_repos:
        raise InvalidValueError(
            "duplicate repository drilldown",
            reason_code="duplicate_drilldown",
        )
    seen_repos.add(drilldown.repository_id)
    if not drilldown.canonical_assessment_report_ref:
        raise InvalidValueError(
            "canonical assessment report reference is required",
            reason_code="missing_canonical_report_ref",
        )
    ref_lower = drilldown.canonical_assessment_report_ref.lower()
    if ref_lower.startswith("file:") or "/users/" in ref_lower or "/tmp/" in ref_lower:
        raise InvalidValueError(
            "canonical report reference must not expose filesystem paths",
            reason_code="unsafe_canonical_report_ref",
        )
    if drilldown.confidence not in set(ConfidenceLevel):
        raise InvalidValueError(
            "invalid drilldown confidence",
            reason_code="invalid_drilldown_confidence",
        )

    for entity_id in drilldown.recurring_pattern_ids:
        if entity_id not in pattern_ids:
            raise InvalidValueError(
                f"unknown pattern id in drilldown: {entity_id}",
                reason_code="unresolved_pattern_ref",
            )
        if drilldown.repository_id not in pattern_members.get(entity_id, set()):
            raise InvalidValueError(
                f"pattern membership invalid for repository: {entity_id}",
                reason_code="pattern_membership_invalid",
            )
    for entity_id in drilldown.modernization_observation_ids:
        if entity_id not in observation_ids:
            raise InvalidValueError(
                f"unknown observation id in drilldown: {entity_id}",
                reason_code="unresolved_observation_ref",
            )
        if drilldown.repository_id not in observation_members.get(entity_id, set()):
            raise InvalidValueError(
                f"observation membership invalid for repository: {entity_id}",
                reason_code="observation_membership_invalid",
            )

    _validate_refs(
        drilldown.finding_refs,
        allowed=finding_ids,
        repository_id=drilldown.repository_id,
        assessment_id=drilldown.assessment_id,
        kind="finding",
    )
    _validate_refs(
        drilldown.recommendation_refs,
        allowed=rec_ids,
        repository_id=drilldown.repository_id,
        assessment_id=drilldown.assessment_id,
        kind="recommendation",
    )
    _validate_refs(
        drilldown.priority_action_refs,
        allowed=pa_ids,
        repository_id=drilldown.repository_id,
        assessment_id=drilldown.assessment_id,
        kind="priority_action",
    )
    _validate_refs(
        drilldown.roadmap_refs,
        allowed=roadmap_ids,
        repository_id=drilldown.repository_id,
        assessment_id=drilldown.assessment_id,
        kind="roadmap_initiative",
    )
    _validate_refs(
        drilldown.correlation_refs,
        allowed=corr_ids,
        repository_id=drilldown.repository_id,
        assessment_id=drilldown.assessment_id,
        kind="correlation",
    )

    for text in drilldown.limitations:
        lowered = text.lower()
        for token in _FORBIDDEN:
            if token in lowered:
                raise InvalidValueError(
                    f"drilldown limitation contains prohibited language: {token}",
                    reason_code="forbidden_drilldown_language",
                )

    if report.report_scope is ReportScope.PUBLIC_OSS_DATASET:
        if drilldown.visibility in {
            DataVisibility.CUSTOMER_PRIVATE,
            DataVisibility.INTERNAL,
        }:
            if drilldown.display_name == drilldown.repository_id:
                raise InvalidValueError(
                    "public-scope drilldown must not expose private repository identity",
                    reason_code="public_scope_private_identity_leak",
                )
            if not drilldown.display_name.startswith("repository-"):
                raise InvalidValueError(
                    "public-scope private repository requires anonymized display name",
                    reason_code="public_scope_private_display_leak",
                )


def _validate_refs(
    refs,
    *,
    allowed: set[tuple[str, str, str]],
    repository_id: str,
    assessment_id: str,
    kind: str,
) -> None:
    seen: set[str] = set()
    for ref in refs:
        if ref.entity_id in seen:
            raise InvalidValueError(
                f"duplicate {kind} ref: {ref.entity_id}",
                reason_code="duplicate_entity_ref",
            )
        seen.add(ref.entity_id)
        if ref.assessment_id != assessment_id:
            raise InvalidValueError(
                f"{kind} ref assessment mismatch",
                reason_code="cross_assessment_entity_ref",
            )
        key = (repository_id, assessment_id, ref.entity_id)
        if key not in allowed:
            raise InvalidValueError(
                f"unresolved {kind} ref: {ref.entity_id}",
                reason_code="unresolved_entity_ref",
            )
