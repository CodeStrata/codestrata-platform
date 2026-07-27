"""Portfolio persistence and source-intelligence ports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from codestrata_platform.domain.engineering.aggregate import EngineeringSnapshot
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio.lifecycle import PortfolioSnapshotStatus, PortfolioStatus
from codestrata_platform.domain.portfolio.portfolio import EngineeringPortfolio
from codestrata_platform.domain.portfolio.snapshot import PortfolioSnapshot
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class PublishedRepositoryIntelligence:
    """Bounded published repository intelligence for portfolio aggregation."""

    repository_id: RepositoryId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    assessment_id: str
    engineering_snapshot: EngineeringSnapshot
    knowledge_graph_id: str | None
    knowledge_graph_version: int | None
    graph_intelligence_policy_version: str | None
    has_retrieval_index: bool
    published_at: datetime | None
    explicit_repository_dependencies: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PortfolioRefreshCandidate:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    reasons: tuple[str, ...]


class EngineeringPortfolioRepository(Protocol):
    def get(self, portfolio_id: PortfolioId) -> EngineeringPortfolio | None: ...

    def save(self, portfolio: EngineeringPortfolio) -> None: ...

    def list_by_workspace(
        self,
        workspace_id: WorkspaceId,
        *,
        status: PortfolioStatus | None = None,
    ) -> tuple[EngineeringPortfolio, ...]: ...

    def list_by_organization(
        self,
        organization_id: OrganizationId,
        *,
        status: PortfolioStatus | None = None,
    ) -> tuple[EngineeringPortfolio, ...]: ...

    def list_containing_repository(
        self,
        repository_id: RepositoryId,
    ) -> tuple[EngineeringPortfolio, ...]: ...


class PortfolioSnapshotRepository(Protocol):
    def get(self, portfolio_snapshot_id: PortfolioSnapshotId) -> PortfolioSnapshot | None: ...

    def save(self, snapshot: PortfolioSnapshot) -> None: ...

    def find_completed_by_projection_key(
        self,
        projection_key: str,
    ) -> PortfolioSnapshot | None: ...

    def get_latest_completed(
        self,
        portfolio_id: PortfolioId,
    ) -> PortfolioSnapshot | None: ...

    def list_by_portfolio(
        self,
        portfolio_id: PortfolioId,
        *,
        status: PortfolioSnapshotStatus | None = None,
        limit: int = 50,
    ) -> tuple[PortfolioSnapshot, ...]: ...

    def latest_version_for_portfolio(self, portfolio_id: PortfolioId) -> int: ...


class PortfolioQueryRepository(Protocol):
    def get_snapshot(
        self,
        portfolio_snapshot_id: PortfolioSnapshotId,
    ) -> PortfolioSnapshot | None: ...

    def list_technologies(
        self,
        portfolio_snapshot_id: PortfolioSnapshotId,
        *,
        technology: str | None = None,
        framework: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[object, ...]: ...

    def list_findings(
        self,
        portfolio_snapshot_id: PortfolioSnapshotId,
        *,
        category: str | None = None,
        severity: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[object, ...]: ...

    def list_recommendations(
        self,
        portfolio_snapshot_id: PortfolioSnapshotId,
        *,
        category: str | None = None,
        priority: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[object, ...]: ...


class PortfolioSourceIntelligenceRepository(Protocol):
    """Bounded read access to published repository Platform intelligence."""

    def load_latest_published(
        self,
        *,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
        repository_id: RepositoryId,
    ) -> PublishedRepositoryIntelligence | None: ...
