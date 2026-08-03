"""Validate TechnologyDistribution invariants."""

from __future__ import annotations

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.domain.enums import DataVisibility
from codestrata_platform.intelligence_reporting.domain.technology import TechnologyDistribution


def validate_distribution(
    distribution: TechnologyDistribution,
    *,
    dataset_repository_ids: set[str],
    visibility_policy: VisibilityAggregationScope,
    repository_visibility: dict[str, DataVisibility],
) -> None:
    seen_ids: set[str] = set()
    for observation in distribution.observations:
        if observation.technology_id in seen_ids:
            raise InvalidValueError(
                "duplicate technology observation identity",
                reason_code="duplicate_technology_identity",
            )
        seen_ids.add(observation.technology_id)
        for repo_id in observation.repository_ids:
            if repo_id not in dataset_repository_ids:
                raise InvalidValueError(
                    f"observation repository not in dataset: {repo_id}",
                    reason_code="tech_repo_not_in_dataset",
                )
            visibility = repository_visibility.get(repo_id)
            if (
                visibility_policy is VisibilityAggregationScope.PUBLIC_OSS
                and visibility is not None
                and visibility is not DataVisibility.PUBLIC
            ):
                raise InvalidValueError(
                    f"private repository ID leaked into public technology distribution: {repo_id}",
                    reason_code="private_ref_leak",
                )
        if observation.repository_count != len(set(observation.repository_ids)):
            raise InvalidValueError(
                "repository_count must equal unique repository IDs",
                reason_code="tech_repo_count_mismatch",
            )
        if observation.occurrence_count < observation.repository_count:
            raise InvalidValueError(
                "occurrence_count cannot be less than repository_count",
                reason_code="tech_occurrence_lt_presence",
            )
        if observation.repository_ratio.numerator != observation.repository_count:
            raise InvalidValueError(
                "ratio numerator must equal repository_count",
                reason_code="tech_ratio_numerator_mismatch",
            )
        if observation.repository_ratio.denominator != distribution.repository_denominator:
            raise InvalidValueError(
                "ratio denominator must equal technology denominator",
                reason_code="tech_ratio_denominator_mismatch",
            )
        for version in observation.versions:
            if version.state.value == "known" and not version.version:
                raise InvalidValueError(
                    "known version state requires explicit version string",
                    reason_code="known_version_missing_value",
                )
            if version.state.value == "unavailable" and version.version:
                raise InvalidValueError(
                    "unavailable version must not carry an exact version string",
                    reason_code="unavailable_version_has_value",
                )
