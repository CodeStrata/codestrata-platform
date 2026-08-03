"""ModernizationObservationPolicy and diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ModernizationObservationCategory,
)
from codestrata_platform.intelligence_reporting.domain.modernization import (
    MODERNIZATION_OBSERVATION_POLICY_VERSION,
    ModernizationObservation,
)

ACTION_IDENTITY_CATALOG_VERSION = "modernization-action-identity-v1"
STATEMENT_TEMPLATE_VERSION = "modernization-observation-statement-v1"
CONFIDENCE_POLICY_VERSION = "modernization-observation-confidence-v1"
PATTERN_SUPPORT_CATALOG_VERSION = "modernization-pattern-support-v1"


class LegacyObservationPolicy(StrEnum):
    EXCLUDE = "exclude"
    LIMITED = "limited"
    REJECT = "reject"


_DEFAULT_CATEGORIES: tuple[ModernizationObservationCategory, ...] = (
    ModernizationObservationCategory.SECURITY_REMEDIATION,
    ModernizationObservationCategory.DEPENDENCY_GOVERNANCE,
    ModernizationObservationCategory.ARCHITECTURE_MODERNIZATION,
    ModernizationObservationCategory.MAINTAINABILITY,
    ModernizationObservationCategory.TESTING_ENABLEMENT,
    ModernizationObservationCategory.CLOUD_ENABLEMENT,
    ModernizationObservationCategory.AI_ENABLEMENT,
    ModernizationObservationCategory.SHARED_FOUNDATION,
    ModernizationObservationCategory.OPERATIONAL_READINESS,
)


@dataclass(frozen=True, slots=True)
class ModernizationObservationPolicy:
    policy_id: str = "modernization-observations"
    policy_version: str = "v1"
    included_categories: tuple[ModernizationObservationCategory, ...] = _DEFAULT_CATEGORIES
    included_assessment_heads: tuple[str, ...] = ()
    minimum_repository_count: int = 2
    minimum_repository_ratio: float = 0.0
    required_support_types: tuple[str, ...] = ("recommendation",)
    recommendation_identity_policy: str = "provider_or_category_and_head"
    priority_action_support_policy: str = "primary_recommendation_action_identity"
    roadmap_support_policy: str = "pa_backed_only"
    recurring_pattern_support_policy: str = "reviewed_catalog_only"
    legacy_policy: LegacyObservationPolicy = LegacyObservationPolicy.LIMITED
    comparability_policy: str = "comparable_or_partially_comparable"
    visibility_policy: VisibilityAggregationScope = VisibilityAggregationScope.MIXED_INTERNAL
    confidence_policy_version: str = CONFIDENCE_POLICY_VERSION
    statement_template_version: str = STATEMENT_TEMPLATE_VERSION
    action_identity_catalog_version: str = ACTION_IDENTITY_CATALOG_VERSION
    allow_single_repository: bool = False
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.minimum_repository_count < 2 and not self.allow_single_repository:
            raise ValueError(
                "minimum_repository_count must be >= 2 unless allow_single_repository"
            )
        if self.allow_single_repository:
            raise ValueError(
                "one-repository portfolio modernization observations are prohibited"
            )
        if not (0.0 <= self.minimum_repository_ratio <= 1.0):
            raise ValueError("minimum_repository_ratio must be between 0 and 1")
        if not self.policy_id.strip() or not self.policy_version.strip():
            raise ValueError("policy_id and policy_version are required")
        object.__setattr__(
            self,
            "included_categories",
            tuple(sorted(self.included_categories, key=lambda item: item.value)),
        )

    @property
    def policy_token(self) -> str:
        return (
            f"{self.policy_id}:{self.policy_version}:"
            f"{self.action_identity_catalog_version}:"
            f"{self.statement_template_version}"
        )

    @property
    def domain_policy_version(self) -> str:
        return (
            f"{MODERNIZATION_OBSERVATION_POLICY_VERSION}:"
            f"{self.action_identity_catalog_version}"
        )


@dataclass(frozen=True, slots=True)
class ModernizationObservationDiagnostics:
    input_recommendation_count: int = 0
    input_priority_action_count: int = 0
    input_roadmap_count: int = 0
    recurring_pattern_support_count: int = 0
    candidate_count: int = 0
    accepted_observation_count: int = 0
    below_threshold_count: int = 0
    rejected_candidate_count: int = 0
    legacy_limited_count: int = 0
    incomplete_support_chain_count: int = 0
    unavailable_denominator_count: int = 0
    unresolved_reference_count: int = 0
    observations_by_category: tuple[tuple[str, int], ...] = ()
    observations_by_head: tuple[tuple[str, int], ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ModernizationObservationResult:
    observations: tuple[ModernizationObservation, ...]
    diagnostics: ModernizationObservationDiagnostics
    policy_token: str
