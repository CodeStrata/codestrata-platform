"""Portfolio application queries."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio.lifecycle import PortfolioStatus
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class GetPortfolioQuery:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId


@dataclass(frozen=True, slots=True)
class ListPortfoliosQuery:
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    status: PortfolioStatus | None = None
    offset: int = 0
    limit: int = 50


@dataclass(frozen=True, slots=True)
class ListPortfolioRepositoriesQuery:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    offset: int = 0
    limit: int = 50


@dataclass(frozen=True, slots=True)
class GetPortfolioSnapshotQuery:
    portfolio_snapshot_id: PortfolioSnapshotId
    organization_id: OrganizationId | None = None
    workspace_id: WorkspaceId | None = None


@dataclass(frozen=True, slots=True)
class GetLatestPortfolioSnapshotQuery:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId


@dataclass(frozen=True, slots=True)
class ListPortfolioSnapshotsQuery:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    offset: int = 0
    limit: int = 50


@dataclass(frozen=True, slots=True)
class PortfolioInventoryQuery:
    portfolio_snapshot_id: PortfolioSnapshotId
    organization_id: OrganizationId | None = None
    workspace_id: WorkspaceId | None = None
    repository_id: str | None = None
    technology: str | None = None
    framework: str | None = None
    category: str | None = None
    severity: str | None = None
    priority: str | None = None
    modernization_theme: str | None = None
    modernization_wave: str | None = None
    criticality: str | None = None
    production_scope: bool | None = None
    availability_status: str | None = None
    freshness_status: str | None = None
    offset: int = 0
    limit: int = 50
