"""Embedding provider package."""

from __future__ import annotations

from codestrata_platform.application.retrieval.policies import (
    configured_embedding_dimension,
    configured_embedding_model,
    configured_embedding_provider,
)
from codestrata_platform.domain.retrieval.embedding import EmbeddingProvider
from codestrata_platform.infrastructure.retrieval.embeddings.deterministic_embedding_provider import (
    DeterministicEmbeddingProvider,
)
from codestrata_platform.infrastructure.retrieval.embeddings.external_embedding_provider import (
    ExternalEmbeddingProvider,
)


def create_embedding_provider() -> EmbeddingProvider:
    """Create the configured embedding provider without silent paid fallback."""

    provider = configured_embedding_provider()
    model = configured_embedding_model()
    dimension = configured_embedding_dimension()
    if provider == DeterministicEmbeddingProvider.PROVIDER_ID:
        return DeterministicEmbeddingProvider(model=model, dimension=dimension)
    return ExternalEmbeddingProvider(
        provider_id=provider,
        model_id=model,
        dimension=dimension,
    )


__all__ = [
    "DeterministicEmbeddingProvider",
    "ExternalEmbeddingProvider",
    "create_embedding_provider",
]
