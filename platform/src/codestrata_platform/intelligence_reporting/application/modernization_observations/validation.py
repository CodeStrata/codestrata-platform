"""Validate modernization observation outputs."""

from __future__ import annotations

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.domain.enums import DataVisibility
from codestrata_platform.intelligence_reporting.domain.modernization import (
    ModernizationObservation,
)


def validate_observations(
    observations: tuple[ModernizationObservation, ...],
    *,
    dataset_repository_ids: set[str],
    recommendation_ids: set[str],
    priority_action_ids: set[str],
    roadmap_ids: set[str],
    finding_ids: set[str],
    visibility_policy: VisibilityAggregationScope,
    repository_visibility: dict[str, DataVisibility],
) -> None:
    seen: set[str] = set()
    for observation in observations:
        if observation.observation_id.value in seen:
            raise InvalidValueError(
                "duplicate observation identity",
                reason_code="duplicate_observation_identity",
            )
        seen.add(observation.observation_id.value)
        if observation.repository_count < 2:
            raise InvalidValueError(
                "observation requires at least two repositories",
                reason_code="observation_requires_multiple_repositories",
            )
        if observation.repository_count != len(observation.repository_ids):
            raise InvalidValueError(
                "repository_count mismatch",
                reason_code="observation_repository_count_mismatch",
            )
        if not observation.recommendation_ids and not observation.priority_action_ids:
            raise InvalidValueError(
                "observation missing deterministic support",
                reason_code="observation_missing_deterministic_support",
            )
        if ":" not in observation.normalized_subject:
            raise InvalidValueError(
                "observation identity must not be title-only",
                reason_code="title_only_observation_identity",
            )
        for repo_id in observation.repository_ids:
            if repo_id not in dataset_repository_ids:
                raise InvalidValueError(
                    f"observation repository not in dataset: {repo_id}",
                    reason_code="observation_repo_not_in_dataset",
                )
            visibility = repository_visibility.get(repo_id)
            if (
                visibility_policy is VisibilityAggregationScope.PUBLIC_OSS
                and visibility is not None
                and visibility is not DataVisibility.PUBLIC
            ):
                raise InvalidValueError(
                    f"private repository ID leaked into public modernization observation: "
                    f"{repo_id}",
                    reason_code="private_ref_leak",
                )
        for rid in observation.recommendation_ids:
            if rid not in recommendation_ids:
                raise InvalidValueError(
                    f"unresolved recommendation ID: {rid}",
                    reason_code="unresolved_recommendation_ref",
                )
        for aid in observation.priority_action_ids:
            if aid not in priority_action_ids:
                raise InvalidValueError(
                    f"unresolved priority action ID: {aid}",
                    reason_code="unresolved_priority_action_ref",
                )
        for iid in observation.roadmap_initiative_ids:
            if iid not in roadmap_ids:
                raise InvalidValueError(
                    f"unresolved roadmap initiative ID: {iid}",
                    reason_code="unresolved_roadmap_ref",
                )
        for fid in observation.supporting_finding_ids:
            if fid not in finding_ids:
                raise InvalidValueError(
                    f"unresolved finding ID: {fid}",
                    reason_code="unresolved_finding_ref",
                )
        _reject_unsafe_statement(f"{observation.title} {observation.statement}")
        for forbidden_attr in (
            "portfolio_recommendation",
            "roi",
            "cost_estimate",
            "staffing",
            "timeline",
            "priority_score",
            "urgency_score",
        ):
            if hasattr(observation, forbidden_attr):
                raise InvalidValueError(
                    f"forbidden portfolio-action field: {forbidden_attr}",
                    reason_code="forbidden_portfolio_action_field",
                )


def _reject_unsafe_statement(blob: str) -> None:
    lowered = blob.lower()
    for token in (
        "portfolio should",
        "must standardize",
        "urgent transformation",
        "industry",
        "roi",
        "staffing",
        "delivery commitment",
        "improving",
        "declining",
    ):
        if token in lowered:
            raise InvalidValueError(
                f"unsafe observation statement wording: {token}",
                reason_code="unsafe_observation_statement",
            )
