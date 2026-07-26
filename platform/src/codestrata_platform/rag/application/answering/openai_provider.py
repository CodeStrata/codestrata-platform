"""OpenAI grounded-answer provider (Phase 5.8)."""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Protocol

from codestrata.ai.providers.common import (
    ProviderAuthenticationError,
    ProviderThrottlingError,
    ProviderTimeoutError,
    categorize_provider_error,
    retry_call,
)
from codestrata.config.settings import (
    CodestrataSettings,
    KnowledgeAnsweringSettings,
    OpenAISettings,
)
from codestrata.security.database_url import sanitize_exception_message
from codestrata_platform.rag.application.answering.llm_schema import (
    StructuredAnswerValidationError,
    parse_llm_answer,
)
from codestrata_platform.rag.application.answering.prompts import (
    PROMPT_VERSION,
    build_repair_prompt,
    build_user_prompt,
    get_system_prompt,
)
from codestrata_platform.rag.application.answering.protocol import (
    AnswerProviderCapabilities,
    AnswerProviderDiagnostic,
    AnswerProviderHealth,
    AnswerProviderRequest,
    AnswerProviderResult,
    AnswerProviderUsage,
)
from codestrata_platform.rag.application.answering.safety import (
    looks_like_instruction_injection,
    scrub_hits,
)
from codestrata_platform.rag.domain.answering import AnswerModelIdentity

logger = logging.getLogger(__name__)


class OpenAIChatCompletions(Protocol):
    def create(self, **kwargs: Any) -> Any: ...


class OpenAIChatClient(Protocol):
    @property
    def chat(self) -> Any: ...


