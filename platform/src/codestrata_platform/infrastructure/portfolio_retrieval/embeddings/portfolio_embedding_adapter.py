"""Portfolio-scoped embedding provider adapter.

Thin wrapper around the canonical Engineering Retrieval embedding provider
factory. Portfolio-specific environment overrides
(``CODESTRATA_PORTFOLIO_EMBEDDING_*``) are honored when set; otherwise the
shared Engineering Retrieval configuration (``CODESTRATA_EMBEDDING_*``) is
reused so a single embedding provider can serve both retrieval domains by
default.
"""

from __future__ import annotations

from codestrata_platform.application.portfolio_retrieval.policies import (
    configured_portfolio_embedding_dimension,
    configured_portfolio_embedding_model,
    configured_portfolio_embedding_provider,
)
from codestrata_platform.domain.retrieval.embedding import EmbeddingProvider
from codestrata_platform.infrastructure.retrieval.embeddings.deterministic_embedding_provider import (
    DeterministicEmbeddingProvider,
)
from codestrata_platform.infrastructure.retrieval.embeddings.external_embedding_provider import (
    ExternalEmbeddingProvider,
)


def create_portfolio_embedding_provider() -> EmbeddingProvider:
    """Create the configured portfolio embedding provider without silent paid fallback."""

    provider = configured_portfolio_embedding_provider()
    model = configured_portfolio_embedding_model()
    dimension = configured_portfolio_embedding_dimension()
    if provider == DeterministicEmbeddingProvider.PROVIDER_ID:
        return DeterministicEmbeddingProvider(model=model, dimension=dimension)
    return ExternalEmbeddingProvider(
        provider_id=provider,
        model_id=model,
        dimension=dimension,
    )


__all__ = ["create_portfolio_embedding_provider"]
