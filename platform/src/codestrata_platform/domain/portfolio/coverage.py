"""Portfolio coverage and freshness value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.portfolio.lifecycle import (
    AssessmentFreshnessStatus,
    RepositoryAvailabilityStatus,
)
from codestrata_platform.domain.repository.ids import RepositoryId


@dataclass(frozen=True, slots=True)
class RepositoryCoverageStatus:
    repository_id: RepositoryId
    availability_status: RepositoryAvailabilityStatus
    has_published_snapshot: bool
    has_completed_graph: bool
    has_retrieval_index: bool
    freshness_status: AssessmentFreshnessStatus
    assessment_age_days: int | None
    engineering_snapshot_id: str | None
    selected_at: datetime | None


@dataclass(frozen=True, slots=True)
class AssessmentFreshnessSummary:
    current_count: int
    aging_count: int
    stale_count: int
    unknown_count: int
    evaluated_at: datetime
    policy_version: str
    current_threshold_days: int
    aging_threshold_days: int


@dataclass(frozen=True, slots=True)
class EvidenceCoverageSummary:
    findings_total: int
    findings_with_evidence: int
    coverage_ratio: float


@dataclass(frozen=True, slots=True)
class RecommendationCoverageSummary:
    high_critical_findings: int
    high_critical_with_recommendations: int
    coverage_ratio: float


@dataclass(frozen=True, slots=True)
class GraphCoverageSummary:
    repositories_with_graphs: int
    repositories_total: int
    coverage_ratio: float


@dataclass(frozen=True, slots=True)
class PortfolioCoverageSummary:
    repositories_total: int
    repositories_with_published_snapshots: int
    repositories_without_assessments: int
    repositories_unavailable: int
    repository_participation_percentage: float
    repository_statuses: tuple[RepositoryCoverageStatus, ...]
    freshness: AssessmentFreshnessSummary
    evidence: EvidenceCoverageSummary
    recommendations: RecommendationCoverageSummary
    graphs: GraphCoverageSummary
    technology_coverage_count: int
