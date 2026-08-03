"""CapabilityComparisonPolicy and diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.domain.capability import (
    AssessmentHeadDistribution,
    CapabilityComparison,
)


class PriorityActionOwnershipPolicy(StrEnum):
    """Primary-head ownership: one PA counts under one canonical head only."""

    PRIMARY_HEAD = "primary_head"


class LegacyCapabilityPolicy(StrEnum):
    INCLUDE_LIMITED = "include_limited"
    EXCLUDE = "exclude"


class UnknownHeadPolicy(StrEnum):
    REJECT = "reject"
    SKIP = "skip"


@dataclass(frozen=True, slots=True)
class CapabilityComparisonPolicy:
    policy_id: str = "capability-comparison"
    policy_version: str = "v1"
    included_assessment_heads: tuple[str, ...] = ()
    repository_inclusion_policy: str = "dataset_included_repositories"
    comparability_policy: str = "per_head_comparability"
    coverage_denominator_policy: str = "head_available_or_disabled"
    confidence_distribution_policy: str = "one_value_per_repository_head"
    count_presentation_policy: str = "entity_count_and_repository_presence"
    severity_projection_policy: str = "highest_calibrated_finding_severity"
    priority_action_ownership_policy: PriorityActionOwnershipPolicy = (
        PriorityActionOwnershipPolicy.PRIMARY_HEAD
    )
    legacy_policy: LegacyCapabilityPolicy = LegacyCapabilityPolicy.INCLUDE_LIMITED
    visibility_policy: VisibilityAggregationScope = VisibilityAggregationScope.MIXED_INTERNAL
    unknown_head_policy: UnknownHeadPolicy = UnknownHeadPolicy.SKIP
    minimum_comparable_repository_count: int = 1
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.minimum_comparable_repository_count < 1:
            raise ValueError("minimum_comparable_repository_count must be >= 1")
        if not self.policy_id.strip() or not self.policy_version.strip():
            raise ValueError("policy_id and policy_version are required")
        # Ranking / composite score configuration is prohibited.
        forbidden = {
            "maturity_score",
            "readiness_score",
            "health_score",
            "ranking",
            "percentile",
            "league_table",
            "composite_score",
        }
        blob = " ".join(
            [
                self.repository_inclusion_policy,
                self.comparability_policy,
                self.count_presentation_policy,
                *self.limitations,
            ]
        ).lower()
        for token in forbidden:
            if token in blob.replace("-", "_").replace(" ", "_"):
                raise ValueError(f"ranking/score configuration prohibited: {token}")

    @property
    def policy_token(self) -> str:
        return (
            f"{self.policy_id}:{self.policy_version}:"
            f"{self.priority_action_ownership_policy.value}:"
            f"{self.legacy_policy.value}"
        )


@dataclass(frozen=True, slots=True)
class CapabilityComparisonDiagnostics:
    input_head_fact_count: int = 0
    comparison_count: int = 0
    repository_snapshot_count: int = 0
    comparable_snapshot_count: int = 0
    limited_snapshot_count: int = 0
    unavailable_snapshot_count: int = 0
    empty_head_count: int = 0
    missing_coverage_count: int = 0
    missing_confidence_count: int = 0
    excluded_repository_count: int = 0
    unresolved_reference_count: int = 0
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CapabilityComparisonResult:
    comparisons: tuple[CapabilityComparison, ...]
    head_distributions: tuple[AssessmentHeadDistribution, ...]
    diagnostics: CapabilityComparisonDiagnostics
    policy_token: str