class OpenAIAnswerProvider:
    """Production OpenAI grounded answers via chat completions JSON mode."""

    PROVIDER_ID = "openai"

    def __init__(
        self,
        *,
        client: OpenAIChatClient | None = None,
        model: str = "gpt-4o-mini",
        model_version: str = "1.0.0",
        timeout_seconds: int = 60,
        max_retries: int = 3,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str = "",
        settings: CodestrataSettings | None = None,
    ) -> None:
        self._client = client
        self._model = model.strip()
        self._model_version = model_version.strip()
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._api_key_env = api_key_env
        self._base_url = base_url.strip()
        self._settings = settings

    def model_identity(self) -> AnswerModelIdentity:
        return AnswerModelIdentity(
            provider_id=self.PROVIDER_ID,
            model=self._model,
            model_version=self._model_version,
            is_production_model=True,
            is_generative_ai=True,
        )

    def capabilities(self) -> AnswerProviderCapabilities:
        return AnswerProviderCapabilities(
            provider_id=self.PROVIDER_ID,
            supports_freeform_synthesis=True,
            supports_streaming=False,
            is_generative_ai=True,
            is_production_model=True,
            extra={"prompt_version": PROMPT_VERSION, "api": "openai.chat"},
        )

    def health(self) -> AnswerProviderHealth:
        try:
            if self._client is None and not os.environ.get(self._api_key_env, "").strip():
                return AnswerProviderHealth(
                    healthy=False,
                    message=f"{self._api_key_env} is not set",
                    detail={"category": "authentication"},
                )
            _ = self._get_client()
            return AnswerProviderHealth(
                healthy=True,
                message="openai answer provider configured",
                detail={"model": self._model, "prompt_version": PROMPT_VERSION},
            )
        except Exception as exc:  # noqa: BLE001
            return AnswerProviderHealth(
                healthy=False,
                message=sanitize_exception_message(str(exc)),
                detail={"category": categorize_provider_error(exc)},
            )

    def generate(self, request: AnswerProviderRequest) -> AnswerProviderResult:
        started = time.perf_counter()
        hits = scrub_hits(request.hits)
        injection_flags = sum(
            1 for hit in hits if hit.content and looks_like_instruction_injection(hit.content)
        )
        user_prompt = build_user_prompt(
            question=request.normalized_question,
            style=request.style,
            hits=hits,
            citation_labels=request.citation_labels,
        )
        diagnostics: list[AnswerProviderDiagnostic] = []
        if injection_flags:
            diagnostics.append(
                AnswerProviderDiagnostic(
                    code="prompt_injection_heuristic",
                    message=(
                        f"flagged {injection_flags} evidence block(s) with "
                        "instruction-like content; treated as untrusted data"
                    ),
                    severity="warning",
                )
            )

        repair_count = 0
        text, tokens, request_id = self._invoke(user_prompt)
        try:
            result = parse_llm_answer(
                text,
                hits=hits,
                allowed_citations=request.citation_labels,
            )
        except StructuredAnswerValidationError as exc:
            repair_count = 1
            repair = build_repair_prompt(
                error=str(exc),
                citation_labels=request.citation_labels,
            )
            text, tokens, request_id = self._invoke(user_prompt + "\n\n" + repair)
            result = parse_llm_answer(
                text,
                hits=hits,
                allowed_citations=request.citation_labels,
            )

        latency_ms = int((time.perf_counter() - started) * 1000)
        diagnostics.extend(result.diagnostics)
        diagnostics.append(
            AnswerProviderDiagnostic(
                code="provider_usage",
                message=(
                    f"provider=openai model={self._model} latency_ms={latency_ms} "
                    f"retries=0 repair_count={repair_count} "
                    f"tokens={tokens} prompt_version={PROMPT_VERSION} "
                    f"request_id={request_id or 'none'}"
                ),
                severity="info",
            )
        )
        return AnswerProviderResult(
            summary=result.summary,
            statements=result.statements,
            citations=result.citations,
            diagnostics=tuple(diagnostics),
            usage=AnswerProviderUsage(
                statements_proposed=result.usage.statements_proposed,
                citations_attached=result.usage.citations_attached,
                characters_produced=result.usage.characters_produced,
            ),
            insufficient_evidence=result.insufficient_evidence,
        )

    def _get_client(self) -> OpenAIChatClient:
        if self._client is not None:
            return self._client
        api_key = os.environ.get(self._api_key_env, "").strip()
        if not api_key:
            raise ProviderAuthenticationError(
                f"{self._api_key_env} is required for openai answers"
            )
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "openai package is required for OpenAIAnswerProvider "
                "(pip install 'codestrata[openai]')"
            ) from exc
        kwargs: dict[str, Any] = {
            "api_key": api_key,
            "timeout": float(self._timeout_seconds),
            "max_retries": 0,
        }
        if self._base_url:
            kwargs["base_url"] = self._base_url
        self._client = OpenAI(**kwargs)
        return self._client

    def _invoke(self, user_prompt: str) -> tuple[str, int | None, str | None]:
        client = self._get_client()

        def _call() -> Any:
            try:
                return client.chat.completions.create(
                    model=self._model,
                    temperature=0,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": get_system_prompt()},
                        {"role": "user", "content": user_prompt},
                    ],
                )
            except Exception as exc:  # noqa: BLE001
                category = categorize_provider_error(exc)
                if category == "throttling":
                    raise ProviderThrottlingError(str(exc)) from exc
                if category == "authentication":
                    raise ProviderAuthenticationError(
                        sanitize_exception_message(str(exc))
                    ) from exc
                if category == "timeout":
                    raise ProviderTimeoutError(str(exc)) from exc
                raise

        response = retry_call(
            _call,
            max_retries=self._max_retries,
            retry_on=(ProviderThrottlingError,),
        )
        choice = response.choices[0]
        text = (choice.message.content or "").strip()
        usage = getattr(response, "usage", None)
        tokens = getattr(usage, "total_tokens", None) if usage else None
        request_id = getattr(response, "id", None)
        return text, int(tokens) if tokens is not None else None, request_id


def create_openai_answer_provider(
    *,
    settings: CodestrataSettings | None = None,
    answering_settings: KnowledgeAnsweringSettings | None = None,
    openai_settings: OpenAISettings | None = None,
    client: OpenAIChatClient | None = None,
    model: str | None = None,
    **_: Any,
) -> OpenAIAnswerProvider:
    del answering_settings
    oai = openai_settings or (settings.ai.openai if settings else OpenAISettings())
    return OpenAIAnswerProvider(
        client=client,
        model=(model or oai.answer_model).strip(),
        timeout_seconds=oai.timeout_seconds,
        max_retries=oai.max_retries,
        api_key_env=oai.api_key_env,
        base_url=oai.base_url,
        settings=settings,
    )


__all__ = [
    "OpenAIAnswerProvider",
    "OpenAIChatClient",
    "create_openai_answer_provider",
]
