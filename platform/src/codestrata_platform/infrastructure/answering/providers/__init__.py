"""LLM provider factory."""

from __future__ import annotations

from codestrata_platform.application.answering.policies import (
    configured_llm_model,
    configured_llm_provider,
)
from codestrata_platform.domain.answering.ports import LLMProvider
from codestrata_platform.infrastructure.answering.providers.deterministic_llm_provider import (
    DeterministicLLMProvider,
)
from codestrata_platform.infrastructure.answering.providers.external_llm_provider import (
    ExternalLLMProvider,
)


def create_llm_provider() -> LLMProvider:
    provider = configured_llm_provider()
    model = configured_llm_model()
    if provider == DeterministicLLMProvider.PROVIDER_ID:
        return DeterministicLLMProvider(model=model)
    return ExternalLLMProvider(provider_id=provider, model_id=model)


__all__ = [
    "DeterministicLLMProvider",
    "ExternalLLMProvider",
    "create_llm_provider",
]
