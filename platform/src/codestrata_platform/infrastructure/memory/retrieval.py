"""In-memory Engineering Retrieval Index repository."""

from __future__ import annotations

from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.chunk import RetrievalChunk
from codestrata_platform.domain.retrieval.document import RetrievalDocument
from codestrata_platform.domain.retrieval.embedding import EmbeddingProvider
from codestrata_platform.domain.retrieval.identifiers import (
    RetrievalChunkId,
    RetrievalDocumentId,
    RetrievalIndexId,
)
from codestrata_platform.domain.retrieval.index import EngineeringRetrievalIndex
from codestrata_platform.domain.retrieval.lifecycle import RetrievalIndexStatus
from codestrata_platform.domain.retrieval.query import RetrievalQuery, RetrievalScope
from codestrata_platform.domain.retrieval.result import RetrievalSearchResult
from codestrata_platform.domain.retrieval.taxonomy import RetrievalMode
from codestrata_platform.infrastructure.retrieval.search import search_index


class InMemoryRetrievalRepository:
    """In-memory RetrievalIndexRepository + RetrievalQueryRepository adapter."""

    def __init__(self, *, embeddings: EmbeddingProvider | None = None) -> None:
        self._items: dict[str, EngineeringRetrievalIndex] = {}
        self._embeddings = embeddings

    def get(self, index_id: RetrievalIndexId) -> EngineeringRetrievalIndex | None:
        item = self._items.get(index_id.value)
        return item.snapshot() if item is not None else None

    def save(self, index: EngineeringRetrievalIndex) -> None:
        self._items[index.index_id.value] = index.snapshot()

    def find_by_projection_key(
        self,
        projection_key: str,
    ) -> EngineeringRetrievalIndex | None:
        key = projection_key.strip()
        for item in self._items.values():
            if item.projection_key.value == key:
                return item.snapshot()
        return None

    def list_by_repository(
        self,
        repository_id: RepositoryId,
    ) -> tuple[EngineeringRetrievalIndex, ...]:
        return tuple(
            item.snapshot()
            for item in sorted(
                (
                    item
                    for item in self._items.values()
                    if item.repository_id == repository_id
                ),
                key=lambda item: item.index_version.value,
            )
        )

    def get_latest_completed(
        self,
        repository_id: RepositoryId,
    ) -> EngineeringRetrievalIndex | None:
        completed = [
            item
            for item in self._items.values()
            if item.repository_id == repository_id
            and item.status is RetrievalIndexStatus.COMPLETED
        ]
        if not completed:
            return None
        latest = max(completed, key=lambda item: item.index_version.value)
        return latest.snapshot()

    def latest_index_version_for_repository(self, repository_id: RepositoryId) -> int:
        versions = [
            item.index_version.value
            for item in self._items.values()
            if item.repository_id == repository_id
        ]
        return max(versions) if versions else 0

    def list_documents_by_index(
        self,
        index_id: RetrievalIndexId,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[RetrievalDocument, ...]:
        index = self.get(index_id)
        if index is None:
            return ()
        return index.documents[offset : offset + limit]

    def get_document(
        self,
        index_id: RetrievalIndexId,
        document_id: RetrievalDocumentId,
    ) -> RetrievalDocument | None:
        index = self.get(index_id)
        if index is None:
            return None
        for item in index.documents:
            if item.document_id == document_id:
                return item
        return None

    def get_chunk(
        self,
        index_id: RetrievalIndexId,
        chunk_id: RetrievalChunkId,
    ) -> RetrievalChunk | None:
        index = self.get(index_id)
        if index is None:
            return None
        for item in index.chunks:
            if item.chunk_id == chunk_id:
                return item
        return None

    def search(
        self,
        index_id: RetrievalIndexId,
        query: RetrievalQuery,
        *,
        scope: RetrievalScope,
    ) -> RetrievalSearchResult:
        index = self.get(index_id)
        if index is None or index.status is not RetrievalIndexStatus.COMPLETED:
            return RetrievalSearchResult(hits=(), mode=query.mode.value, top_k=query.top_k)
        query_embedding = None
        if (
            query.mode in {RetrievalMode.VECTOR, RetrievalMode.HYBRID}
            and self._embeddings is not None
        ):
            query_embedding = self._embeddings.embed_text(query.query_text)
        return search_index(index, query, scope=scope, query_embedding=query_embedding)

    def statistics(self, index_id: RetrievalIndexId) -> dict[str, int]:
        index = self.get(index_id)
        if index is None:
            return {}
        return {
            "document_count": len(index.documents),
            "chunk_count": len(index.chunks),
            "embedded_chunk_count": sum(1 for item in index.chunks if item.embedding is not None),
        }
