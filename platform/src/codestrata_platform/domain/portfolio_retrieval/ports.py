"""Ports for Portfolio Retrieval Index persistence, queries, and sourcing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio.lifecycle import RepositoryCriticality
from codestrata_platform.domain.portfolio.snapshot import PortfolioSnapshot
from codestrata_platform.domain.portfolio_retrieval.chunk import PortfolioRetrievalChunk
from codestrata_platform.domain.portfolio_retrieval.document import PortfolioRetrievalDocument
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    PortfolioRetrievalChunkId,
    PortfolioRetrievalDocumentId,
    PortfolioRetrievalIndexId,
)
from codestrata_platform.domain.portfolio_retrieval.index import PortfolioRetrievalIndex
from codestrata_platform.domain.portfolio_retrieval.query import PortfolioRetrievalQuery
from codestrata_platform.domain.portfolio_retrieval.result import PortfolioRetrievalSearchResult
from codestrata_platform.domain.portfolio_retrieval.scope import PortfolioRetrievalScope


class PortfolioRetrievalIndexRepository(Protocol):
    def get(self, index_id: PortfolioRetrievalIndexId) -> PortfolioRetrievalIndex | None: ...

    def save(self, index: PortfolioRetrievalIndex) -> None: ...

    def find_by_projection_key(
        self,
        projection_key: str,
    ) -> PortfolioRetrievalIndex | None: ...

    def list_by_portfolio(
        self,
        portfolio_id: PortfolioId,
    ) -> tuple[PortfolioRetrievalIndex, ...]: ...

    def get_latest_completed(
        self,
        portfolio_id: PortfolioId,
    ) -> PortfolioRetrievalIndex | None: ...

    def latest_index_version_for_portfolio(self, portfolio_id: PortfolioId) -> int: ...


class PortfolioRetrievalDocumentRepository(Protocol):
    def list_by_index(
        self,
        index_id: PortfolioRetrievalIndexId,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[PortfolioRetrievalDocument, ...]: ...

    def get(
        self,
        index_id: PortfolioRetrievalIndexId,
        document_id: PortfolioRetrievalDocumentId,
    ) -> PortfolioRetrievalDocument | None: ...


class PortfolioRetrievalChunkRepository(Protocol):
    def get(
        self,
        index_id: PortfolioRetrievalIndexId,
        chunk_id: PortfolioRetrievalChunkId,
    ) -> PortfolioRetrievalChunk | None: ...


class PortfolioRetrievalQueryRepository(Protocol):
    def search(
        self,
        index_id: PortfolioRetrievalIndexId,
        query: PortfolioRetrievalQuery,
        *,
        scope: PortfolioRetrievalScope,
        criticality_lookup: dict[str, RepositoryCriticality] | None = None,
    ) -> PortfolioRetrievalSearchResult: ...

    def statistics(self, index_id: PortfolioRetrievalIndexId) -> dict[str, int]: ...


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalSourceSnapshot:
    """Bounded read model of a completed PortfolioSnapshot and its inventories."""

    portfolio_snapshot: PortfolioSnapshot
    technology_inventory: tuple[object, ...]
    finding_inventory: tuple[object, ...]
    recommendation_inventory: tuple[object, ...]
    risk_summary: object | None
    modernization_summary: object | None
    coverage_summary: object | None
    dependency_signals: tuple[object, ...]


class PortfolioRetrievalSourceRepository(Protocol):
    """Bounded read access to a completed PortfolioSnapshot and its inventories."""

    def load_completed(
        self,
        portfolio_snapshot_id: PortfolioSnapshotId,
    ) -> PortfolioRetrievalSourceSnapshot | None: ...
