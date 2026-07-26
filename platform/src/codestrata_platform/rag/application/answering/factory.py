"""Answer provider factory (Phase 5.6 / 5.8).

Resolves providers through ``AIProviderRegistry``. Prefer
``[ai].answer_provider`` when ``CodestrataSettings`` is supplied; otherwise use
``knowledge.answering.provider``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from codestrata.config.settings import CodestrataSettings, KnowledgeAnsweringSettings
from codestrata_platform.rag.application.answering.deterministic import (
    DeterministicExtractiveAnswerProvider,
    create_deterministic_extractive_answer_provider,
)
from codestrata_platform.rag.application.answering.protocol import AnswerProvider

if TYPE_CHECKING:
    from codestrata.ai.providers.registry import AIProviderRegistry

RESERVED_UNIMPLEMENTED_PROVIDERS = frozenset({"anthropic", "local_model"})


class AnswerProviderConfigurationError(ValueError):
    """Raised when an answering provider cannot be constructed from settings."""


def resolve_answer_provider_name(
    *,
    settings: CodestrataSettings | None = None,
    answering_settings: KnowledgeAnsweringSettings | None = None,
) -> str:
    """Resolve the selected answer provider (no silent fallback)."""

    if settings is not None:
        return settings.ai.answer_provider.strip().lower()
    cfg = answering_settings or KnowledgeAnsweringSettings()
    return (cfg.provider or "").strip().lower()


def create_answer_provider(
    settings: KnowledgeAnsweringSettings | None = None,
    *,
    codestrata_settings: CodestrataSettings | None = None,
    registry: AIProviderRegistry | None = None,
    **kwargs: Any,
) -> AnswerProvider:
    """Create an AnswerProvider from configuration via the registry.

    Never silently falls back to the deterministic provider when another
    provider name is selected but unimplemented or misconfigured.
    """

    from codestrata.ai.providers.registry import get_default_registry

    answering = settings or (
        codestrata_settings.knowledge.answering
        if codestrata_settings is not None
        else KnowledgeAnsweringSettings()
    )
    name = resolve_answer_provider_name(
        settings=codestrata_settings,
        answering_settings=answering,
    )
    if name in RESERVED_UNIMPLEMENTED_PROVIDERS:
        raise AnswerProviderConfigurationError(
            f"answer provider {name!r} is reserved but not implemented in Phase 5.8"
        )
    allowed = {
        "deterministic",
        "deterministic_extractive",
        "bedrock",
        "openai",
    }
    if name not in allowed:
        raise AnswerProviderConfigurationError(
            f"unknown answer provider {name!r}; "
            f"supported: {sorted(allowed - {'deterministic'})}; "
            f"reserved: {', '.join(sorted(RESERVED_UNIMPLEMENTED_PROVIDERS))}"
        )

    reg = registry or get_default_registry()
    provider: AnswerProvider = reg.create_answer(
        name,
        settings=codestrata_settings,
        answering_settings=answering,
        **kwargs,
    )
    return provider


__all__ = [
    "AnswerProviderConfigurationError",
    "DeterministicExtractiveAnswerProvider",
    "RESERVED_UNIMPLEMENTED_PROVIDERS",
    "create_answer_provider",
    "create_deterministic_extractive_answer_provider",
    "resolve_answer_provider_name",
]
