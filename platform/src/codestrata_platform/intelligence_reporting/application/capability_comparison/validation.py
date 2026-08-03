"""Validate capability comparison invariants."""

from __future__ import annotations

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.domain.capability import (
    AssessmentHeadDistribution,
    CapabilityComparison,
)
from codestrata_platform.intelligence_reporting.domain.enums import DataVisibility


_FORBIDDEN_FIELDS = (
    "maturity_score",
    "readiness_score",
    "health_score",
    "composite_score",
    "percentile",
    "league_table",
    "ranking",
    "best",
    "worst",
    "time_points",
    "trend",
    "improving",
    "declining",
)


def validate_capability_outputs(
    *,
    comparisons: tuple[CapabilityComparison, ...],
    head_distributions: tuple[AssessmentHeadDistribution, ...],
    dataset_repository_ids: set[str],
    visibility_policy: VisibilityAggregationScope,
    repository_visibility: dict[str, DataVisibility],
) -> None:
    seen_heads: set[str] = set()
    for comparison in comparisons:
        if comparison.assessment_head_id in seen_heads:
            raise InvalidValueError(
                "duplicate CapabilityComparison for assessment head",
                reason_code="duplicate_capability_comparison",
            )
        seen_heads.add(comparison.assessment_head_id)
        seen_repos: set[str] = set()
        for snap in comparison.repositories:
            if snap.repository_id not in dataset_repository_ids:
                raise InvalidValueError(
                    f"snapshot repository not in dataset: {snap.repository_id}",
                    reason_code="capability_repo_not_in_dataset",
                )
            if snap.repository_id in seen_repos:
                raise InvalidValueError(
                    "duplicate repository/head snapshot",
                    reason_code="duplicate_repository_head_snapshot",
                )
            seen_repos.add(snap.repository_id)
            visibility = repository_visibility.get(snap.repository_id)
            if (
                visibility_policy is VisibilityAggregationScope.PUBLIC_OSS
                and visibility is not None
                and visibility is not DataVisibility.PUBLIC
            ):
                raise InvalidValueError(
                    f"private repository ID leaked into public capability comparison: "
                    f"{snap.repository_id}",
                    reason_code="private_ref_leak",
                )
            for name in ("finding_count", "recommendation_count", "priority_action_count"):
                if getattr(snap, name) < 0:
                    raise InvalidValueError(
                        f"{name} must be non-negative",
                        reason_code=f"negative_{name}",
                    )
        if comparison.distribution.coverage_total not in {0, len(comparison.repositories)}:
            raise InvalidValueError(
                "coverage distribution must reconcile with snapshots",
                reason_code="capability_coverage_mismatch",
            )
        if comparison.distribution.confidence_total not in {0, len(comparison.repositories)}:
            raise InvalidValueError(
                "confidence distribution must reconcile with snapshots",
                reason_code="capability_confidence_mismatch",
            )
        _reject_forbidden_text(" ".join(comparison.limitations))

    dist_heads = [item.assessment_head_id for item in head_distributions]
    if len(dist_heads) != len(set(dist_heads)):
        raise InvalidValueError(
            "duplicate AssessmentHeadDistribution for assessment head",
            reason_code="duplicate_head_distribution",
        )
    for item in head_distributions:
        _reject_forbidden_text(" ".join(item.limitations))
        for field_name in _FORBIDDEN_FIELDS:
            if hasattr(item, field_name):
                raise InvalidValueError(
                    f"forbidden field present on AssessmentHeadDistribution: {field_name}",
                    reason_code="forbidden_score_or_trend_field",
                )


def _reject_forbidden_text(blob: str) -> None:
    lowered = blob.lower()
    # Allow required disclaimer text that mentions what comparisons do *not* measure.
    for token in (
        "improving",
        "declining",
        "increasing",
        "decreasing",
        "progress",
        "regression",
        "maturity score",
        "best repository",
        "worst repository",
        "is the riskiest",
        "team performs better",
    ):
        if token in lowered:
            raise InvalidValueError(
                f"forbidden comparative/trend wording: {token}",
                reason_code="forbidden_capability_wording",
            )
