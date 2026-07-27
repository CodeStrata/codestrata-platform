"""Portfolio modernization value objects."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.portfolio.lifecycle import (
    ModernizationTheme,
    ModernizationWave,
    PriorityBand,
)
from codestrata_platform.domain.repository.ids import RepositoryId


@dataclass(frozen=True, slots=True)
class ModernizationPriorityScore:
    score: int
    band: PriorityBand
    confidence: float
    contributing_factors: tuple[str, ...]
    policy_version: str


@dataclass(frozen=True, slots=True)
class ModernizationDependency:
    dependency_key: str
    description: str
    blocking: bool


@dataclass(frozen=True, slots=True)
class ModernizationConstraint:
    constraint_key: str
    description: str
    unresolved: bool


@dataclass(frozen=True, slots=True)
class ModernizationCandidate:
    candidate_id: str
    repository_id: RepositoryId
    theme: ModernizationTheme
    priority: ModernizationPriorityScore
    wave: ModernizationWave
    affected_technologies: tuple[str, ...]
    affected_components: tuple[str, ...]
    related_findings: tuple[str, ...]
    related_recommendations: tuple[str, ...]
    dependency_constraints: tuple[ModernizationDependency, ...]
    constraints: tuple[ModernizationConstraint, ...]
    evidence_coverage: float
    source_snapshot_references: tuple[str, ...]
    wave_factors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PortfolioModernizationSummary:
    candidates: tuple[ModernizationCandidate, ...]
    theme_counts: tuple[tuple[ModernizationTheme, int], ...]
    wave_counts: tuple[tuple[ModernizationWave, int], ...]
    policy_version: str
