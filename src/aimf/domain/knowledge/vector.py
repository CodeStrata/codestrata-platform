"""Provider-neutral vector-store domain models."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aimf.domain.graph.validation import optional_nonblank, require_nonblank
from aimf.domain.knowledge.identifiers import build_vector_record_id, fingerprint_payload
from aimf.domain.knowledge.schemas import (
    VECTOR_RECORD_SCHEMA_NAME,
    VECTOR_RECORD_SCHEMA_VERSION,
)


class IndexScope(BaseModel):
    """Isolation boundary for indexed vector records."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str | None = None
    repository_id: str | None = None
    scan_id: str | None = None
    namespace: str = "default"

    @field_validator("tenant_id", "repository_id", "scan_id", mode="before")
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="index scope field")

    @field_validator("namespace", mode="before")
    @classmethod
    def normalize_namespace(cls, value: object) -> str:
        return require_nonblank(str(value), label="namespace").strip().lower()

    def matches(self, metadata: Mapping[str, Any]) -> bool:
        """Return True when ``metadata`` satisfies all set scope fields."""

        if self.tenant_id is not None and metadata.get("tenant_id") != self.tenant_id:
            return False
        if self.repository_id is not None and metadata.get("repository_id") != self.repository_id:
            return False
        if self.scan_id is not None and metadata.get("scan_id") != self.scan_id:
            return False
        if metadata.get("namespace", "default") != self.namespace:
            return False
        return True


class VectorFilter(BaseModel):
    """Equality metadata filter for vector search and scoped operations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str | None = None
    repository_id: str | None = None
    scan_id: str | None = None
    equals: dict[str, Any] = Field(default_factory=dict)

    @field_validator("tenant_id", "repository_id", "scan_id", mode="before")
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="vector filter field")

    @field_validator("equals", mode="before")
    @classmethod
    def normalize_equals(cls, value: object) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise ValueError("equals must be a mapping")
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("equals keys must be strings")
            compact = key.strip()
            if not compact:
                raise ValueError("equals keys must not be blank")
            cleaned[compact] = item
        return cleaned

    def matches(self, metadata: Mapping[str, Any]) -> bool:
        """Return True when ``metadata`` satisfies all filter predicates."""

        if self.tenant_id is not None and metadata.get("tenant_id") != self.tenant_id:
            return False
        if self.repository_id is not None and metadata.get("repository_id") != self.repository_id:
            return False
        if self.scan_id is not None and metadata.get("scan_id") != self.scan_id:
            return False
        for key, expected in sorted(self.equals.items()):
            if metadata.get(key) != expected:
                return False
        return True


class VectorRecord(BaseModel):
    """Dense vector record ready for a provider-neutral store."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    record_id: str
    schema_name: str = VECTOR_RECORD_SCHEMA_NAME
    schema_version: str = VECTOR_RECORD_SCHEMA_VERSION
    namespace: str = "default"
    entity_id: str
    embedding: tuple[float, ...]
    metadata: dict[str, Any] = Field(default_factory=dict)
    text: str | None = None
    fingerprint: str

    @field_validator(
        "record_id",
        "schema_name",
        "schema_version",
        "entity_id",
        "fingerprint",
        mode="before",
    )
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="vector record field")

    @field_validator("namespace", mode="before")
    @classmethod
    def normalize_namespace(cls, value: object) -> str:
        return require_nonblank(str(value), label="namespace").strip().lower()

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

    @field_validator("metadata", mode="before")
    @classmethod
    def normalize_metadata(cls, value: object) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise ValueError("metadata must be a mapping")
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("metadata keys must be strings")
            compact = key.strip()
            if not compact:
                raise ValueError("metadata keys must not be blank")
            cleaned[compact] = item
        return cleaned

    @field_validator("text", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="text")

    @model_validator(mode="after")
    def ensure_isolation_keys(self) -> VectorRecord:
        """Ensure namespace is mirrored into metadata for scope matching."""

        meta = dict(self.metadata)
        meta.setdefault("namespace", self.namespace)
        if meta != self.metadata:
            object.__setattr__(self, "metadata", meta)
        return self

    @classmethod
    def create(
        cls,
        *,
        entity_id: str,
        embedding: Sequence[float],
        metadata: Mapping[str, Any] | None = None,
        text: str | None = None,
        namespace: str = "default",
        schema_name: str = VECTOR_RECORD_SCHEMA_NAME,
        schema_version: str = VECTOR_RECORD_SCHEMA_VERSION,
    ) -> VectorRecord:
        """Construct a vector record with a deterministic record ID."""

        ns = require_nonblank(namespace, label="namespace").strip().lower()
        record_id = build_vector_record_id(namespace=ns, entity_id=entity_id)
        meta = dict(metadata or {})
        meta.setdefault("namespace", ns)
        vector = tuple(float(v) for v in embedding)
        fingerprint = fingerprint_payload(
            {
                "schema_name": schema_name,
                "schema_version": schema_version,
                "namespace": ns,
                "entity_id": entity_id,
                "embedding": list(vector),
                "metadata": meta,
                "text": text,
            }
        )
        return cls(
            record_id=record_id,
            schema_name=schema_name,
            schema_version=schema_version,
            namespace=ns,
            entity_id=entity_id,
            embedding=vector,
            metadata=meta,
            text=text,
            fingerprint=fingerprint,
        )


class VectorQuery(BaseModel):
    """Dense similarity query with optional metadata filters."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    embedding: tuple[float, ...]
    top_k: int = 10
    filter: VectorFilter | None = None
    # Reserved for future hybrid retrieval (not executed in this phase).
    text_query: str | None = None

    @field_validator("embedding", mode="before")
    @classmethod
    def normalize_embedding(cls, value: object) -> tuple[float, ...]:
        return VectorRecord.normalize_embedding(value)

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("top_k must be positive")
        return value

    @field_validator("text_query", mode="before")
    @classmethod
    def normalize_text_query(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="text_query")


class VectorSearchResult(BaseModel):
    """One ranked hit from a vector search."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    record_id: str
    score: float
    record: VectorRecord

    @field_validator("record_id", mode="before")
    @classmethod
    def normalize_record_id(cls, value: object) -> str:
        return require_nonblank(str(value), label="record_id")


class VectorStoreCapabilities(BaseModel):
    """Provider capability advertisement for future routing."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider_id: str
    supports_dense: bool = True
    supports_sparse: bool = False
    supports_hybrid: bool = False
    supports_metadata_filter: bool = True
    supports_tenant_isolation: bool = True
    supports_scoped_delete: bool = True
    max_dimensions: int | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("provider_id", mode="before")
    @classmethod
    def normalize_provider_id(cls, value: object) -> str:
        return require_nonblank(str(value), label="provider_id").strip().lower()


class VectorStoreHealth(BaseModel):
    """Health probe result for a vector store provider."""

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
