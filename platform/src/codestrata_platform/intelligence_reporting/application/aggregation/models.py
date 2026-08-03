"""Cross-repository aggregation foundation models (factual inputs only).

This aggregation layer produces factual cross-repository inputs. It does not
create recurring-pattern conclusions, portfolio recommendations, or industry
benchmarks.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentComparability,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ActivationStatus,
    ComparabilityStatus,
    ConfidenceLevel,
    CoverageStatus,
    DataVisibility,
    SourceType,
    VersionState,
)
from codestrata_platform.intelligence_reporting.domain.repository_snapshot import (
    RepositoryPopulation,
)
from codestrata_platform.intelligence_reporting.domain.technology import Ratio


class LegacyAssessmentPolicy(StrEnum):
    EXCLUDE = "exclude"
    LIMITED = "limited"
    REJECT = "reject"


class IncomparableRepositoryPolicy(StrEnum):
    EXCLUDE_FROM_CANONICAL_DENOMINATORS = "exclude_from_canonical_denominators"
    INCLUDE_WITH_LIMITATION = "include_with_limitation"
    REJECT = "reject"


class DisabledHeadPolicy(StrEnum):
    EXCLUDE_FROM_EVALUATED = "exclude_from_evaluated"
    INCLUDE_AS_DISABLED = "include_as_disabled"


class UnavailableHeadPolicy(StrEnum):
    EXCLUDE_FROM_EVALUATED = "exclude_from_evaluated"
    INCLUDE_AS_UNAVAILABLE = "include_as_unavailable"


class VisibilityAggregationScope(StrEnum):
    PUBLIC_OSS = "public_oss"
    CUSTOMER_PRIVATE = "customer_private"
    INTERNAL = "internal"
    MIXED_INTERNAL = "mixed_internal"


class DenominatorScope(StrEnum):
    ALL_INCLUDED_REPOSITORIES = "all_included_repositories"
    COMPARABLE_REPOSITORIES = "comparable_repositories"
    ASSESSMENT_HEAD_AVAILABLE = "assessment_head_available"
    ASSESSMENT_HEAD_ACTIVATED = "assessment_head_activated"
    ASSESSMENT_HEAD_EVALUATED = "assessment_head_evaluated"
    TECHNOLOGY_INVENTORY_AVAILABLE = "technology_inventory_available"
    RECOMMENDATION_CAPABLE = "recommendation_capable"
    ROADMAP_AVAILABLE = "roadmap_available"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class IntelligenceAggregationPolicy:
    """Explicit controls for cross-repository factual aggregation."""

    policy_id: str = "intelligence-aggregation"
    policy_version: str = "v1"
    included_assessment_heads: tuple[str, ...] = ()
    repository_counting_policy: str = "distinct_included_repositories"
    entity_deduplication_policy: str = "composite_repository_assessment_entity"
    legacy_assessment_policy: LegacyAssessmentPolicy = LegacyAssessmentPolicy.LIMITED
    incomparable_repository_policy: IncomparableRepositoryPolicy = (
        IncomparableRepositoryPolicy.EXCLUDE_FROM_CANONICAL_DENOMINATORS
    )
    disabled_head_policy: DisabledHeadPolicy = DisabledHeadPolicy.EXCLUDE_FROM_EVALUATED
    unavailable_head_policy: UnavailableHeadPolicy = (
        UnavailableHeadPolicy.EXCLUDE_FROM_EVALUATED
    )
    visibility_policy: VisibilityAggregationScope = VisibilityAggregationScope.MIXED_INTERNAL
    minimum_pattern_repository_count: int = 2
    denominator_policy: str = "explicit_scope_denominators"
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.minimum_pattern_repository_count < 1:
            raise ValueError("minimum_pattern_repository_count must be >= 1")
        if not self.policy_id.strip() or not self.policy_version.strip():
            raise ValueError("policy_id and policy_version are required")

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"


@dataclass(frozen=True, slots=True)
class AggregatedEntityRef:
    """Composite cross-repository entity reference — Engine IDs preserved."""

    repository_id: str
    assessment_id: str
    entity_type: str
    entity_id: str
    assessment_head_id: str | None = None
    canonical_report_reference: str | None = None
    rule_id: str | None = None
    provider_id: str | None = None
    category: str | None = None
    severity: str | None = None
    confidence: str | None = None
    priority: str | None = None
    phase: str | None = None

    @property
    def composite_key(self) -> tuple[str, str, str, str]:
        return (self.repository_id, self.assessment_id, self.entity_type, self.entity_id)


@dataclass(frozen=True, slots=True)
class AggregationDenominator:
    denominator_id: str
    scope: DenominatorScope
    eligible_repository_ids: tuple[str, ...] = ()
    excluded_repository_ids: tuple[str, ...] = ()
    unavailable_repository_ids: tuple[str, ...] = ()
    denominator_count: int = 0
    limitations: tuple[str, ...] = ()
    ratio: Ratio | None = None

    def __post_init__(self) -> None:
        eligible = tuple(sorted(set(self.eligible_repository_ids)))
        object.__setattr__(self, "eligible_repository_ids", eligible)
        object.__setattr__(
            self,
            "excluded_repository_ids",
            tuple(sorted(set(self.excluded_repository_ids))),
        )
        object.__setattr__(
            self,
            "unavailable_repository_ids",
            tuple(sorted(set(self.unavailable_repository_ids))),
        )
        if self.denominator_count != len(eligible):
            raise ValueError("denominator_count must equal eligible_repository_ids length")


@dataclass(frozen=True, slots=True)
class AggregatedRepositoryRecord:
    repository_id: str
    assessment_id: str
    assessment_run_id: str
    canonical_report_digest: str
    source_type: SourceType
    visibility: DataVisibility
    assessment_schema_version: str
    enabled_heads: tuple[str, ...] = ()
    disabled_heads: tuple[str, ...] = ()
    unavailable_heads: tuple[str, ...] = ()
    missing_heads: tuple[str, ...] = ()
    legacy_or_incomplete: bool = False
    comparable: bool = False
    canonical_report_reference: str | None = None
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AggregatedTechnologyFact:
    normalized_name: str
    category: str
    version_state: VersionState
    version: str | None
    repository_id: str
    assessment_id: str
    source_entity_ref: AggregatedEntityRef
    confidence: ConfidenceLevel = ConfidenceLevel.UNAVAILABLE
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AggregatedAssessmentHeadFact:
    repository_id: str
    assessment_id: str
    assessment_head_id: str
    activation_status: ActivationStatus
    coverage_status: CoverageStatus
    confidence_level: ConfidenceLevel
    finding_count: int = 0
    recommendation_count: int = 0
    priority_action_count: int = 0
    highest_severity: str | None = None
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AggregatedFindingFact:
    repository_id: str
    assessment_id: str
    finding_id: str
    rule_id: str
    assessment_head_id: str | None
    severity: str
    finding_confidence: str
    evidence_completeness: str | None = None
    primary_evidence_id: str | None = None
    correlation_ids: tuple[str, ...] = ()
    rule_version: str | None = None
    canonical_subject_ref: str | None = None
    limitations: tuple[str, ...] = ()
    unclassified: bool = False


@dataclass(frozen=True, slots=True)
class AggregatedRecommendationFact:
    repository_id: str
    assessment_id: str
    recommendation_id: str
    provider_id: str | None
    category: str
    priority: str
    recommendation_confidence: str
    supporting_finding_ids: tuple[str, ...] = ()
    primary_finding_id: str | None = None
    priority_score: str | None = None
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AggregatedPriorityActionFact:
    repository_id: str
    assessment_id: str
    priority_action_id: str
    priority: str
    supporting_recommendation_ids: tuple[str, ...] = ()
    supporting_finding_ids: tuple[str, ...] = ()
    priority_score: str | None = None
    presentation_bucket: str | None = None
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AggregatedRoadmapFact:
    repository_id: str
    assessment_id: str
    initiative_id: str
    phase: str | None
    initiative_type: str | None
    supporting_priority_action_ids: tuple[str, ...] = ()
    supporting_recommendation_ids: tuple[str, ...] = ()
    supporting_finding_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AggregatedCorrelationFact:
    repository_id: str
    assessment_id: str
    correlation_id: str
    correlation_type: str
    finding_ids: tuple[str, ...] = ()
    assessment_head_ids: tuple[str, ...] = ()
    confidence: str | None = None
    basis: str | None = None
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AggregatedCoverageFact:
    repository_id: str
    assessment_id: str
    assessment_head_id: str
    coverage_status: str
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AggregatedConfidenceFact:
    repository_id: str
    assessment_id: str
    assessment_head_id: str
    confidence_level: str
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AggregationDiagnostics:
    included_repository_count: int = 0
    excluded_repository_count: int = 0
    legacy_repository_count: int = 0
    comparable_repository_count: int = 0
    technology_fact_count: int = 0
    finding_fact_count: int = 0
    recommendation_fact_count: int = 0
    priority_action_fact_count: int = 0
    roadmap_fact_count: int = 0
    correlation_fact_count: int = 0
    unresolved_reference_count: int = 0
    duplicate_reference_count: int = 0
    unavailable_denominator_count: int = 0
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AggregateCounts:
    repository_count: int = 0
    technology_occurrence_count: int = 0
    technology_repository_presence_count: int = 0
    finding_count: int = 0
    recommendation_count: int = 0
    priority_action_count: int = 0
    roadmap_initiative_count: int = 0
    correlation_count: int = 0


@dataclass(frozen=True, slots=True)
class CrossRepositoryAggregation:
    """Factual cross-repository aggregation — not an EngineeringIntelligenceReport."""

    aggregation_id: str
    dataset_id: str
    policy_id: str
    policy_version: str
    repository_population: RepositoryPopulation
    repository_index: tuple[AggregatedRepositoryRecord, ...] = ()
    assessment_index: tuple[AggregatedEntityRef, ...] = ()
    technology_facts: tuple[AggregatedTechnologyFact, ...] = ()
    assessment_head_facts: tuple[AggregatedAssessmentHeadFact, ...] = ()
    finding_facts: tuple[AggregatedFindingFact, ...] = ()
    recommendation_facts: tuple[AggregatedRecommendationFact, ...] = ()
    priority_action_facts: tuple[AggregatedPriorityActionFact, ...] = ()
    roadmap_facts: tuple[AggregatedRoadmapFact, ...] = ()
    correlation_facts: tuple[AggregatedCorrelationFact, ...] = ()
    coverage_facts: tuple[AggregatedCoverageFact, ...] = ()
    confidence_facts: tuple[AggregatedConfidenceFact, ...] = ()
    denominators: tuple[AggregationDenominator, ...] = ()
    aggregate_counts: AggregateCounts = field(default_factory=AggregateCounts)
    comparability: AssessmentComparability | None = None
    comparability_status: ComparabilityStatus = ComparabilityStatus.UNKNOWN
    limitations: tuple[str, ...] = ()
    diagnostics: AggregationDiagnostics = field(default_factory=AggregationDiagnostics)
