"""Vector store factory from knowledge configuration (Phase 5.4.1)."""

from __future__ import annotations

from codestrata_platform.rag.application.vector_store import VectorStore
from codestrata.config.settings import KnowledgeSettings, KnowledgeVectorStoreSettings
from codestrata_platform.rag.vector_store.memory import create_in_memory_vector_store
from codestrata_platform.rag.vector_store.resolution import (
    ENV_DATABASE_URL,
    ENV_VECTOR_STORE_PROVIDER,
    SUPPORTED_VECTOR_STORE_PROVIDERS,
    VectorStoreConfigurationError,
    VectorStoreConnectivityError,
    VectorStoreExtensionError,
    missing_database_url_error,
    resolve_connect_timeout_seconds,
    resolve_database_url,
    resolve_embedding_dimension,
    resolve_vector_store_provider,
    resolve_vector_store_schema,
)
from codestrata.security.database_url import redact_database_url, sanitize_exception_message

__all__ = [
    "SUPPORTED_VECTOR_STORE_PROVIDERS",
    "VectorStoreConfigurationError",
    "VectorStoreConnectivityError",
    "VectorStoreExtensionError",
    "create_vector_store",
]


def create_vector_store(
    settings: KnowledgeSettings | KnowledgeVectorStoreSettings | None = None,
    *,
    connection_string: str | None = None,
    dimension: int | None = None,
) -> VectorStore:
    """Create a vector store for the resolved provider.

    Provider precedence: ``CODESTRATA_VECTOR_STORE_PROVIDER`` → codestrata.toml →
    ``memory``. Never silently falls back from ``pgvector`` to ``memory``.

    ``connection_string`` is an explicit programmatic override for tests.
    Prefer ``CODESTRATA_DATABASE_URL`` for normal operation.
    """

    provider = resolve_vector_store_provider(settings)
    if provider == "memory":
        return create_in_memory_vector_store()

    if provider != "pgvector":
        raise VectorStoreConfigurationError(
            f"unsupported knowledge.vector_store.provider: {provider!r}"
        )

    database_url = resolve_database_url(
        settings, programmatic_url=connection_string
    )
    if not database_url:
        raise missing_database_url_error()

    schema = resolve_vector_store_schema(settings)
    resolved_dimension = (
        dimension
        if dimension is not None
        else resolve_embedding_dimension(settings)
    )
    timeout = resolve_connect_timeout_seconds(settings)
    hnsw = True
    if isinstance(settings, KnowledgeSettings):
        hnsw = settings.vector_store.hnsw
    elif isinstance(settings, KnowledgeVectorStoreSettings):
        hnsw = settings.hnsw

    try:
        from codestrata_platform.rag.vector_store.pgvector import create_pgvector_store
    except ImportError as exc:
        raise VectorStoreConfigurationError(
            "provider='pgvector' requires the optional dependency group "
            "'pgvector' (pip install 'codestrata[pgvector]')"
        ) from exc

    try:
        store = create_pgvector_store(
            connection_string=database_url,
            schema=schema,
            dimension=resolved_dimension,
            hnsw=hnsw,
            connect_timeout_seconds=timeout,
        )
    except VectorStoreExtensionError:
        raise
    except VectorStoreConnectivityError:
        raise
    except VectorStoreConfigurationError:
        raise
    except Exception as exc:
        message = sanitize_exception_message(str(exc), database_url=database_url)
        redacted = redact_database_url(database_url)
        lowered = message.lower()
        if any(
            token in lowered
            for token in (
                "could not connect",
                "connection refused",
                "timeout",
                "timed out",
                "name or service not known",
                "no route to host",
                "operationalerror",
                "connection failed",
            )
        ):
            raise VectorStoreConnectivityError(
                "PostgreSQL is unreachable for provider='pgvector'. "
                f"Endpoint: {redacted}. "
                f"Verify Docker (`docker compose up -d postgres`) or "
                f"hosted connectivity, then confirm {ENV_DATABASE_URL} / "
                f"{ENV_VECTOR_STORE_PROVIDER}. Details: {message}"
            ) from None
        raise VectorStoreConfigurationError(
            f"failed to initialize PgVectorStore for endpoint {redacted}: {message}"
        ) from None

    return store
