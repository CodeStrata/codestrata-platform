"""Deterministic test embedding provider (Phase 5.3).

Not a semantic production model. Same text always yields the same L2-normalized
fixed-dimension vector with no network or LLM access.
"""

from __future__ import annotations

import hashlib
import math
import random
from collections.abc import Sequence
from typing import Any

from codestrata_platform.rag.domain.embedding import (
    EmbeddingBatchResult,
    EmbeddingDiagnostic,
    EmbeddingModelIdentity,
    EmbeddingProviderCapabilities,
    EmbeddingProviderHealth,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingUsage,
)


class DeterministicEmbeddingProvider:
    """Hash-seeded fixed-dimension embeddings for tests and dogfood only."""

    PROVIDER_ID = "deterministic"
    DEFAULT_MODEL = "deterministic-test-embedding"
    DEFAULT_MODEL_VERSION = "1.0.0"
    DEFAULT_DIMENSION = 384

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        model_version: str = DEFAULT_MODEL_VERSION,
        dimension: int = DEFAULT_DIMENSION,
        max_input_characters: int = 12_000,
        batch_size: int = 32,
    ) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        if max_input_characters <= 0:
            raise ValueError("max_input_characters must be positive")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self._model = model.strip()
        self._model_version = model_version.strip()
        self._dimension = dimension
        self._max_input_characters = max_input_characters
        self._batch_size = batch_size

    def model_identity(self) -> EmbeddingModelIdentity:
        return EmbeddingModelIdentity(
            provider_id=self.PROVIDER_ID,
            model=self._model,
            model_version=self._model_version,
            dimension=self._dimension,
        )

    def capabilities(self) -> EmbeddingProviderCapabilities:
        return EmbeddingProviderCapabilities(
            provider_id=self.PROVIDER_ID,
            supports_batch=True,
            max_batch_size=self._batch_size,
            max_input_characters=self._max_input_characters,
            dimension=self._dimension,
            is_deterministic=True,
            is_production_semantic=False,
            extra={"purpose": "test_and_pipeline_validation_only"},
        )

    def health(self) -> EmbeddingProviderHealth:
        return EmbeddingProviderHealth(
            healthy=True,
            message="deterministic embedding provider ready",
            detail={"dimension": self._dimension},
        )

    def embed_text(self, text: str, *, request_id: str = "single") -> EmbeddingResult:
        request = EmbeddingRequest(request_id=request_id, text=text)
        batch = self.embed_batch([request])
        if batch.failed_request_ids:
            diagnostic = next(
                (item for item in batch.diagnostics if item.request_id == request_id),
                None,
            )
            message = diagnostic.message if diagnostic else "embedding failed"
            raise ValueError(message)
        return batch.results[0]

    def embed_batch(self, requests: Sequence[EmbeddingRequest]) -> EmbeddingBatchResult:
        results: list[EmbeddingResult] = []
        failed: list[str] = []
        diagnostics: list[EmbeddingDiagnostic] = []
        identity = self.model_identity()

        for request in requests:
            text = request.text
            if not text.strip():
                failed.append(request.request_id)
                diagnostics.append(
                    EmbeddingDiagnostic(
                        code="empty_input",
                        message="embedding text must not be blank",
                        request_id=request.request_id,
                        severity="warning",
                    )
                )
                continue
            if len(text) > self._max_input_characters:
                failed.append(request.request_id)
                diagnostics.append(
                    EmbeddingDiagnostic(
                        code="input_too_large",
                        message=(
                            f"input length {len(text)} exceeds max_input_characters "
                            f"{self._max_input_characters}"
                        ),
                        request_id=request.request_id,
                        severity="warning",
                    )
                )
                continue
            embedding = self._embed_bytes(text.encode("utf-8"))
            results.append(
                EmbeddingResult(
                    request_id=request.request_id,
                    embedding=embedding,
                    dimension=self._dimension,
                    model_identity=identity,
                    usage=EmbeddingUsage(input_characters=len(text)),
                )
            )
        return EmbeddingBatchResult(
            results=tuple(results),
            failed_request_ids=tuple(failed),
            diagnostics=tuple(diagnostics),
        )

    def _embed_bytes(self, data: bytes) -> tuple[float, ...]:
        digest = hashlib.sha256(data).digest()
        seed = int.from_bytes(digest[:8], "big")
        rng = random.Random(seed)
        values = [rng.gauss(0.0, 1.0) for _ in range(self._dimension)]
        norm = math.sqrt(sum(value * value for value in values))
        if norm == 0.0:
            # Extremely unlikely; fall back to a unit vector on the first axis.
            unit = [0.0] * self._dimension
            unit[0] = 1.0
            return tuple(unit)
        return tuple(value / norm for value in values)


def create_deterministic_embedding_provider(
    *,
    model: str = DeterministicEmbeddingProvider.DEFAULT_MODEL,
    model_version: str = DeterministicEmbeddingProvider.DEFAULT_MODEL_VERSION,
    dimension: int = DeterministicEmbeddingProvider.DEFAULT_DIMENSION,
    max_input_characters: int = 12_000,
    batch_size: int = 32,
    embedding_settings: Any | None = None,
    **_: Any,
) -> DeterministicEmbeddingProvider:
    """Factory for the Phase 5.3 deterministic embedding provider."""

    if embedding_settings is not None:
        model = getattr(embedding_settings, "model", model) or model
        model_version = (
            getattr(embedding_settings, "model_version", model_version) or model_version
        )
        dimension = int(getattr(embedding_settings, "dimension", dimension) or dimension)
        max_input_characters = int(
            getattr(embedding_settings, "max_input_characters", max_input_characters)
            or max_input_characters
        )
        batch_size = int(getattr(embedding_settings, "batch_size", batch_size) or batch_size)
    return DeterministicEmbeddingProvider(
        model=model,
        model_version=model_version,
        dimension=dimension,
        max_input_characters=max_input_characters,
        batch_size=batch_size,
    )
