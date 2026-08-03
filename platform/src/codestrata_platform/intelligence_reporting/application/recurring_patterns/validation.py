"""Validate recurring pattern outputs."""

from __future__ import annotations

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.domain.enums import DataVisibility
from codestrata_platform.intelligence_reporting.domain.patterns import (
    RecurringIntelligencePattern,
)


def validate_patterns(
    patterns: tuple[RecurringIntelligencePattern, ...],
    *,
    dataset_repository_ids: set[str],
    assessment_ids_by_repo: dict[str, set[str]],
    finding_ids_by_assessment: dict[str, set[str]],
    recommendation_ids_by_assessment: dict[str, set[str]],
    visibility_policy: VisibilityAggregationScope,
    repository_visibility: dict[str, DataVisibility],
) -> None:
    seen: set[str] = set()
    for pattern in patterns:
        if pattern.pattern_id.value in seen:
            raise InvalidValueError(
                "duplicate pattern identity",
                reason_code="duplicate_pattern_identity",
            )
        seen.add(pattern.pattern_id.value)
        if pattern.repository_count < 2 and not pattern.allow_single_repository:
            raise InvalidValueError(
                "pattern requires at least two repositories",
                reason_code="pattern_requires_multiple_repositories",
            )
        if len(pattern.repository_ids) != len(set(pattern.repository_ids)):
            raise InvalidValueError(
                "duplicate repository IDs in pattern",
                reason_code="duplicate_pattern_repository_ids",
            )
        if pattern.repository_count != len(pattern.repository_ids):
            raise InvalidValueError(
                "repository_count mismatch",
                reason_code="pattern_repository_count_mismatch",
            )
        if pattern.repository_ratio is not None:
            if pattern.repository_ratio.numerator != pattern.repository_count:
                raise InvalidValueError(
                    "pattern ratio numerator must equal repository_count",
                    reason_code="pattern_ratio_numerator_mismatch",
                )
        for repo_id in pattern.repository_ids:
            if repo_id not in dataset_repository_ids:
                raise InvalidValueError(
                    f"pattern repository not in dataset: {repo_id}",
                    reason_code="pattern_repo_not_in_dataset",
                )
            visibility = repository_visibility.get(repo_id)
            if (
                visibility_policy is VisibilityAggregationScope.PUBLIC_OSS
                and visibility is not None
                and visibility is not DataVisibility.PUBLIC
            ):
                raise InvalidValueError(
                    f"private repository ID leaked into public recurring pattern: {repo_id}",
                    reason_code="private_ref_leak",
                )
        for assessment_id in pattern.assessment_ids:
            if not any(assessment_id in ids for ids in assessment_ids_by_repo.values()):
                raise InvalidValueError(
                    f"unresolved assessment ID in pattern: {assessment_id}",
                    reason_code="unresolved_assessment_ref",
                )
        # Finding / recommendation membership: IDs must exist in some assessment.
        known_findings = set().union(*finding_ids_by_assessment.values()) if finding_ids_by_assessment else set()
        known_recs = (
            set().union(*recommendation_ids_by_assessment.values())
            if recommendation_ids_by_assessment
            else set()
        )
        for finding_id in pattern.finding_ids:
            if finding_id not in known_findings:
                raise InvalidValueError(
                    f"unresolved finding ID in pattern: {finding_id}",
                    reason_code="unresolved_finding_ref",
                )
        for rec_id in pattern.recommendation_ids:
            if rec_id not in known_recs:
                raise InvalidValueError(
                    f"unresolved recommendation ID in pattern: {rec_id}",
                    reason_code="unresolved_recommendation_ref",
                )
        _reject_unsafe_statement(pattern.statement)
        if not pattern.normalized_subject.strip():
            raise InvalidValueError(
                "pattern normalized_subject required",
                reason_code="missing_pattern_subject",
            )
        # Title must not be the sole identity — subject/rules must carry structure.
        if (
            not pattern.rule_ids
            and pattern.pattern_type.value.startswith("recurring_")
            and ":" not in pattern.normalized_subject
        ):
            raise InvalidValueError(
                "pattern identity must not be title-only",
                reason_code="title_only_pattern_identity",
            )


def _reject_unsafe_statement(statement: str) -> None:
    lowered = statement.lower()
    for token in (
        "systemic",
        "widespread",
        "industry prevalence",
        "maturity score",
        "should standardize",
        "portfolio recommendation",
        "improving",
        "declining",
    ):
        if token in lowered:
            raise InvalidValueError(
                f"unsafe pattern statement wording: {token}",
                reason_code="unsafe_pattern_statement",
            )
