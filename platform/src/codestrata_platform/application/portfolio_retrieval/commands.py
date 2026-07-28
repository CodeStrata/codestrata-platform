"""Portfolio retrieval application commands."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio_retrieval.identifiers import PortfolioRetrievalIndexId
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class BuildPortfolioRetrievalIndexCommand:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    portfolio_snapshot_id: PortfolioSnapshotId | None = None
    embedding_provider: str | None = None
    embedding_model: str | None = None
    embedding_dimension: int | None = None
    force: bool = False


@dataclass(frozen=True, slots=True)
class RebuildPortfolioRetrievalIndexCommand:
    index_id: PortfolioRetrievalIndexId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    embedding_provider: str | None = None
    embedding_model: str | None = None
    embedding_dimension: int | None = None
    force: bool = False


@dataclass(frozen=True, slots=True)
class FailPortfolioRetrievalIndexCommand:
    index_id: PortfolioRetrievalIndexId
    reason: str


@dataclass(frozen=True, slots=True)
class SupersedePortfolioRetrievalIndexCommand:
    index_id: PortfolioRetrievalIndexId


@dataclass(frozen=True, slots=True)
class ArchivePortfolioRetrievalIndexCommand:
    index_id: PortfolioRetrievalIndexId
