"""Portfolio finding inventory value objects."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.engineering.enums import EngineeringCategory, EngineeringSeverity
from codestrata_platform.domain.repository.ids import RepositoryId


@dataclass(frozen=True, slots=True)
class FindingConcentration:
    repository_count: int
    finding_count: int
    production_count: int


@dataclass(frozen=True, slots=True)
class PortfolioFindingDistribution:
    severity: EngineeringSeverity
    count: int


@dataclass(frozen=True, slots=True)
class RecurringFindingPattern:
    recurrence_key: str
    rule_id: str
    category: EngineeringCategory
    normalized_title_id: str
    technology_key: str | None
    repository_count: int
    finding_count: int
    affected_repositories: tuple[RepositoryId, ...]
    severity_distribution: tuple[PortfolioFindingDistribution, ...]
    production_count: int
    evidence_coverage: float
    recommendation_coverage: float
    concentration: FindingConcentration
    source_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PortfolioFindingCluster:
    cluster_key: str
    patterns: tuple[RecurringFindingPattern, ...]


@dataclass(frozen=True, slots=True)
class PortfolioFindingSummary:
    total_findings: int
    repository_count: int
    high_critical_count: int
    recurring_patterns: tuple[RecurringFindingPattern, ...]
    clusters: tuple[PortfolioFindingCluster, ...]
    severity_distribution: tuple[PortfolioFindingDistribution, ...]
