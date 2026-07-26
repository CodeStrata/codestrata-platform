"""Provider-neutral embedding provider port (Phase 5.3)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from aimf.domain.knowledge.embedding import (
    EmbeddingBatchResult,
    EmbeddingModelIdentity,
    EmbeddingProviderCapabilities,
    EmbeddingProviderHealth,
    EmbeddingRequest,
    EmbeddingResult,
)


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Provider-neutral embedding contract.

    Implementations must not depend on vector-store backends. Only the
    deterministic test provider is implemented in Phase 5.3.
    """

    def embed_text(self, text: str, *, request_id: str = "single") -> EmbeddingResult:
        """Embed one text string."""

    def embed_batch(self, requests: Sequence[EmbeddingRequest]) -> EmbeddingBatchResult:
        """Embed many texts with deterministic result ordering."""

    def health(self) -> EmbeddingProviderHealth:
        """Return provider readiness."""

    def capabilities(self) -> EmbeddingProviderCapabilities:
        """Advertise provider capabilities."""

    def model_identity(self) -> EmbeddingModelIdentity:
        """Return stable provider/model/version/dimension identity."""
