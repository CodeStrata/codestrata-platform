"""Portfolio recommendation inventory value objects."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.engineering.enums import EngineeringCategory
from codestrata_platform.domain.portfolio.lifecycle import PriorityBand
from codestrata_platform.domain.repository.ids import RepositoryId


@dataclass(frozen=True, slots=True)
class RecommendationConcentration:
    repository_count: int
    recommendation_count: int


@dataclass(frozen=True, slots=True)
class PortfolioRecommendationPriority:
    score: int
    band: PriorityBand
    contributing_factors: tuple[str, ...]
    policy_version: str


@dataclass(frozen=True, slots=True)
class RecurringRecommendationPattern:
    recurrence_key: str
    canonical_recommendation_id: str | None
    category: EngineeringCategory
    priority: str
    linked_finding_rule: str | None
    target_technology: str | None
    target_component: str | None
    roadmap_horizon: str | None
    repository_count: int
    recommendation_count: int
    affected_repositories: tuple[RepositoryId, ...]
    priority_score: PortfolioRecommendationPriority
    concentration: RecommendationConcentration
    source_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RecommendationCoverageGap:
    gap_key: str
    finding_rule_id: str
    category: EngineeringCategory
    severity: str
    repository_count: int
    finding_count: int
    affected_repositories: tuple[RepositoryId, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class PortfolioRecommendationSummary:
    total_recommendations: int
    repository_count: int
    recurring_patterns: tuple[RecurringRecommendationPattern, ...]
    coverage_gaps: tuple[RecommendationCoverageGap, ...]
