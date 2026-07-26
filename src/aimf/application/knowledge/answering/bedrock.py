"""AWS Bedrock grounded-answer provider (Phase 5.8)."""

from __future__ import annotations

import logging
import time
from typing import Any, Protocol

from aimf.ai.aws_config import (
    AwsAuthenticationError,
    create_bedrock_runtime_client,
)
from aimf.ai.providers.common import (
    ProviderAuthenticationError,
    ProviderThrottlingError,
    ProviderTimeoutError,
    categorize_provider_error,
    retry_call,
)
from aimf.application.knowledge.answering.llm_schema import (
    StructuredAnswerValidationError,
    parse_llm_answer,
)
from aimf.application.knowledge.answering.prompts import (
    PROMPT_VERSION,
    build_repair_prompt,
    build_user_prompt,
    get_system_prompt,
)
from aimf.application.knowledge.answering.protocol import (
    AnswerProviderCapabilities,
    AnswerProviderDiagnostic,
    AnswerProviderHealth,
    AnswerProviderRequest,
    AnswerProviderResult,
    AnswerProviderUsage,
)
from aimf.application.knowledge.answering.safety import (
    looks_like_instruction_injection,
    scrub_hits,
)
from aimf.config.settings import AimfSettings, BedrockSettings, KnowledgeAnsweringSettings
from aimf.domain.knowledge.answering import AnswerModelIdentity
from aimf.security.database_url import sanitize_exception_message

logger = logging.getLogger(__name__)


class BedrockConverseClient(Protocol):
    def converse(self, **kwargs: Any) -> Any: ...


class BedrockAnswerProvider:
    """Production Bedrock grounded answers via Converse API."""

    PROVIDER_ID = "bedrock"

    def __init__(
        self,
        *,
        client: BedrockConverseClient | None = None,
        model: str = "amazon.nova-lite-v1:0",
        model_version: str = "1.0.0",
        timeout_seconds: int = 60,
        max_retries: int = 3,
        settings: AimfSettings | None = None,
    ) -> None:
        self._client = client
        self._model = model.strip()
        self._model_version = model_version.strip()
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
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
            extra={"prompt_version": PROMPT_VERSION, "api": "bedrock.converse"},
        )

    def health(self) -> AnswerProviderHealth:
        try:
            _ = self._get_client()
            return AnswerProviderHealth(
                healthy=True,
                message="bedrock answer provider configured",
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
        text, usage_tokens, request_id = self._invoke(user_prompt)
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
            text, usage_tokens, request_id = self._invoke(
                user_prompt + "\n\n" + repair
            )
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
                    f"provider=bedrock model={self._model} latency_ms={latency_ms} "
                    f"retries=0 repair_count={repair_count} "
                    f"tokens={usage_tokens} prompt_version={PROMPT_VERSION} "
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

    def _get_client(self) -> BedrockConverseClient:
        if self._client is not None:
            return self._client
        try:
            client = create_bedrock_runtime_client(
                settings=self._settings,
                timeout_seconds=float(self._timeout_seconds),
                model_id=self._model,
            )
        except AwsAuthenticationError as exc:
            raise ProviderAuthenticationError(str(exc)) from exc
        self._client = client
        return client

    def _invoke(self, user_prompt: str) -> tuple[str, int | None, str | None]:
        client = self._get_client()

        def _call() -> Any:
            try:
                return client.converse(
                    modelId=self._model,
                    messages=[
                        {
                            "role": "user",
                            "content": [{"text": user_prompt}],
                        }
                    ],
                    system=[{"text": get_system_prompt()}],
                    inferenceConfig={"temperature": 0.0},
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
        text_parts: list[str] = []
        for item in response.get("output", {}).get("message", {}).get("content", []):
            if isinstance(item, dict) and "text" in item:
                text_parts.append(str(item["text"]))
        text = "\n".join(text_parts).strip()
        usage = response.get("usage") or {}
        tokens = usage.get("totalTokens")
        request_id = None
        metadata = response.get("ResponseMetadata") or {}
        if isinstance(metadata, dict):
            request_id = metadata.get("RequestId")
        return text, int(tokens) if tokens is not None else None, request_id


def create_bedrock_answer_provider(
    *,
    settings: AimfSettings | None = None,
    answering_settings: KnowledgeAnsweringSettings | None = None,
    bedrock_settings: BedrockSettings | None = None,
    client: BedrockConverseClient | None = None,
    model: str | None = None,
    **_: Any,
) -> BedrockAnswerProvider:
    del answering_settings
    bed = bedrock_settings or (settings.ai.bedrock if settings else BedrockSettings())
    resolved = (
        model
        or (bed.answer_model or None)
        or bed.model_id
        or "amazon.nova-lite-v1:0"
    )
    return BedrockAnswerProvider(
        client=client,
        model=str(resolved),
        timeout_seconds=bed.timeout_seconds,
        max_retries=bed.max_retries,
        settings=settings,
    )


__all__ = [
    "BedrockAnswerProvider",
    "BedrockConverseClient",
    "create_bedrock_answer_provider",
]
