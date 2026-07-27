"""Retrieval chunk value objects."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.retrieval.document import (
    RetrievalSourceReference,
    sanitize_retrieval_text,
)
from codestrata_platform.domain.retrieval.identifiers import (
    ChunkChecksum,
    EmbeddingVector,
    RetrievalChunkId,
    RetrievalDocumentId,
    RetrievalIndexId,
)

HARD_MAX_TOKENS = 1000
DEFAULT_TARGET_MIN_TOKENS = 300
DEFAULT_TARGET_MAX_TOKENS = 600


def estimate_tokens(text: str) -> int:
    """Deterministic tokenizer approximation (~4 chars/token)."""

    compact = text.strip()
    if not compact:
        return 0
    return max(1, (len(compact) + 3) // 4)


@dataclass(frozen=True, slots=True)
class RetrievalChunk:
    chunk_id: RetrievalChunkId
    document_id: RetrievalDocumentId
    index_id: RetrievalIndexId
    ordinal: int
    text: str
    token_estimate: int
    checksum: ChunkChecksum
    embedding: EmbeddingVector | None = None
    source_references: tuple[RetrievalSourceReference, ...] = ()
    graph_node_ids: tuple[str, ...] = ()
    graph_edge_ids: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.ordinal < 0:
            raise InvalidValueError(
                "chunk ordinal must be >= 0",
                reason_code="invalid_chunk_ordinal",
            )
        text = sanitize_retrieval_text(self.text, max_length=HARD_MAX_TOKENS * 4)
        tokens = estimate_tokens(text)
        if tokens > HARD_MAX_TOKENS:
            raise InvalidValueError(
                f"chunk exceeds hard maximum of {HARD_MAX_TOKENS} tokens",
                reason_code="chunk_too_large",
            )
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "token_estimate", tokens)
        expected = ChunkChecksum.from_text(text)
        if self.checksum.value != expected.value:
            raise InvalidValueError(
                "chunk checksum does not match text",
                reason_code="chunk_checksum_mismatch",
            )
        if not self.source_references:
            raise InvalidValueError(
                "chunks require source references",
                reason_code="missing_chunk_source_references",
            )
