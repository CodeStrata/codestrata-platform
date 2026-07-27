"""Portfolio technology inventory value objects."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.portfolio.identifiers import PortfolioTechnologyId
from codestrata_platform.domain.portfolio.lifecycle import (
    TechnologyLifecycleSignal,
    TechnologyStandardizationStatus,
)
from codestrata_platform.domain.repository.ids import RepositoryId


@dataclass(frozen=True, slots=True)
class TechnologyConcentration:
    repository_count: int
    usage_percentage: float
    production_usage_count: int


@dataclass(frozen=True, slots=True)
class PortfolioTechnologyUsage:
    repository_id: RepositoryId
    engineering_snapshot_id: str
    component_count: int
    finding_count: int
    high_critical_finding_count: int
    recommendation_count: int
    production_scope: bool = False


@dataclass(frozen=True, slots=True)
class PortfolioTechnology:
    technology_id: PortfolioTechnologyId
    canonical_key: str
    normalized_name: str
    framework: str | None
    categories: tuple[str, ...]
    repository_count: int
    repository_references: tuple[RepositoryId, ...]
    component_count: int
    finding_count: int
    high_critical_finding_count: int
    recommendation_count: int
    usage_percentage: float
    production_usage_count: int
    lifecycle_signal: TechnologyLifecycleSignal
    standardization_status: TechnologyStandardizationStatus
    concentration: TechnologyConcentration
    source_snapshot_references: tuple[str, ...]
    usages: tuple[PortfolioTechnologyUsage, ...] = ()
