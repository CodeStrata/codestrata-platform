"""Provider-neutral embedding domain models (Phase 5.3)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from codestrata.domain.graph.validation import as_tuple, optional_nonblank, require_nonblank
from codestrata_platform.rag.domain.schemas import (
    EMBEDDING_RESULT_SCHEMA_NAME,
    EMBEDDING_RESULT_SCHEMA_VERSION,
)


class EmbeddingProviderId(StrEnum):
    """Known embedding provider identifiers (only deterministic is implemented)."""

    DETERMINISTIC = "deterministic"
    BEDROCK = "bedrock"
    OPENAI = "openai"
    LOCAL_SENTENCE_TRANSFORMER = "local_sentence_transformer"


class EmbeddingRequest(BaseModel):
    """One text embedding request with stable ordering identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    text: str

    @field_validator("request_id", mode="before")
    @classmethod
    def normalize_request_id(cls, value: object) -> str:
        return require_nonblank(str(value), label="request_id")

    @field_validator("text", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("text must be a string")
        return value


class EmbeddingUsage(BaseModel):
    """Optional usage counters for future metered providers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    input_characters: int = Field(default=0, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)


class EmbeddingDiagnostic(BaseModel):
    """Diagnostic for embedding failures or limitations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    message: str
    request_id: str | None = None
    severity: str = "info"

    @field_validator("code", "message", "severity", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="embedding diagnostic field")

    @field_validator("request_id", mode="before")
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="request_id")


class EmbeddingModelIdentity(BaseModel):
    """Stable provider/model identity used for index compatibility."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider_id: str
    model: str
    model_version: str
    dimension: int = Field(ge=1)

    @field_validator("provider_id", "model", "model_version", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="embedding model identity field")


class EmbeddingProviderCapabilities(BaseModel):
    """Capability advertisement for embedding providers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider_id: str
    supports_batch: bool = True
    max_batch_size: int | None = Field(default=None, ge=1)
    max_input_characters: int | None = Field(default=None, ge=1)
    dimension: int = Field(ge=1)
    is_deterministic: bool = False
    is_production_semantic: bool = False
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("provider_id", mode="before")
    @classmethod
    def normalize_provider_id(cls, value: object) -> str:
        return require_nonblank(str(value), label="provider_id").strip().lower()


class EmbeddingProviderHealth(BaseModel):
    """Health probe for an embedding provider."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    healthy: bool
    message: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="message")


class EmbeddingResult(BaseModel):
    """One embedding vector for a request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_name: str = EMBEDDING_RESULT_SCHEMA_NAME
    schema_version: str = EMBEDDING_RESULT_SCHEMA_VERSION
    request_id: str
    embedding: tuple[float, ...]
    dimension: int = Field(ge=1)
    model_identity: EmbeddingModelIdentity
    usage: EmbeddingUsage = Field(default_factory=EmbeddingUsage)
    diagnostics: tuple[EmbeddingDiagnostic, ...] = ()

    @field_validator("request_id", "schema_name", "schema_version", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="embedding result field")

    @field_validator("embedding", mode="before")
    @classmethod
    def normalize_embedding(cls, value: object) -> tuple[float, ...]:
        if isinstance(value, tuple):
            values = value
        elif isinstance(value, list):
            values = tuple(value)
        else:
            raise ValueError("embedding must be a list or tuple of floats")
        if not values:
            raise ValueError("embedding must not be empty")
        cleaned: list[float] = []
        for item in values:
            if isinstance(item, bool) or not isinstance(item, int | float):
                raise ValueError("embedding values must be numbers")
            cleaned.append(float(item))
        return tuple(cleaned)

    @field_validator("diagnostics", mode="before")
    @classmethod
    def normalize_diagnostics(cls, value: object) -> tuple[Any, ...]:
        return as_tuple(value)


class EmbeddingBatchResult(BaseModel):
    """Ordered batch embedding results (aligned with request order)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    results: tuple[EmbeddingResult, ...] = ()
    failed_request_ids: tuple[str, ...] = ()
    diagnostics: tuple[EmbeddingDiagnostic, ...] = ()

    @field_validator("results", "failed_request_ids", "diagnostics", mode="before")
    @classmethod
    def normalize_sequences(cls, value: object) -> tuple[Any, ...]:
        return as_tuple(value)

    @property
    def success_count(self) -> int:
        return len(self.results)

    @property
    def failure_count(self) -> int:
        return len(self.failed_request_ids)
