"""Provider-neutral boundary for future external embedding providers.

Does not select a paid provider automatically. Instantiation requires explicit
configuration and does not load API keys into logs.
"""

from __future__ import annotations

from codestrata_platform.domain.retrieval.errors import RetrievalInvariantError
from codestrata_platform.domain.retrieval.identifiers import (
    EmbeddingDimension,
    EmbeddingModelId,
    EmbeddingProviderId,
    EmbeddingVector,
)


class ExternalEmbeddingProvider:
    """Stub boundary for OpenAI / Bedrock / other approved providers.

    Production wiring must inject a concrete adapter. This stub rejects calls so
    indexing cannot silently fall back to an unconfigured paid provider.
    """

    def __init__(
        self,
        *,
        provider_id: str,
        model_id: str,
        dimension: int,
    ) -> None:
        self._provider_id = EmbeddingProviderId(provider_id)
        self._model_id = EmbeddingModelId(model_id)
        self._dimension = EmbeddingDimension(dimension)

    def provider_id(self) -> EmbeddingProviderId:
        return self._provider_id

    def model_id(self) -> EmbeddingModelId:
        return self._model_id

    def dimension(self) -> EmbeddingDimension:
        return self._dimension

    def embed_text(self, text: str) -> EmbeddingVector:
        raise RetrievalInvariantError(
            "External embedding provider is not configured for this environment",
            reason_code="external_embedding_not_configured",
        )

    def embed_batch(self, texts: tuple[str, ...]) -> tuple[EmbeddingVector, ...]:
        raise RetrievalInvariantError(
            "External embedding provider is not configured for this environment",
            reason_code="external_embedding_not_configured",
        )

    def health_check(self) -> bool:
        return False


__all__ = ["ExternalEmbeddingProvider"]
