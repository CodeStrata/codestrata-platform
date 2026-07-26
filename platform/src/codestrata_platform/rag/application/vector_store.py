"""Application ports for the Repository Knowledge Layer vector store."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from codestrata_platform.rag.domain.vector import (
    IndexScope,
    VectorFilter,
    VectorQuery,
    VectorRecord,
    VectorSearchResult,
    VectorStoreCapabilities,
    VectorStoreHealth,
)


@runtime_checkable
class VectorStore(Protocol):
    """Provider-neutral vector store contract.

    Implementations may back dense similarity with in-memory structures,
    PostgreSQL/pgvector, or future adapters (Qdrant, OpenSearch, Pinecone).
    This phase defines the protocol and an in-memory test provider only.
    """

    def upsert(self, records: Sequence[VectorRecord]) -> None:
        """Insert or replace records by deterministic ``record_id``."""

    def search(self, query: VectorQuery) -> Sequence[VectorSearchResult]:
        """Return ranked dense similarity hits with stable tie-breaking."""

    def fetch_filtered(
        self,
        vector_filter: VectorFilter | None = None,
        *,
        limit: int,
        require_text: bool = True,
    ) -> Sequence[VectorRecord]:
        """Return filtered records for lexical / hybrid retrieval."""

    def delete_scope(self, scope: IndexScope) -> int:
        """Delete all records matching the isolation scope; return count."""

    def delete_ids(self, record_ids: Sequence[str]) -> int:
        """Delete records by id; return count of deleted records."""

    def health(self) -> VectorStoreHealth:
        """Return provider health for readiness checks."""

    def capabilities(self) -> VectorStoreCapabilities:
        """Advertise provider capabilities for future routing."""
