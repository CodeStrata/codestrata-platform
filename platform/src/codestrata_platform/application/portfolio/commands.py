"""Portfolio application commands."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio.lifecycle import RepositoryCriticality
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class CreatePortfolioCommand:
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    name: str
    description: str | None = None
    max_repositories: int | None = None


@dataclass(frozen=True, slots=True)
class UpdatePortfolioCommand:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    name: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AddRepositoryToPortfolioCommand:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    repository_id: RepositoryId
    criticality: RepositoryCriticality = RepositoryCriticality.UNSPECIFIED
    business_capability: str | None = None
    owner_reference: str | None = None
    lifecycle_status: str | None = None
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RemoveRepositoryFromPortfolioCommand:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    repository_id: RepositoryId


@dataclass(frozen=True, slots=True)
class ArchivePortfolioCommand:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId


@dataclass(frozen=True, slots=True)
class BuildPortfolioSnapshotCommand:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    aggregation_policy_version: str | None = None
    force_rebuild: bool = False


@dataclass(frozen=True, slots=True)
class RebuildPortfolioSnapshotCommand:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    aggregation_policy_version: str | None = None


@dataclass(frozen=True, slots=True)
class FailPortfolioSnapshotCommand:
    portfolio_snapshot_id: PortfolioSnapshotId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    reason: str


@dataclass(frozen=True, slots=True)
class SupersedePortfolioSnapshotCommand:
    portfolio_snapshot_id: PortfolioSnapshotId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
