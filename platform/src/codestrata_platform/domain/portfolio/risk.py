"""Portfolio risk value objects."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.engineering.enums import EngineeringCategory, EngineeringSeverity
from codestrata_platform.domain.portfolio.lifecycle import PriorityBand
from codestrata_platform.domain.repository.ids import RepositoryId


@dataclass(frozen=True, slots=True)
class PortfolioRiskDistribution:
    severity: EngineeringSeverity
    count: int


@dataclass(frozen=True, slots=True)
class PortfolioRiskConcentration:
    dimension: str
    key: str
    repository_count: int
    finding_count: int
    high_critical_count: int
    score: int
    band: PriorityBand
    factors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PortfolioRiskHotspot:
    hotspot_key: str
    repository_id: RepositoryId | None
    technology_key: str | None
    category: EngineeringCategory | None
    score: int
    band: PriorityBand
    factors: tuple[str, ...]
    source_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RepositoryRiskProfile:
    repository_id: RepositoryId
    score: int
    band: PriorityBand
    finding_count: int
    high_critical_count: int
    evidence_gap_count: int
    recommendation_gap_count: int
    factors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TechnologyRiskProfile:
    technology_key: str
    score: int
    band: PriorityBand
    repository_count: int
    high_critical_count: int
    factors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SystemicRisk:
    systemic_key: str
    title: str
    score: int
    band: PriorityBand
    repository_count: int
    evidence: tuple[str, ...]
    factors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PortfolioRiskSummary:
    overall_score: int
    overall_band: PriorityBand
    severity_distribution: tuple[PortfolioRiskDistribution, ...]
    concentrations: tuple[PortfolioRiskConcentration, ...]
    hotspots: tuple[PortfolioRiskHotspot, ...]
    repository_profiles: tuple[RepositoryRiskProfile, ...]
    technology_profiles: tuple[TechnologyRiskProfile, ...]
    systemic_risks: tuple[SystemicRisk, ...]
    policy_version: str
