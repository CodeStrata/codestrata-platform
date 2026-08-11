"""Deterministic embedding provider for tests and local validation.

Not a semantic production model. Same text always yields the same
L2-normalized fixed-dimension vector with no network access.
"""

from __future__ import annotations

import hashlib
import math
import random

from codestrata_platform.domain.retrieval.errors import RetrievalInvariantError
from codestrata_platform.domain.retrieval.identifiers import (
    DEFAULT_EMBEDDING_DIMENSION,
    EmbeddingDimension,
    EmbeddingModelId,
    EmbeddingProviderId,
    EmbeddingVector,
)

MAX_INPUT_CHARACTERS = 12_000
MAX_BATCH_SIZE = 64


class DeterministicEmbeddingProvider:
    """Hash-seeded fixed-dimension embeddings for tests and architecture validation."""

    PROVIDER_ID = "deterministic"
    DEFAULT_MODEL = "deterministic-test-embedding"

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        dimension: int = DEFAULT_EMBEDDING_DIMENSION,
        max_input_characters: int = MAX_INPUT_CHARACTERS,
        batch_size: int = MAX_BATCH_SIZE,
    ) -> None:
        if dimension < 1:
            raise ValueError("dimension must be positive")
        if max_input_characters < 1:
            raise ValueError("max_input_characters must be positive")
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        self._model = model.strip() or self.DEFAULT_MODEL
        self._dimension = EmbeddingDimension(dimension)
        self._max_input_characters = max_input_characters
        self._batch_size = batch_size

    def provider_id(self) -> EmbeddingProviderId:
        return EmbeddingProviderId(self.PROVIDER_ID)

    def model_id(self) -> EmbeddingModelId:
        return EmbeddingModelId(self._model)

    def dimension(self) -> EmbeddingDimension:
        return self._dimension

    def embed_text(self, text: str) -> EmbeddingVector:
        return self.embed_batch((text,))[0]

    def embed_batch(self, texts: tuple[str, ...]) -> tuple[EmbeddingVector, ...]:
        if len(texts) > self._batch_size:
            raise RetrievalInvariantError(
                f"embedding batch exceeds maximum of {self._batch_size}",
                reason_code="embedding_batch_too_large",
            )
        vectors: list[EmbeddingVector] = []
        for text in texts:
            compact = text.strip()
            if not compact:
                raise RetrievalInvariantError(
                    "embedding text must be non-blank",
                    reason_code="empty_embedding_text",
                )
            if len(compact) > self._max_input_characters:
                raise RetrievalInvariantError(
                    "embedding text exceeds maximum input size",
                    reason_code="embedding_input_too_large",
                )
            vectors.append(self._embed_bytes(compact.encode("utf-8")))
        return tuple(vectors)

    def health_check(self) -> bool:
        return True

    def _embed_bytes(self, data: bytes) -> EmbeddingVector:
        digest = hashlib.sha256(data).digest()
        seed = int.from_bytes(digest[:8], "big")
        rng = random.Random(seed)
        values = [rng.gauss(0.0, 1.0) for _ in range(self._dimension.value)]
        norm = math.sqrt(sum(value * value for value in values))
        if norm == 0.0:
            unit = [0.0] * self._dimension.value
            unit[0] = 1.0
            return EmbeddingVector(tuple(unit))
        return EmbeddingVector(tuple(value / norm for value in values))


__all__ = ["DeterministicEmbeddingProvider"]
