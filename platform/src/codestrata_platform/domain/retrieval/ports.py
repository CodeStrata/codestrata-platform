"""Ports for Engineering Retrieval Index persistence and queries."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.chunk import RetrievalChunk
from codestrata_platform.domain.retrieval.document import RetrievalDocument
from codestrata_platform.domain.retrieval.identifiers import (
    RetrievalChunkId,
    RetrievalDocumentId,
    RetrievalIndexId,
)
from codestrata_platform.domain.retrieval.index import EngineeringRetrievalIndex
from codestrata_platform.domain.retrieval.query import RetrievalQuery, RetrievalScope
from codestrata_platform.domain.retrieval.result import RetrievalSearchResult


class RetrievalIndexRepository(Protocol):
    def get(self, index_id: RetrievalIndexId) -> EngineeringRetrievalIndex | None: ...

    def save(self, index: EngineeringRetrievalIndex) -> None: ...

    def find_by_projection_key(
        self,
        projection_key: str,
    ) -> EngineeringRetrievalIndex | None: ...

    def list_by_repository(
        self,
        repository_id: RepositoryId,
    ) -> tuple[EngineeringRetrievalIndex, ...]: ...

    def get_latest_completed(
        self,
        repository_id: RepositoryId,
    ) -> EngineeringRetrievalIndex | None: ...

    def latest_index_version_for_repository(self, repository_id: RepositoryId) -> int: ...


class RetrievalDocumentRepository(Protocol):
    def list_by_index(
        self,
        index_id: RetrievalIndexId,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[RetrievalDocument, ...]: ...

    def get(
        self,
        index_id: RetrievalIndexId,
        document_id: RetrievalDocumentId,
    ) -> RetrievalDocument | None: ...


class RetrievalChunkRepository(Protocol):
    def get(
        self,
        index_id: RetrievalIndexId,
        chunk_id: RetrievalChunkId,
    ) -> RetrievalChunk | None: ...


class RetrievalQueryRepository(Protocol):
    def search(
        self,
        index_id: RetrievalIndexId,
        query: RetrievalQuery,
        *,
        scope: RetrievalScope,
    ) -> RetrievalSearchResult: ...

    def statistics(self, index_id: RetrievalIndexId) -> dict[str, int]: ...
