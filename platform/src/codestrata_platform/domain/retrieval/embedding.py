"""Embedding provider port and related value objects."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.retrieval.identifiers import (
    EmbeddingDimension,
    EmbeddingModelId,
    EmbeddingProviderId,
    EmbeddingVector,
)


class EmbeddingProvider(Protocol):
    def provider_id(self) -> EmbeddingProviderId: ...

    def model_id(self) -> EmbeddingModelId: ...

    def dimension(self) -> EmbeddingDimension: ...

    def embed_text(self, text: str) -> EmbeddingVector: ...

    def embed_batch(self, texts: tuple[str, ...]) -> tuple[EmbeddingVector, ...]: ...

    def health_check(self) -> bool: ...
