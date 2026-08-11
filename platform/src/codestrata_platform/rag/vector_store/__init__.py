"""Vector store infrastructure adapters.

Phase 5.4 adds PostgreSQL + pgvector alongside the in-memory provider.
Phase 5.4.1 hardens environment configuration, secrets, and Docker ops.
"""

from codestrata_platform.rag.vector_store.factory import (
    SUPPORTED_VECTOR_STORE_PROVIDERS,
    VectorStoreConfigurationError,
    VectorStoreConnectivityError,
    VectorStoreExtensionError,
    create_vector_store,
)
from codestrata_platform.rag.vector_store.memory import (
    InMemoryVectorStore,
    cosine_similarity,
    create_in_memory_vector_store,
)

__all__ = [
    "SUPPORTED_VECTOR_STORE_PROVIDERS",
    "InMemoryVectorStore",
    "VectorStoreConfigurationError",
    "VectorStoreConnectivityError",
    "VectorStoreExtensionError",
    "cosine_similarity",
    "create_in_memory_vector_store",
    "create_vector_store",
]
