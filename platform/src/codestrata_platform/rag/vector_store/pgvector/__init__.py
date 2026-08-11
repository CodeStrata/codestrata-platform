"""PostgreSQL + pgvector vector store provider (Phase 5.4)."""

from codestrata_platform.rag.vector_store.pgvector.capabilities import (
    PgVectorCapabilities,
    PgVectorStoreHealth,
)
from codestrata_platform.rag.vector_store.pgvector.store import (
    PgVectorStore,
    create_pgvector_store,
)

__all__ = [
    "PgVectorCapabilities",
    "PgVectorStore",
    "PgVectorStoreHealth",
    "create_pgvector_store",
]
