"""Retrieval application queries."""

from __future__ import annotations

from dataclasses import dataclass, field

from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.identifiers import (
    RetrievalChunkId,
    RetrievalDocumentId,
    RetrievalIndexId,
)
from codestrata_platform.domain.retrieval.query import RetrievalQuery
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType, RetrievalMode


@dataclass(frozen=True, slots=True)
class GetRetrievalIndexQuery:
    index_id: RetrievalIndexId


@dataclass(frozen=True, slots=True)
class GetLatestRepositoryRetrievalIndexQuery:
    repository_id: RepositoryId


@dataclass(frozen=True, slots=True)
class ListRepositoryRetrievalIndexesQuery:
    repository_id: RepositoryId


@dataclass(frozen=True, slots=True)
class SearchRetrievalIndexQuery:
    index_id: RetrievalIndexId
    query: RetrievalQuery


@dataclass(frozen=True, slots=True)
class AssembleRetrievalContextQuery:
    index_id: RetrievalIndexId
    query_text: str
    mode: RetrievalMode = RetrievalMode.HYBRID
    top_k: int = 10
    max_tokens: int = 6000
    content_types: tuple[RetrievalContentType, ...] = ()


@dataclass(frozen=True, slots=True)
class GetRetrievalDocumentQuery:
    index_id: RetrievalIndexId
    document_id: RetrievalDocumentId


@dataclass(frozen=True, slots=True)
class GetRetrievalChunkQuery:
    index_id: RetrievalIndexId
    chunk_id: RetrievalChunkId


@dataclass(frozen=True, slots=True)
class GetRetrievalIndexStatisticsQuery:
    index_id: RetrievalIndexId


@dataclass(frozen=True, slots=True)
class ListRetrievalDocumentsQuery:
    index_id: RetrievalIndexId
    offset: int = 0
    limit: int = 100
    content_types: tuple[RetrievalContentType, ...] = field(default_factory=tuple)
