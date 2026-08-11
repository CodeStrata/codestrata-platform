"""Capability and health models for the PostgreSQL + pgvector provider."""

from __future__ import annotations

from typing import Any

from codestrata_platform.rag.domain.vector import VectorStoreCapabilities, VectorStoreHealth


class PgVectorCapabilities(VectorStoreCapabilities):
    """Capabilities advertisement for ``PgVectorStore``."""


class PgVectorStoreHealth(VectorStoreHealth):
    """Health probe result for ``PgVectorStore``."""


def build_pgvector_capabilities(
    *,
    dimension: int,
    schema: str,
    hnsw: bool,
) -> PgVectorCapabilities:
    return PgVectorCapabilities(
        provider_id="pgvector",
        supports_dense=True,
        supports_sparse=False,
        supports_hybrid=False,
        supports_metadata_filter=True,
        supports_tenant_isolation=True,
        supports_scoped_delete=True,
        max_dimensions=dimension,
        extra={
            "schema": schema,
            "hnsw": hnsw,
            "similarity": "cosine",
            "exact_cosine": False,
        },
    )


def build_pgvector_health(
    *,
    healthy: bool,
    message: str | None = None,
    detail: dict[str, Any] | None = None,
) -> PgVectorStoreHealth:
    return PgVectorStoreHealth(
        healthy=healthy,
        message=message,
        detail=dict(detail or {}),
    )
