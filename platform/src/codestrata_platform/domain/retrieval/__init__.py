"""Canonical Engineering Retrieval domain package."""

from __future__ import annotations

from codestrata_platform.domain.retrieval.chunk import RetrievalChunk, estimate_tokens
from codestrata_platform.domain.retrieval.document import (
    RetrievalDocument,
    RetrievalSourceReference,
    sanitize_retrieval_text,
)
from codestrata_platform.domain.retrieval.embedding import EmbeddingProvider
from codestrata_platform.domain.retrieval.errors import (
    RetrievalError,
    RetrievalInvariantError,
    RetrievalLimitError,
)
from codestrata_platform.domain.retrieval.identifiers import (
    DEFAULT_EMBEDDING_DIMENSION,
    ChunkChecksum,
    EmbeddingDimension,
    EmbeddingModelId,
    EmbeddingProviderId,
    EmbeddingVector,
    RetrievalChunkId,
    RetrievalDocumentId,
    RetrievalIndexId,
    RetrievalProjectionKey,
    RetrievalResultId,
    deterministic_chunk_id,
    deterministic_document_id,
    deterministic_index_id,
)
from codestrata_platform.domain.retrieval.index import EngineeringRetrievalIndex
from codestrata_platform.domain.retrieval.lifecycle import (
    RetrievalIndexStatus,
    RetrievalIndexVersion,
)
from codestrata_platform.domain.retrieval.ports import (
    RetrievalChunkRepository,
    RetrievalDocumentRepository,
    RetrievalIndexRepository,
    RetrievalQueryRepository,
)
from codestrata_platform.domain.retrieval.query import (
    RetrievalQuery,
    RetrievalScope,
    RetrievalScore,
)
from codestrata_platform.domain.retrieval.result import RetrievalHit, RetrievalSearchResult
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType, RetrievalMode

__all__ = [
    "DEFAULT_EMBEDDING_DIMENSION",
    "ChunkChecksum",
    "EmbeddingDimension",
    "EmbeddingModelId",
    "EmbeddingProvider",
    "EmbeddingProviderId",
    "EmbeddingVector",
    "EngineeringRetrievalIndex",
    "RetrievalChunk",
    "RetrievalChunkId",
    "RetrievalChunkRepository",
    "RetrievalContentType",
    "RetrievalDocument",
    "RetrievalDocumentId",
    "RetrievalDocumentRepository",
    "RetrievalError",
    "RetrievalHit",
    "RetrievalIndexId",
    "RetrievalIndexRepository",
    "RetrievalIndexStatus",
    "RetrievalIndexVersion",
    "RetrievalInvariantError",
    "RetrievalLimitError",
    "RetrievalMode",
    "RetrievalProjectionKey",
    "RetrievalQuery",
    "RetrievalQueryRepository",
    "RetrievalResultId",
    "RetrievalScope",
    "RetrievalScore",
    "RetrievalSearchResult",
    "RetrievalSourceReference",
    "deterministic_chunk_id",
    "deterministic_document_id",
    "deterministic_index_id",
    "estimate_tokens",
    "sanitize_retrieval_text",
]
