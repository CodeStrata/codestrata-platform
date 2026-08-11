"""In-memory vector store for deterministic tests (no external dependencies)."""

from __future__ import annotations

import math
from collections.abc import Sequence

from codestrata_platform.rag.application.vector_store import VectorStore
from codestrata_platform.rag.domain.vector import (
    IndexScope,
    VectorFilter,
    VectorQuery,
    VectorRecord,
    VectorSearchResult,
    VectorStoreCapabilities,
    VectorStoreHealth,
)


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Exact cosine similarity; zero-norm vectors score ``0.0``."""

    if len(left) != len(right):
        raise ValueError("embedding dimensions must match")
    if not left:
        return 0.0
    dot = 0.0
    left_norm_sq = 0.0
    right_norm_sq = 0.0
    for a, b in zip(left, right, strict=True):
        dot += a * b
        left_norm_sq += a * a
        right_norm_sq += b * b
    if left_norm_sq == 0.0 or right_norm_sq == 0.0:
        return 0.0
    return dot / (math.sqrt(left_norm_sq) * math.sqrt(right_norm_sq))


class InMemoryVectorStore:
    """Deterministic dense vector store for foundation tests.

    * Exact cosine similarity
    * Metadata filtering via ``VectorFilter``
    * Tenant / repository / scan isolation via metadata + ``IndexScope``
    * Stable ordering: score descending, then ``record_id`` ascending
    * Duplicate upserts replace by ``record_id``
    """

    def __init__(self) -> None:
        self._records: dict[str, VectorRecord] = {}

    def upsert(self, records: Sequence[VectorRecord]) -> None:
        for record in records:
            self._records[record.record_id] = record

    def search(self, query: VectorQuery) -> Sequence[VectorSearchResult]:
        hits: list[VectorSearchResult] = []
        for record in self._records.values():
            if query.filter is not None and not query.filter.matches(record.metadata):
                continue
            if len(record.embedding) != len(query.embedding):
                continue
            score = cosine_similarity(query.embedding, record.embedding)
            hits.append(
                VectorSearchResult(
                    record_id=record.record_id,
                    score=score,
                    record=record,
                )
            )
        hits.sort(key=lambda item: (-item.score, item.record_id))
        return tuple(hits[: query.top_k])

    def fetch_filtered(
        self,
        vector_filter: VectorFilter | None = None,
        *,
        limit: int,
        require_text: bool = True,
    ) -> Sequence[VectorRecord]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        matched: list[VectorRecord] = []
        for record in sorted(self._records.values(), key=lambda item: item.record_id):
            if vector_filter is not None and not vector_filter.matches(record.metadata):
                continue
            if require_text and not (record.text and record.text.strip()):
                continue
            matched.append(record)
            if len(matched) >= limit:
                break
        return tuple(matched)

    def delete_scope(self, scope: IndexScope) -> int:
        to_delete = [
            record_id
            for record_id, record in self._records.items()
            if scope.matches(record.metadata)
        ]
        for record_id in to_delete:
            del self._records[record_id]
        return len(to_delete)

    def delete_ids(self, record_ids: Sequence[str]) -> int:
        deleted = 0
        for record_id in record_ids:
            if record_id in self._records:
                del self._records[record_id]
                deleted += 1
        return deleted

    def health(self) -> VectorStoreHealth:
        return VectorStoreHealth(
            healthy=True,
            message="in-memory vector store ready",
            detail={
                "record_count": len(self._records),
                "persistent": False,
                "connectivity": True,
            },
        )

    def capabilities(self) -> VectorStoreCapabilities:
        return VectorStoreCapabilities(
            provider_id="memory",
            supports_dense=True,
            supports_sparse=False,
            supports_hybrid=False,
            supports_metadata_filter=True,
            supports_tenant_isolation=True,
            supports_scoped_delete=True,
            max_dimensions=None,
            extra={"exact_cosine": True},
        )

    def __len__(self) -> int:
        return len(self._records)


def create_in_memory_vector_store() -> VectorStore:
    """Factory for the memory provider (Phase 5.1 default)."""

    return InMemoryVectorStore()
