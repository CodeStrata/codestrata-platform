"""RecurringPatternPolicy and diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.domain.enums import PatternType
from codestrata_platform.intelligence_reporting.domain.patterns import (
    PATTERN_POLICY_VERSION,
    RecurringIntelligencePattern,
)


class LegacyPatternPolicy(StrEnum):
    EXCLUDE = "exclude"
    LIMITED = "limited"
    REJECT = "reject"


class UnknownIdentityPolicy(StrEnum):
    SKIP = "skip"
    REJECT = "reject"


IDENTITY_POLICY_VERSION = "recurring-pattern-identity-v1"
STATEMENT_TEMPLATE_VERSION = "recurring-pattern-statement-v1"

_DEFAULT_TYPES: tuple[PatternType, ...] = (
    PatternType.RECURRING_RULE,
    PatternType.RECURRING_CONFIGURATION_CONDITION,
    PatternType.RECURRING_DEPENDENCY_CONDITION,
    PatternType.RECURRING_ARCHITECTURE_CONDITION,
    PatternType.RECURRING_COMPLEXITY_CONDITION,
    PatternType.RECURRING_RECOMMENDATION,
    PatternType.RECURRING_TECHNOLOGY_CONDITION,
)


@dataclass(frozen=True, slots=True)
class RecurringPatternPolicy:
    policy_id: str = "recurring-patterns"
    policy_version: str = "v1"
    included_pattern_types: tuple[PatternType, ...] = _DEFAULT_TYPES
    included_assessment_heads: tuple[str, ...] = ()
    minimum_repository_count: int = 2
    minimum_repository_ratio: float = 0.0
    identity_policy_version: str = IDENTITY_POLICY_VERSION
    rule_pattern_policy: str = "rule_id_and_assessment_head"
    recommendation_pattern_policy: str = "provider_or_category_and_head"
    priority_action_pattern_policy: str = "deferred_without_stable_intent"
    technology_pattern_policy: str = "conflict_only_not_prevalence"
    legacy_policy: LegacyPatternPolicy = LegacyPatternPolicy.LIMITED
    comparability_policy: str = "comparable_or_partially_comparable"
    visibility_policy: VisibilityAggregationScope = VisibilityAggregationScope.MIXED_INTERNAL
    statement_template_version: str = STATEMENT_TEMPLATE_VERSION
    allow_single_repository: bool = False
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.minimum_repository_count < 2 and not self.allow_single_repository:
            raise ValueError(
                "minimum_repository_count must be >= 2 unless allow_single_repository"
            )
        if self.allow_single_repository:
            raise ValueError(
                "one-repository recurring patterns are prohibited for Slice 6.6"
            )
        if not (0.0 <= self.minimum_repository_ratio <= 1.0):
            raise ValueError("minimum_repository_ratio must be between 0 and 1")
        if not self.policy_id.strip() or not self.policy_version.strip():
            raise ValueError("policy_id and policy_version are required")
        object.__setattr__(
            self,
            "included_pattern_types",
            tuple(sorted(self.included_pattern_types, key=lambda item: item.value)),
        )

    @property
    def policy_token(self) -> str:
        return (
            f"{self.policy_id}:{self.policy_version}:"
            f"{self.identity_policy_version}:{self.statement_template_version}"
        )

    @property
    def domain_policy_version(self) -> str:
        """Version embedded in Slice 6.1 pattern_id material."""

        return f"{PATTERN_POLICY_VERSION}:{self.identity_policy_version}"


@dataclass(frozen=True, slots=True)
class RecurringPatternDiagnostics:
    finding_occurrence_count: int = 0
    recommendation_occurrence_count: int = 0
    priority_action_occurrence_count: int = 0
    candidate_count: int = 0
    accepted_pattern_count: int = 0
    rejected_candidate_count: int = 0
    below_threshold_count: int = 0
    legacy_limited_count: int = 0
    unavailable_denominator_count: int = 0
    unresolved_reference_count: int = 0
    patterns_by_type: tuple[tuple[str, int], ...] = ()
    patterns_by_head: tuple[tuple[str, int], ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RecurringPatternResult:
    patterns: tuple[RecurringIntelligencePattern, ...]
    diagnostics: RecurringPatternDiagnostics
    policy_token: str
