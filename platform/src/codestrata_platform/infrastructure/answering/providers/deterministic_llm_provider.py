"""Deterministic LLM provider for tests and local orchestration validation."""

from __future__ import annotations

import hashlib
import re

from codestrata_platform.domain.answering.identifiers import ProviderRequestId
from codestrata_platform.domain.answering.ports import (
    LLMCapabilities,
    LLMGenerateRequest,
    LLMGenerateResult,
)

_LABEL_RE = re.compile(r"\[(?:C|P)\d+\]")


class DeterministicLLMProvider:
    """Produces citation-shaped grounded responses without network access."""

    PROVIDER_ID = "deterministic"
    DEFAULT_MODEL = "deterministic-test-answer"

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        fail_next: bool = False,
        malformed_next: bool = False,
    ) -> None:
        self._model = model.strip() or self.DEFAULT_MODEL
        self._fail_next = fail_next
        self._malformed_next = malformed_next

    def provider_id(self) -> str:
        return self.PROVIDER_ID

    def model_id(self) -> str:
        return self._model

    def capabilities(self) -> LLMCapabilities:
        return LLMCapabilities(
            supports_citations=True,
            is_deterministic=True,
            is_production_semantic=False,
        )

    def generate(self, request: LLMGenerateRequest) -> LLMGenerateResult:
        if self._fail_next:
            self._fail_next = False
            raise TimeoutError("deterministic provider simulated timeout")
        request_id = ProviderRequestId(
            "det-req:" + hashlib.sha256(request.user_question.encode("utf-8")).hexdigest()[:24]
        )
        if self._malformed_next:
            self._malformed_next = False
            return LLMGenerateResult(
                generated_text=(
                    "I inspected the repository source and invent behavior without citations."
                ),
                provider_request_id=request_id,
                finish_reason="stop",
                usage_metadata={
                    "input_characters": len(request.user_question),
                    "output_tokens": 20,
                },
                provider_diagnostics={"mode": "malformed_simulation"},
            )
        labels = _LABEL_RE.findall(request.user_question)
        unique = []
        for label in labels:
            if label not in unique:
                unique.append(label)
        if not unique:
            unique = ["[P1]"] if "[P" in request.user_question else ["[C1]"]
        cited = ", ".join(unique[:3])
        text = (
            f"Based on retrieved Platform intelligence {cited}, "
            f"the assessment context supports a grounded answer to the question. "
            f"Observed facts are limited to the supplied retrieval context. "
            f"No raw repository source code was inspected."
        )
        return LLMGenerateResult(
            generated_text=text,
            provider_request_id=request_id,
            finish_reason="stop",
            usage_metadata={
                "input_characters": len(request.user_question) + len(request.system_instruction),
                "output_tokens": max(1, len(text) // 4),
            },
            provider_diagnostics={"mode": "deterministic"},
        )

    def health_check(self) -> bool:
        return True


__all__ = ["DeterministicLLMProvider"]
