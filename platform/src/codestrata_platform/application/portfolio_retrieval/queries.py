"""Portfolio retrieval application queries."""

from __future__ import annotations

from dataclasses import dataclass, field

from codestrata_platform.application.portfolio_retrieval.policies import (
    DEFAULT_PORTFOLIO_CONTEXT_MAX_REPOSITORIES,
    DEFAULT_PORTFOLIO_CONTEXT_MAX_TOKENS,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    PortfolioRetrievalChunkId,
    PortfolioRetrievalDocumentId,
    PortfolioRetrievalIndexId,
)
from codestrata_platform.domain.portfolio_retrieval.lifecycle import RepositoryBalanceMode
from codestrata_platform.domain.portfolio_retrieval.query import PortfolioRetrievalQuery
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType
from codestrata_platform.domain.retrieval.taxonomy import RetrievalMode
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class GetPortfolioRetrievalIndexQuery:
    index_id: PortfolioRetrievalIndexId
    organization_id: OrganizationId
    workspace_id: WorkspaceId


@dataclass(frozen=True, slots=True)
class GetLatestPortfolioRetrievalIndexQuery:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId


@dataclass(frozen=True, slots=True)
class ListPortfolioRetrievalIndexesQuery:
    portfolio_id: PortfolioId
    organization_id: OrganizationId
    workspace_id: WorkspaceId


@dataclass(frozen=True, slots=True)
class SearchPortfolioRetrievalIndexQuery:
    index_id: PortfolioRetrievalIndexId
    query: PortfolioRetrievalQuery
    organization_id: OrganizationId
    workspace_id: WorkspaceId


@dataclass(frozen=True, slots=True)
class GetPortfolioRetrievalDocumentQuery:
    index_id: PortfolioRetrievalIndexId
    document_id: PortfolioRetrievalDocumentId


@dataclass(frozen=True, slots=True)
class GetPortfolioRetrievalChunkQuery:
    index_id: PortfolioRetrievalIndexId
    chunk_id: PortfolioRetrievalChunkId


@dataclass(frozen=True, slots=True)
class GetPortfolioRetrievalIndexStatisticsQuery:
    index_id: PortfolioRetrievalIndexId


@dataclass(frozen=True, slots=True)
class ListPortfolioRetrievalDocumentsQuery:
    index_id: PortfolioRetrievalIndexId
    offset: int = 0
    limit: int = 100
    content_types: tuple[PortfolioRetrievalContentType, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class BuildPortfolioRetrievalContextQuery:
    index_id: PortfolioRetrievalIndexId
    query_text: str
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    mode: RetrievalMode = RetrievalMode.HYBRID
    top_k: int = 10
    max_tokens: int = DEFAULT_PORTFOLIO_CONTEXT_MAX_TOKENS
    max_repositories: int = DEFAULT_PORTFOLIO_CONTEXT_MAX_REPOSITORIES
    content_types: tuple[PortfolioRetrievalContentType, ...] = ()
    repository_balance_mode: RepositoryBalanceMode = RepositoryBalanceMode.NONE
    repository_ids: tuple[str, ...] = ()
    exclude_repository_ids: tuple[str, ...] = ()
