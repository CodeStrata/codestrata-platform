"""OpenAI embedding provider (Phase 5.8)."""

from __future__ import annotations

import logging
import os
from collections.abc import Sequence
from typing import Any, Protocol

from aimf.ai.providers.common import (
    ProviderAuthenticationError,
    ProviderThrottlingError,
    ProviderTimeoutError,
    categorize_provider_error,
    retry_call,
)
from aimf.config.settings import AimfSettings, KnowledgeEmbeddingSettings, OpenAISettings
from aimf.domain.knowledge.embedding import (
    EmbeddingBatchResult,
    EmbeddingDiagnostic,
    EmbeddingModelIdentity,
    EmbeddingProviderCapabilities,
    EmbeddingProviderHealth,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingUsage,
)
from aimf.security.database_url import sanitize_exception_message

logger = logging.getLogger(__name__)

DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_OPENAI_EMBEDDING_DIMENSION = 1536


class OpenAIEmbeddingsAPI(Protocol):
    def create(self, **kwargs: Any) -> Any: ...


class OpenAIClient(Protocol):
    @property
    def embeddings(self) -> OpenAIEmbeddingsAPI: ...


class OpenAIEmbeddingProvider:
    """Production OpenAI embeddings via the official SDK."""

    PROVIDER_ID = "openai"

    def __init__(
        self,
        *,
        client: OpenAIClient | None = None,
        model: str = DEFAULT_OPENAI_EMBEDDING_MODEL,
        model_version: str = "1.0.0",
        dimension: int = DEFAULT_OPENAI_EMBEDDING_DIMENSION,
        max_input_characters: int = 12_000,
        batch_size: int = 32,
        timeout_seconds: int = 60,
        max_retries: int = 3,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str = "",
        settings: AimfSettings | None = None,
    ) -> None:
        self._client = client
        self._model = model.strip()
        self._model_version = model_version.strip()
        self._dimension = dimension
        self._max_input_characters = max_input_characters
        self._batch_size = batch_size
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._api_key_env = api_key_env
        self._base_url = base_url.strip()
        self._settings = settings

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
            extra={"api": "openai.embeddings"},
        )

    def health(self) -> EmbeddingProviderHealth:
        try:
            key = os.environ.get(self._api_key_env, "").strip()
            if self._client is None and not key:
                return EmbeddingProviderHealth(
                    healthy=False,
                    message=f"{self._api_key_env} is not set",
                    detail={"category": "authentication"},
                )
            _ = self._get_client()
            return EmbeddingProviderHealth(
                healthy=True,
                message="openai embedding provider configured",
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
            raise RuntimeError("openai embedding returned no results")
        return batch.results[0]

    def embed_batch(self, requests: Sequence[EmbeddingRequest]) -> EmbeddingBatchResult:
        results: list[EmbeddingResult] = []
        diagnostics: list[EmbeddingDiagnostic] = []
        pending: list[EmbeddingRequest] = []
        for request in requests:
            if len(request.text) > self._max_input_characters:
                diagnostics.append(
                    EmbeddingDiagnostic(
                        code="input_too_large",
                        message="embedding input exceeds max_input_characters",
                        request_id=request.request_id,
                        severity="error",
                    )
                )
            else:
                pending.append(request)

        for start in range(0, len(pending), self._batch_size):
            chunk = pending[start : start + self._batch_size]
            try:
                chunk_requests = list(chunk)

                def _call(
                    requests: list[EmbeddingRequest] = chunk_requests,
                ) -> tuple[list[list[float]], int | None]:
                    return self._embed_chunk(requests)

                vectors, tokens = retry_call(
                    _call,
                    max_retries=self._max_retries,
                    retry_on=(ProviderThrottlingError,),
                )
            except Exception as exc:  # noqa: BLE001
                for request in chunk:
                    diagnostics.append(
                        EmbeddingDiagnostic(
                            code=categorize_provider_error(exc),
                            message=sanitize_exception_message(str(exc)),
                            request_id=request.request_id,
                            severity="error",
                        )
                    )
                continue
            for request, vector in zip(chunk, vectors, strict=True):
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
                            input_characters=len(request.text),
                            input_tokens=tokens,
                        ),
                    )
                )

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

    def _get_client(self) -> OpenAIClient:
        if self._client is not None:
            return self._client
        api_key = os.environ.get(self._api_key_env, "").strip()
        if not api_key:
            raise ProviderAuthenticationError(
                f"{self._api_key_env} is required for openai embeddings"
            )
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "openai package is required for OpenAIEmbeddingProvider "
                "(pip install 'ai-modernization-factory[openai]')"
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

    def _embed_chunk(
        self, requests: Sequence[EmbeddingRequest]
    ) -> tuple[list[list[float]], int | None]:
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": self._model,
            "input": [item.text for item in requests],
        }
        if self._dimension > 0 and "text-embedding-3" in self._model:
            kwargs["dimensions"] = self._dimension
        try:
            response = client.embeddings.create(**kwargs)
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
        data = sorted(response.data, key=lambda item: item.index)
        vectors = [list(item.embedding) for item in data]
        usage = getattr(response, "usage", None)
        tokens = getattr(usage, "total_tokens", None) if usage else None
        return vectors, int(tokens) if tokens is not None else None


def create_openai_embedding_provider(
    *,
    settings: AimfSettings | None = None,
    embedding_settings: KnowledgeEmbeddingSettings | None = None,
    openai_settings: OpenAISettings | None = None,
    client: OpenAIClient | None = None,
    model: str | None = None,
    dimension: int | None = None,
    **_: Any,
) -> OpenAIEmbeddingProvider:
    emb = embedding_settings or KnowledgeEmbeddingSettings(provider="openai")
    oai = openai_settings or (settings.ai.openai if settings else OpenAISettings())
    resolved_model = (model or oai.embedding_model or emb.model).strip()
    if dimension is not None:
        resolved_dim = dimension
    elif oai.embedding_dimensions > 0:
        resolved_dim = oai.embedding_dimensions
    elif embedding_settings is not None:
        resolved_dim = embedding_settings.dimension
    else:
        resolved_dim = DEFAULT_OPENAI_EMBEDDING_DIMENSION
    return OpenAIEmbeddingProvider(
        client=client,
        model=resolved_model,
        model_version=emb.model_version,
        dimension=resolved_dim,
        max_input_characters=emb.max_input_characters,
        batch_size=emb.batch_size,
        timeout_seconds=oai.timeout_seconds,
        max_retries=oai.max_retries,
        api_key_env=oai.api_key_env,
        base_url=oai.base_url,
        settings=settings,
    )


__all__ = [
    "DEFAULT_OPENAI_EMBEDDING_DIMENSION",
    "DEFAULT_OPENAI_EMBEDDING_MODEL",
    "OpenAIClient",
    "OpenAIEmbeddingProvider",
    "create_openai_embedding_provider",
]
