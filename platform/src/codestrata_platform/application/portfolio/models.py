"""Portfolio application read models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.portfolio.coverage import PortfolioCoverageSummary
from codestrata_platform.domain.portfolio.finding import PortfolioFindingSummary
from codestrata_platform.domain.portfolio.lifecycle import (
    PortfolioSnapshotStatus,
    PortfolioStatus,
    RepositoryCriticality,
)
from codestrata_platform.domain.portfolio.modernization import PortfolioModernizationSummary
from codestrata_platform.domain.portfolio.recommendation import PortfolioRecommendationSummary
from codestrata_platform.domain.portfolio.risk import PortfolioRiskSummary
from codestrata_platform.domain.portfolio.snapshot import PortfolioRepositorySnapshotSelection
from codestrata_platform.domain.portfolio.taxonomy import SharedDependencySummary
from codestrata_platform.domain.portfolio.technology import PortfolioTechnology


@dataclass(frozen=True, slots=True)
class PortfolioMembershipSummary:
    membership_id: str
    repository_id: str
    criticality: RepositoryCriticality
    business_capability: str | None
    owner_reference: str | None
    lifecycle_status: str | None
    tags: tuple[str, ...]
    added_at: datetime
    removed_at: datetime | None
    active: bool


@dataclass(frozen=True, slots=True)
class PortfolioSummary:
    portfolio_id: str
    organization_id: str
    workspace_id: str
    name: str
    description: str | None
    status: PortfolioStatus
    repository_count: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


@dataclass(frozen=True, slots=True)
class PortfolioDetails:
    summary: PortfolioSummary
    memberships: tuple[PortfolioMembershipSummary, ...]


@dataclass(frozen=True, slots=True)
class PortfolioSnapshotSummary:
    portfolio_snapshot_id: str
    portfolio_id: str
    organization_id: str
    workspace_id: str
    snapshot_version: int
    status: PortfolioSnapshotStatus
    projection_key: str
    aggregation_policy_version: str
    repository_count: int
    available_repository_count: int
    unavailable_repository_count: int
    created_at: datetime
    completed_at: datetime | None
    superseded_at: datetime | None
    failure_reason: str | None


@dataclass(frozen=True, slots=True)
class PortfolioAggregateEnvelope:
    portfolio_id: str
    portfolio_snapshot_id: str
    portfolio_snapshot_version: int
    generated_at: datetime
    aggregation_policy_version: str
    selected_repository_count: int
    unavailable_repository_count: int
    source_snapshot_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PortfolioSnapshotDetails:
    summary: PortfolioSnapshotSummary
    repository_selections: tuple[PortfolioRepositorySnapshotSelection, ...]
    envelope: PortfolioAggregateEnvelope


@dataclass(frozen=True, slots=True)
class PortfolioTechnologySummaryModel:
    envelope: PortfolioAggregateEnvelope
    items: tuple[PortfolioTechnology, ...]
    total: int


@dataclass(frozen=True, slots=True)
class PortfolioFindingSummaryModel:
    envelope: PortfolioAggregateEnvelope
    summary: PortfolioFindingSummary


@dataclass(frozen=True, slots=True)
class PortfolioRecommendationSummaryModel:
    envelope: PortfolioAggregateEnvelope
    summary: PortfolioRecommendationSummary


@dataclass(frozen=True, slots=True)
class PortfolioRiskSummaryModel:
    envelope: PortfolioAggregateEnvelope
    summary: PortfolioRiskSummary


@dataclass(frozen=True, slots=True)
class PortfolioModernizationSummaryModel:
    envelope: PortfolioAggregateEnvelope
    summary: PortfolioModernizationSummary


@dataclass(frozen=True, slots=True)
class PortfolioCoverageSummaryModel:
    envelope: PortfolioAggregateEnvelope
    summary: PortfolioCoverageSummary


@dataclass(frozen=True, slots=True)
class PortfolioRepositoryProfile:
    repository_id: str
    criticality: RepositoryCriticality
    availability_status: str
    engineering_snapshot_id: str | None
    engineering_snapshot_version: int | None
    knowledge_graph_id: str | None
    risk_score: int | None
    risk_band: str | None
    finding_count: int
    high_critical_count: int
    technology_count: int
    recommendation_count: int
    freshness_status: str | None


@dataclass(frozen=True, slots=True)
class PortfolioEngineeringOverview:
    envelope: PortfolioAggregateEnvelope
    technologies: tuple[PortfolioTechnology, ...]
    findings: PortfolioFindingSummary
    recommendations: PortfolioRecommendationSummary
    risk: PortfolioRiskSummary
    modernization: PortfolioModernizationSummary
    coverage: PortfolioCoverageSummary
    dependencies: SharedDependencySummary
    repository_profiles: tuple[PortfolioRepositoryProfile, ...]
