"""Answering policy value objects."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.answering.identifiers import (
    AnswerPolicyVersion,
    PromptTemplateVersion,
)
from codestrata_platform.domain.errors import InvalidValueError

DEFAULT_TEMPERATURE = 0.1
HARD_MAX_TEMPERATURE = 0.5
DEFAULT_MAX_OUTPUT_TOKENS = 1_200
HARD_MAX_OUTPUT_TOKENS = 3_000
DEFAULT_TOP_K = 12
HARD_MAX_TOP_K = 50


@dataclass(frozen=True, slots=True)
class GenerationParameters:
    temperature: float = DEFAULT_TEMPERATURE
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS
    timeout_seconds: int = 30

    def __post_init__(self) -> None:
        if self.temperature < 0 or self.temperature > HARD_MAX_TEMPERATURE:
            raise InvalidValueError(
                f"temperature must be between 0 and {HARD_MAX_TEMPERATURE}",
                reason_code="invalid_temperature",
            )
        if self.max_output_tokens < 1 or self.max_output_tokens > HARD_MAX_OUTPUT_TOKENS:
            raise InvalidValueError(
                f"max_output_tokens must be between 1 and {HARD_MAX_OUTPUT_TOKENS}",
                reason_code="invalid_max_output_tokens",
            )
        if self.timeout_seconds < 1 or self.timeout_seconds > 120:
            raise InvalidValueError(
                "timeout_seconds must be between 1 and 120",
                reason_code="invalid_llm_timeout",
            )


@dataclass(frozen=True, slots=True)
class AnsweringPolicy:
    answer_policy_version: AnswerPolicyVersion
    prompt_template_version: PromptTemplateVersion
    retrieval_policy_version: str
    allow_partially_grounded: bool = True
    cache_enabled: bool = True
    generation: GenerationParameters = GenerationParameters()
