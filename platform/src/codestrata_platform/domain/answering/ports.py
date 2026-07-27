"""LLM provider port and provider response value objects."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

from codestrata_platform.domain.answering.identifiers import ProviderRequestId
from codestrata_platform.domain.answering.policy import GenerationParameters
from codestrata_platform.domain.errors import InvalidValueError


@dataclass(frozen=True, slots=True)
class LLMCapabilities:
    supports_citations: bool = True
    max_input_characters: int = 48_000
    max_output_tokens: int = 3_000
    is_deterministic: bool = False
    is_production_semantic: bool = False


@dataclass(frozen=True, slots=True)
class LLMGenerateRequest:
    system_instruction: str
    user_question: str
    retrieval_context: str
    parameters: GenerationParameters
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.system_instruction.strip():
            raise InvalidValueError(
                "system_instruction must be non-blank",
                reason_code="empty_system_instruction",
            )
        if not self.user_question.strip():
            raise InvalidValueError(
                "user_question must be non-blank",
                reason_code="empty_user_question",
            )


@dataclass(frozen=True, slots=True)
class LLMGenerateResult:
    generated_text: str
    provider_request_id: ProviderRequestId
    finish_reason: str
    usage_metadata: Mapping[str, int] = field(default_factory=dict)
    safety_metadata: Mapping[str, str] = field(default_factory=dict)
    provider_diagnostics: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_text", self.generated_text.strip())
        object.__setattr__(self, "finish_reason", self.finish_reason.strip() or "unknown")


class LLMProvider(Protocol):
    def provider_id(self) -> str: ...

    def model_id(self) -> str: ...

    def capabilities(self) -> LLMCapabilities: ...

    def generate(self, request: LLMGenerateRequest) -> LLMGenerateResult: ...

    def health_check(self) -> bool: ...
