"""Factory for assess / Modernization Advisor AI model providers."""

from __future__ import annotations

import os

from codestrata.ai.providers.base import AIModelProvider
from codestrata.ai.providers.exceptions import AIProviderConfigurationError
from codestrata.config.settings import DEFAULT_BEDROCK_MODEL_ID, CodestrataSettings

CODESTRATA_BEDROCK_MODEL_ID_ENV = "CODESTRATA_BEDROCK_MODEL_ID"
CODESTRATA_OPENAI_MODEL_ID_ENV = "CODESTRATA_OPENAI_MODEL_ID"

SUPPORTED_ASSESS_AI_PROVIDERS = frozenset({"bedrock", "openai"})


def create_assess_ai_provider(settings: CodestrataSettings) -> AIModelProvider:
    """Create the AI model provider selected by ``[ai].provider`` for assess."""

    provider_name = (settings.ai.provider or "bedrock").strip().lower()
    if provider_name == "bedrock":
        from codestrata.ai.providers.bedrock import BedrockAIModelProvider

        return BedrockAIModelProvider(settings=settings)
    if provider_name == "openai":
        from codestrata.ai.providers.openai_provider import OpenAIAIModelProvider

        return OpenAIAIModelProvider(settings=settings)
    raise AIProviderConfigurationError(
        f"Unsupported assess AI provider '{settings.ai.provider}'. "
        f"Supported: {', '.join(sorted(SUPPORTED_ASSESS_AI_PROVIDERS))}."
    )


def resolve_assess_model_id(
    *,
    cli_model_id: str | None,
    settings: CodestrataSettings,
) -> str:
    """Resolve assess enrichment model ID for the active provider."""

    if cli_model_id and cli_model_id.strip():
        return cli_model_id.strip()

    provider_name = (settings.ai.provider or "bedrock").strip().lower()
    if provider_name == "openai":
        env_model = os.environ.get(CODESTRATA_OPENAI_MODEL_ID_ENV)
        if env_model and env_model.strip():
            return env_model.strip()
        configured = (settings.ai.openai.answer_model or "").strip()
        if configured:
            return configured
        return "gpt-4o-mini"

    env_model_id = os.environ.get(CODESTRATA_BEDROCK_MODEL_ID_ENV)
    if env_model_id and env_model_id.strip():
        return env_model_id.strip()
    configured = (settings.ai.bedrock.model_id or "").strip()
    if configured:
        return configured
    return DEFAULT_BEDROCK_MODEL_ID


# Back-compat alias used by older call sites / docs.
resolve_bedrock_model_id = resolve_assess_model_id

__all__ = [
    "CODESTRATA_BEDROCK_MODEL_ID_ENV",
    "CODESTRATA_OPENAI_MODEL_ID_ENV",
    "SUPPORTED_ASSESS_AI_PROVIDERS",
    "create_assess_ai_provider",
    "resolve_assess_model_id",
    "resolve_bedrock_model_id",
]
