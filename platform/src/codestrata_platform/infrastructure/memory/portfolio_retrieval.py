"""In-memory Portfolio Retrieval Index repository."""

from __future__ import annotations

from codestrata_platform.domain.portfolio.identifiers import PortfolioId
from codestrata_platform.domain.portfolio.lifecycle import RepositoryCriticality
from codestrata_platform.domain.portfolio_retrieval.chunk import PortfolioRetrievalChunk
from codestrata_platform.domain.portfolio_retrieval.document import PortfolioRetrievalDocument
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    PortfolioRetrievalChunkId,
    PortfolioRetrievalDocumentId,
    PortfolioRetrievalIndexId,
)
from codestrata_platform.domain.portfolio_retrieval.index import PortfolioRetrievalIndex
from codestrata_platform.domain.portfolio_retrieval.lifecycle import PortfolioRetrievalIndexStatus
from codestrata_platform.domain.portfolio_retrieval.query import PortfolioRetrievalQuery
from codestrata_platform.domain.portfolio_retrieval.result import PortfolioRetrievalSearchResult
from codestrata_platform.domain.portfolio_retrieval.scope import PortfolioRetrievalScope
from codestrata_platform.domain.retrieval.embedding import EmbeddingProvider
from codestrata_platform.domain.retrieval.taxonomy import RetrievalMode
from codestrata_platform.infrastructure.portfolio_retrieval.search import search_portfolio_index


class InMemoryPortfolioRetrievalRepository:
    """In-memory PortfolioRetrievalIndexRepository + PortfolioRetrievalQueryRepository adapter."""

    def __init__(self, *, embeddings: EmbeddingProvider | None = None) -> None:
        self._items: dict[str, PortfolioRetrievalIndex] = {}
        self._embeddings = embeddings

    def get(self, index_id: PortfolioRetrievalIndexId) -> PortfolioRetrievalIndex | None:
        item = self._items.get(index_id.value)
        return item.snapshot() if item is not None else None

    def save(self, index: PortfolioRetrievalIndex) -> None:
        self._items[index.index_id.value] = index.snapshot()

    def find_by_projection_key(
        self,
        projection_key: str,
    ) -> PortfolioRetrievalIndex | None:
        key = projection_key.strip()
        for item in self._items.values():
            if item.projection_key.value == key:
                return item.snapshot()
        return None

    def list_by_portfolio(
        self,
        portfolio_id: PortfolioId,
    ) -> tuple[PortfolioRetrievalIndex, ...]:
        return tuple(
            item.snapshot()
            for item in sorted(
                (
                    item
                    for item in self._items.values()
                    if item.portfolio_id == portfolio_id
                ),
                key=lambda item: item.index_version.value,
            )
        )

    def get_latest_completed(
        self,
        portfolio_id: PortfolioId,
    ) -> PortfolioRetrievalIndex | None:
        completed = [
            item
            for item in self._items.values()
            if item.portfolio_id == portfolio_id
            and item.status is PortfolioRetrievalIndexStatus.COMPLETED
        ]
        if not completed:
            return None
        latest = max(completed, key=lambda item: item.index_version.value)
        return latest.snapshot()

    def latest_index_version_for_portfolio(self, portfolio_id: PortfolioId) -> int:
        versions = [
            item.index_version.value
            for item in self._items.values()
            if item.portfolio_id == portfolio_id
        ]
        return max(versions) if versions else 0

    def list_documents_by_index(
        self,
        index_id: PortfolioRetrievalIndexId,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[PortfolioRetrievalDocument, ...]:
        index = self.get(index_id)
        if index is None:
            return ()
        return index.documents[offset : offset + limit]

    def get_document(
        self,
        index_id: PortfolioRetrievalIndexId,
        document_id: PortfolioRetrievalDocumentId,
    ) -> PortfolioRetrievalDocument | None:
        index = self.get(index_id)
        if index is None:
            return None
        for item in index.documents:
            if item.document_id == document_id:
                return item
        return None

    def get_chunk(
        self,
        index_id: PortfolioRetrievalIndexId,
        chunk_id: PortfolioRetrievalChunkId,
    ) -> PortfolioRetrievalChunk | None:
        index = self.get(index_id)
        if index is None:
            return None
        for item in index.chunks:
            if item.chunk_id == chunk_id:
                return item
        return None

    def search(
        self,
        index_id: PortfolioRetrievalIndexId,
        query: PortfolioRetrievalQuery,
        *,
        scope: PortfolioRetrievalScope,
        criticality_lookup: dict[str, RepositoryCriticality] | None = None,
    ) -> PortfolioRetrievalSearchResult:
        index = self.get(index_id)
        if index is None or index.status is not PortfolioRetrievalIndexStatus.COMPLETED:
            return PortfolioRetrievalSearchResult(hits=(), mode=query.mode.value, top_k=query.top_k)
        query_embedding = None
        if (
            query.mode in {RetrievalMode.VECTOR, RetrievalMode.HYBRID}
            and self._embeddings is not None
        ):
            query_embedding = self._embeddings.embed_text(query.query_text)
        return search_portfolio_index(
            index,
            query,
            scope=scope,
            query_embedding=query_embedding,
            criticality_lookup=criticality_lookup,
        )

    def statistics(self, index_id: PortfolioRetrievalIndexId) -> dict[str, int]:
        index = self.get(index_id)
        if index is None:
            return {}
        return {
            "document_count": len(index.documents),
            "chunk_count": len(index.chunks),
            "embedded_chunk_count": sum(1 for item in index.chunks if item.embedding is not None),
        }
