"""AWS Bedrock embedding provider (Phase 5.8)."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from typing import Any, Protocol, cast

from codestrata.ai.aws_config import (
    AwsAuthenticationError,
    create_bedrock_runtime_client,
)
from codestrata.ai.providers.common import (
    ProviderAuthenticationError,
    ProviderThrottlingError,
    ProviderTimeoutError,
    categorize_provider_error,
    retry_call,
)
from codestrata.config.settings import (
    BedrockSettings,
    CodestrataSettings,
    KnowledgeEmbeddingSettings,
)
from codestrata.security.database_url import sanitize_exception_message
from codestrata_platform.rag.domain.embedding import (
    EmbeddingBatchResult,
    EmbeddingDiagnostic,
    EmbeddingModelIdentity,
    EmbeddingProviderCapabilities,
    EmbeddingProviderHealth,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingUsage,
)

logger = logging.getLogger(__name__)

DEFAULT_BEDROCK_EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
DEFAULT_BEDROCK_EMBEDDING_DIMENSION = 1024


class BedrockEmbeddingClient(Protocol):
    def invoke_model(self, **kwargs: Any) -> Any: ...


class BedrockEmbeddingProvider:
    """Production Bedrock embeddings via ``invoke_model`` (Titan Embed Text)."""

    PROVIDER_ID = "bedrock"

    def __init__(
        self,
        *,
        client: BedrockEmbeddingClient | None = None,
        model: str = DEFAULT_BEDROCK_EMBEDDING_MODEL,
        model_version: str = "1.0.0",
        dimension: int = DEFAULT_BEDROCK_EMBEDDING_DIMENSION,
        max_input_characters: int = 12_000,
        batch_size: int = 16,
        timeout_seconds: int = 60,
        max_retries: int = 3,
        settings: CodestrataSettings | None = None,
    ) -> None:
        self._model = model.strip()
        self._model_version = model_version.strip()
        self._dimension = dimension
        self._max_input_characters = max_input_characters
        self._batch_size = batch_size
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._settings = settings
        self._client = client

    def model_identity(self) -> EmbeddingModelIdentity:
        return EmbeddingModelIdentity(
            provider_id=self.PROVIDER_ID,
            model=self._model,
            model_version=self._model_version,
            dimension=self._dimension,
        )

    def capabilities(self) -> EmbeddingProviderCapabilities:
        return EmbeddingProviderCapabilities(
            provider_id=self.PROVIDER_ID,
            supports_batch=True,
            max_batch_size=self._batch_size,
            max_input_characters=self._max_input_characters,
            dimension=self._dimension,
            is_deterministic=False,
            is_production_semantic=True,
            extra={"api": "bedrock.invoke_model"},
        )

    def health(self) -> EmbeddingProviderHealth:
        try:
            _ = self._get_client()
            return EmbeddingProviderHealth(
                healthy=True,
                message="bedrock embedding provider configured",
                detail={"model": self._model, "dimension": self._dimension},
            )
        except Exception as exc:  # noqa: BLE001
            return EmbeddingProviderHealth(
                healthy=False,
                message=sanitize_exception_message(str(exc)),
                detail={"category": categorize_provider_error(exc)},
            )

    def embed_text(self, text: str, *, request_id: str = "single") -> EmbeddingResult:
        batch = self.embed_batch(
            [EmbeddingRequest(request_id=request_id, text=text)]
        )
        if not batch.results:
            raise RuntimeError("bedrock embedding returned no results")
        return batch.results[0]

    def embed_batch(self, requests: Sequence[EmbeddingRequest]) -> EmbeddingBatchResult:
        results: list[EmbeddingResult] = []
        diagnostics: list[EmbeddingDiagnostic] = []
        for request in requests:
            text = request.text
            if len(text) > self._max_input_characters:
                diagnostics.append(
                    EmbeddingDiagnostic(
                        code="input_too_large",
                        message="embedding input exceeds max_input_characters",
                        request_id=request.request_id,
                        severity="error",
                    )
                )
                continue
            try:
                text_for_embed = text

                def _call(
                    value: str = text_for_embed,
                ) -> tuple[list[float], int | None]:
                    return self._embed_once(value)

                vector, tokens = retry_call(
                    _call,
                    max_retries=self._max_retries,
                    retry_on=(ProviderThrottlingError,),
                )
            except Exception as exc:  # noqa: BLE001
                diagnostics.append(
                    EmbeddingDiagnostic(
                        code=categorize_provider_error(exc),
                        message=sanitize_exception_message(str(exc)),
                        request_id=request.request_id,
                        severity="error",
                    )
                )
                continue
            if len(vector) != self._dimension:
                diagnostics.append(
                    EmbeddingDiagnostic(
                        code="dimension_mismatch",
                        message=(
                            f"provider returned {len(vector)} dims; "
                            f"expected {self._dimension}"
                        ),
                        request_id=request.request_id,
                        severity="error",
                    )
                )
                continue
            results.append(
                EmbeddingResult(
                    request_id=request.request_id,
                    embedding=tuple(float(v) for v in vector),
                    dimension=self._dimension,
                    model_identity=self.model_identity(),
                    usage=EmbeddingUsage(
                        input_characters=len(text),
                        input_tokens=tokens,
                    ),
                )
            )
        # Preserve request ordering among successful results.
        order = {item.request_id: index for index, item in enumerate(requests)}
        results.sort(key=lambda item: order.get(item.request_id, 10**9))
        failed_ids = tuple(
            item.request_id
            for item in requests
            if item.request_id not in {r.request_id for r in results}
        )
        return EmbeddingBatchResult(
            results=tuple(results),
            failed_request_ids=failed_ids,
            diagnostics=tuple(diagnostics),
        )

    def _get_client(self) -> BedrockEmbeddingClient:
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
        typed = cast(BedrockEmbeddingClient, client)
        self._client = typed
        return typed

    def _embed_once(self, text: str) -> tuple[list[float], int | None]:
        client = self._get_client()
        body: dict[str, object] = {"inputText": text}
        # Titan V2 optional dimensions.
        if "titan-embed-text-v2" in self._model:
            body["dimensions"] = self._dimension
            body["normalize"] = True
        try:
            response = client.invoke_model(
                modelId=self._model,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body).encode("utf-8"),
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
        payload = response.get("body")
        if hasattr(payload, "read"):
            raw = payload.read()
        else:
            raw = payload
        if isinstance(raw, bytes):
            parsed = json.loads(raw.decode("utf-8"))
        elif isinstance(raw, str):
            parsed = json.loads(raw)
        else:
            parsed = raw
        embedding = parsed.get("embedding") or parsed.get("embeddings")
        if isinstance(embedding, list) and embedding and isinstance(embedding[0], list):
            embedding = embedding[0]
        if not isinstance(embedding, list):
            raise RuntimeError("bedrock embedding response missing embedding array")
        tokens = parsed.get("inputTextTokenCount")
        return [float(v) for v in embedding], int(tokens) if tokens is not None else None


def create_bedrock_embedding_provider(
    *,
    settings: CodestrataSettings | None = None,
    embedding_settings: KnowledgeEmbeddingSettings | None = None,
    bedrock_settings: BedrockSettings | None = None,
    client: BedrockEmbeddingClient | None = None,
    model: str | None = None,
    dimension: int | None = None,
    **_: Any,
) -> BedrockEmbeddingProvider:
    emb = embedding_settings or KnowledgeEmbeddingSettings(provider="bedrock")
    bed = bedrock_settings or (settings.ai.bedrock if settings else BedrockSettings())
    resolved_model = (model or bed.embedding_model or emb.model).strip()
    resolved_dim = dimension or (
        emb.dimension
        if emb.provider == "bedrock" and emb.model != "deterministic-test-embedding"
        else DEFAULT_BEDROCK_EMBEDDING_DIMENSION
    )
    # Prefer explicit knowledge.embedding.dimension when provider is bedrock.
    if embedding_settings is not None:
        resolved_dim = embedding_settings.dimension
    return BedrockEmbeddingProvider(
        client=client,
        model=resolved_model,
        model_version=emb.model_version,
        dimension=resolved_dim,
        max_input_characters=emb.max_input_characters,
        batch_size=min(emb.batch_size, 16),
        timeout_seconds=bed.timeout_seconds,
        max_retries=bed.max_retries,
        settings=settings,
    )


__all__ = [
    "BedrockEmbeddingClient",
    "BedrockEmbeddingProvider",
    "DEFAULT_BEDROCK_EMBEDDING_DIMENSION",
    "DEFAULT_BEDROCK_EMBEDDING_MODEL",
    "create_bedrock_embedding_provider",
]
