"""TechnologyDistributionPolicy and diagnostics models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution.normalization import (
    NORMALIZATION_POLICY_VERSION,
)
from codestrata_platform.intelligence_reporting.domain.technology import TechnologyDistribution


class TechnologyVersionGroupingPolicy(StrEnum):
    PRESERVE_EXPLICIT = "preserve_explicit"
    GROUP_BY_EXACT_STRING = "group_by_exact_string"


class ConflictingVersionPolicy(StrEnum):
    PRESERVE_EXPLICIT_ONLY = "preserve_explicit_only"


class UnavailableVersionPolicy(StrEnum):
    PRESERVE = "preserve"


@dataclass(frozen=True, slots=True)
class TechnologyDistributionPolicy:
    policy_id: str = "technology-distribution"
    policy_version: str = "v1"
    included_categories: tuple[str, ...] = ()
    normalization_policy_version: str = NORMALIZATION_POLICY_VERSION
    repository_presence_policy: str = "distinct_eligible_repositories"
    version_grouping_policy: TechnologyVersionGroupingPolicy = (
        TechnologyVersionGroupingPolicy.GROUP_BY_EXACT_STRING
    )
    conflicting_version_policy: ConflictingVersionPolicy = (
        ConflictingVersionPolicy.PRESERVE_EXPLICIT_ONLY
    )
    unavailable_version_policy: UnavailableVersionPolicy = UnavailableVersionPolicy.PRESERVE
    minimum_repository_count: int = 1
    visibility_policy: VisibilityAggregationScope = VisibilityAggregationScope.MIXED_INTERNAL
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.minimum_repository_count < 1:
            raise ValueError("minimum_repository_count must be >= 1")
        if not self.policy_id.strip() or not self.policy_version.strip():
            raise ValueError("policy_id and policy_version are required")

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}:{self.normalization_policy_version}"


@dataclass(frozen=True, slots=True)
class TechnologyDistributionDiagnostics:
    input_fact_count: int = 0
    normalized_fact_count: int = 0
    distinct_technology_count: int = 0
    eligible_repository_count: int = 0
    unavailable_repository_count: int = 0
    conflicting_version_repository_count: int = 0
    unavailable_version_fact_count: int = 0
    alias_normalization_count: int = 0
    rejected_fact_count: int = 0
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TechnologyDistributionResult:
    distribution: TechnologyDistribution
    diagnostics: TechnologyDistributionDiagnostics
    policy_token: str
