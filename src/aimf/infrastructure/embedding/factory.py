"""Embedding provider factory (Phase 5.3 / 5.8).

Resolves providers through ``AIProviderRegistry``. Prefer
``[ai].embedding_provider`` when ``AimfSettings`` is supplied; otherwise use
``knowledge.embedding.provider``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aimf.application.knowledge.embedding.protocol import EmbeddingProvider
from aimf.config.settings import AimfSettings, KnowledgeEmbeddingSettings

if TYPE_CHECKING:
    from aimf.ai.providers.registry import AIProviderRegistry

SUPPORTED_EMBEDDING_PROVIDERS = frozenset(
    {"deterministic", "bedrock", "openai", "local_sentence_transformer"}
)

RESERVED_UNIMPLEMENTED = frozenset({"local_sentence_transformer"})


class EmbeddingProviderConfigurationError(ValueError):
    """Raised when an embedding provider cannot be constructed from settings."""


def resolve_embedding_provider_name(
    *,
    settings: AimfSettings | None = None,
    embedding_settings: KnowledgeEmbeddingSettings | None = None,
) -> str:
    """Resolve the selected embedding provider (no silent fallback)."""

    if settings is not None:
        return settings.ai.embedding_provider.strip().lower()
    cfg = embedding_settings or KnowledgeEmbeddingSettings()
    return cfg.provider.strip().lower()


def create_embedding_provider(
    settings: KnowledgeEmbeddingSettings | None = None,
    *,
    aimf_settings: AimfSettings | None = None,
    registry: AIProviderRegistry | None = None,
    **kwargs: Any,
) -> EmbeddingProvider:
    """Create an embedding provider from configuration via the registry.

    Never silently falls back to another provider when the selected one fails
    or is unimplemented.
    """

    from aimf.ai.providers.registry import get_default_registry

    emb = settings or (
        aimf_settings.knowledge.embedding
        if aimf_settings is not None
        else KnowledgeEmbeddingSettings()
    )
    name = resolve_embedding_provider_name(
        settings=aimf_settings,
        embedding_settings=emb,
    )
    if name in RESERVED_UNIMPLEMENTED:
        raise EmbeddingProviderConfigurationError(
            f"embedding provider {name!r} is reserved but not implemented; "
            "use deterministic, bedrock, or openai"
        )
    if name not in {"deterministic", "bedrock", "openai"}:
        raise EmbeddingProviderConfigurationError(
            f"unknown embedding provider {name!r}; "
            f"supported: {sorted(SUPPORTED_EMBEDDING_PROVIDERS - RESERVED_UNIMPLEMENTED)}"
        )

    reg = registry or get_default_registry()
    provider: EmbeddingProvider = reg.create_embedding(
        name,
        settings=aimf_settings,
        embedding_settings=emb,
        **kwargs,
    )
    return provider


__all__ = [
    "SUPPORTED_EMBEDDING_PROVIDERS",
    "EmbeddingProviderConfigurationError",
    "create_embedding_provider",
    "resolve_embedding_provider_name",
]
