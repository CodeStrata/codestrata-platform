"""Retrieval result value objects."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.retrieval.document import RetrievalSourceReference
from codestrata_platform.domain.retrieval.identifiers import (
    RetrievalChunkId,
    RetrievalDocumentId,
    RetrievalResultId,
)
from codestrata_platform.domain.retrieval.query import RetrievalScore
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType


@dataclass(frozen=True, slots=True)
class RetrievalHit:
    result_id: RetrievalResultId
    chunk_id: RetrievalChunkId
    document_id: RetrievalDocumentId
    content_type: RetrievalContentType
    canonical_type: str
    canonical_id: str
    title: str
    text: str
    score: RetrievalScore
    source_references: tuple[RetrievalSourceReference, ...] = ()
    graph_node_ids: tuple[str, ...] = ()
    graph_edge_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RetrievalSearchResult:
    hits: tuple[RetrievalHit, ...]
    mode: str
    top_k: int
