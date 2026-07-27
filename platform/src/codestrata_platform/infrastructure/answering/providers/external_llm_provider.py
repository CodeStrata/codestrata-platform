"""Provider-neutral boundary for future external LLM providers."""

from __future__ import annotations

from codestrata_platform.domain.answering.errors import AnsweringInvariantError
from codestrata_platform.domain.answering.ports import (
    LLMCapabilities,
    LLMGenerateRequest,
    LLMGenerateResult,
)


class ExternalLLMProvider:
    """Stub for Bedrock / OpenAI adapters.

    Does not select a paid provider automatically.
    """

    def __init__(self, *, provider_id: str, model_id: str) -> None:
        self._provider_id = provider_id.strip().lower()
        self._model_id = model_id.strip()

    def provider_id(self) -> str:
        return self._provider_id

    def model_id(self) -> str:
        return self._model_id

    def capabilities(self) -> LLMCapabilities:
        return LLMCapabilities(is_deterministic=False, is_production_semantic=True)

    def generate(self, request: LLMGenerateRequest) -> LLMGenerateResult:
        raise AnsweringInvariantError(
            "External LLM provider is not configured for this environment",
            reason_code="external_llm_not_configured",
        )

    def health_check(self) -> bool:
        return False


__all__ = ["ExternalLLMProvider"]
