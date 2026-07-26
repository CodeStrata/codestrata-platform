"""Repository retrieval domain models (Phase 5.5)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aimf.domain.graph.validation import as_tuple, optional_nonblank, require_nonblank
from aimf.domain.knowledge.identifiers import fingerprint_payload
from aimf.domain.knowledge.schemas import (
    REPOSITORY_RETRIEVAL_REQUEST_SCHEMA_NAME,
    REPOSITORY_RETRIEVAL_REQUEST_SCHEMA_VERSION,
    REPOSITORY_RETRIEVAL_RESULT_SCHEMA_NAME,
    REPOSITORY_RETRIEVAL_RESULT_SCHEMA_VERSION,
    RETRIEVAL_CONTEXT_SCHEMA_NAME,
    RETRIEVAL_CONTEXT_SCHEMA_VERSION,
    RETRIEVAL_HIT_SCHEMA_NAME,
    RETRIEVAL_HIT_SCHEMA_VERSION,
)


class RetrievalStatus(StrEnum):
    """Overall retrieval run status."""

    SUCCESS = "success"
    EMPTY = "empty"
    PARTIAL = "partial"
    FAILED = "failed"
    DISABLED = "disabled"


class RetrievalScope(BaseModel):
    """Isolation boundary for retrieval (tenant + repository required)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    repository_id: str
    scan_id: str | None = None
    branch: str | None = None
    commit_sha: str | None = None

    @field_validator("tenant_id", "repository_id", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="retrieval scope field")

    @field_validator("scan_id", "branch", "commit_sha", mode="before")
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="retrieval scope optional field")


class RetrievalFilters(BaseModel):
    """Optional metadata filters applied after/during vector search."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_types: tuple[str, ...] = ()
    intelligence_packs: tuple[str, ...] = ()
    severities: tuple[str, ...] = ()
    file_paths: tuple[str, ...] = ()
    symbol_names: tuple[str, ...] = ()
    finding_ids: tuple[str, ...] = ()
    rule_ids: tuple[str, ...] = ()
    equals: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "source_types",
        "intelligence_packs",
        "severities",
        "file_paths",
        "symbol_names",
        "finding_ids",
        "rule_ids",
        mode="before",
    )
    @classmethod
    def normalize_string_tuple(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            compact = optional_nonblank(value, label="filter value")
            return (compact,) if compact else ()
        if not isinstance(value, (list, tuple)):
            raise ValueError("filter list fields must be a list or tuple of strings")
        cleaned: list[str] = []
        for item in value:
            text = optional_nonblank(str(item), label="filter value")
            if text is not None:
                cleaned.append(text)
        return tuple(cleaned)

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


class RetrievalQuery(BaseModel):
    """Prepared query text with fingerprint (no rewriting / expansion)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    original: str
    normalized: str
    fingerprint: str

    @field_validator("original", "normalized", "fingerprint", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="retrieval query field")


class RetrievalLimitations(BaseModel):
    """Explicit retrieval limitations for consumers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    statements: tuple[str, ...] = ()

    @field_validator("statements", mode="before")
    @classmethod
    def normalize_statements(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        return as_tuple(value)


class RetrievalDiagnostic(BaseModel):
    """One retrieval diagnostic entry (no secrets)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    message: str
    severity: str = "info"
    record_id: str | None = None
    chunk_id: str | None = None

    @field_validator("code", "message", "severity", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="retrieval diagnostic field")

    @field_validator("record_id", "chunk_id", mode="before")
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="retrieval diagnostic optional")


class RetrievalCoverage(BaseModel):
    """Aggregate retrieval statistics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    candidates_requested: int = Field(default=0, ge=0)
    candidates_returned: int = Field(default=0, ge=0)
    duplicates_removed: int = Field(default=0, ge=0)
    filter_exclusions: int = Field(default=0, ge=0)
    diversity_exclusions: int = Field(default=0, ge=0)
    context_limit_exclusions: int = Field(default=0, ge=0)
    final_hit_count: int = Field(default=0, ge=0)
    retrieval_mode: str | None = None
    vector_candidates: int = Field(default=0, ge=0)
    lexical_candidates: int = Field(default=0, ge=0)
    fused_candidates: int = Field(default=0, ge=0)
    latency_ms: int = Field(default=0, ge=0)
    source_types: tuple[str, ...] = ()
    intelligence_packs: tuple[str, ...] = ()
    files: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()
    scans: tuple[str, ...] = ()

    @field_validator(
        "source_types",
        "intelligence_packs",
        "files",
        "findings",
        "scans",
        mode="before",
    )
    @classmethod
    def normalize_tuples(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        return tuple(str(item) for item in as_tuple(value))


class RetrievalHit(BaseModel):
    """One ranked retrieval hit with optional content and traceability."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_name: str = RETRIEVAL_HIT_SCHEMA_NAME
    schema_version: str = RETRIEVAL_HIT_SCHEMA_VERSION
    rank: int = Field(ge=1)
    score: float
    record_id: str
    citation_label: str
    chunk_id: str | None = None
    document_id: str | None = None
    content: str | None = None
    source_type: str | None = None
    intelligence_pack: str | None = None
    tenant_id: str | None = None
    repository_id: str | None = None
    scan_id: str | None = None
    branch: str | None = None
    commit_sha: str | None = None
    file_path: str | None = None
    symbol_name: str | None = None
    finding_id: str | None = None
    rule_id: str | None = None
    severity: str | None = None
    confidence: str | None = None
    sequence: int | None = None
    content_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    traceability: dict[str, Any] = Field(default_factory=dict)

    @field_validator("record_id", "citation_label", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="retrieval hit field")

    @field_validator(
        "chunk_id",
        "document_id",
        "content",
        "source_type",
        "intelligence_pack",
        "tenant_id",
        "repository_id",
        "scan_id",
        "branch",
        "commit_sha",
        "file_path",
        "symbol_name",
        "finding_id",
        "rule_id",
        "severity",
        "confidence",
        "content_hash",
        mode="before",
    )
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="retrieval hit optional")

    @field_validator("metadata", "traceability", mode="before")
    @classmethod
    def normalize_mapping(cls, value: object) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise ValueError("metadata/traceability must be a mapping")
        return dict(value)


class RetrievalContext(BaseModel):
    """Assembled grounded context from selected hits."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_name: str = RETRIEVAL_CONTEXT_SCHEMA_NAME
    schema_version: str = RETRIEVAL_CONTEXT_SCHEMA_VERSION
    hits: tuple[RetrievalHit, ...] = ()
    character_count: int = Field(default=0, ge=0)
    citation_labels: tuple[str, ...] = ()

    @field_validator("hits", mode="before")
    @classmethod
    def normalize_hits(cls, value: object) -> tuple[RetrievalHit, ...]:
        if value is None:
            return ()
        if isinstance(value, tuple) and all(isinstance(item, RetrievalHit) for item in value):
            return value
        items = as_tuple(value)
        return tuple(
            item if isinstance(item, RetrievalHit) else RetrievalHit.model_validate(item)
            for item in items
        )

    @field_validator("citation_labels", mode="before")
    @classmethod
    def normalize_labels(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        return tuple(str(item) for item in as_tuple(value))


class RetrievalRequest(BaseModel):
    """Provider-neutral repository retrieval request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_name: str = REPOSITORY_RETRIEVAL_REQUEST_SCHEMA_NAME
    schema_version: str = REPOSITORY_RETRIEVAL_REQUEST_SCHEMA_VERSION
    query: str
    scope: RetrievalScope
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)
    top_k: int = Field(default=10, ge=1)
    candidate_limit: int = Field(default=30, ge=1)
    minimum_score: float = 0.0
    max_query_characters: int = Field(default=4000, ge=1)
    max_context_characters: int = Field(default=30_000, ge=1)
    max_chunks_per_document: int = Field(default=3, ge=1)
    max_chunks_per_file: int = Field(default=3, ge=1)
    max_chunks_per_source_type: int = Field(default=5, ge=1)
    include_content: bool = True
    include_metadata: bool = True
    include_traceability: bool = True

    @field_validator("query", mode="before")
    @classmethod
    def normalize_query(cls, value: object) -> str:
        # Preserve original whitespace for fingerprinting of raw input;
        # emptiness is validated during query preparation.
        return str(value)

    @model_validator(mode="after")
    def ensure_candidate_ge_topk(self) -> RetrievalRequest:
        if self.candidate_limit < self.top_k:
            object.__setattr__(self, "candidate_limit", self.top_k)
        return self


class RetrievalResult(BaseModel):
    """Provider-neutral repository retrieval result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_name: str = REPOSITORY_RETRIEVAL_RESULT_SCHEMA_NAME
    schema_version: str = REPOSITORY_RETRIEVAL_RESULT_SCHEMA_VERSION
    status: RetrievalStatus
    query: RetrievalQuery | None = None
    scope: RetrievalScope
    context: RetrievalContext = Field(default_factory=RetrievalContext)
    coverage: RetrievalCoverage = Field(default_factory=RetrievalCoverage)
    diagnostics: tuple[RetrievalDiagnostic, ...] = ()
    limitations: tuple[str, ...] = ()
    fingerprint: str | None = None

    @field_validator("diagnostics", mode="before")
    @classmethod
    def normalize_diagnostics(cls, value: object) -> tuple[RetrievalDiagnostic, ...]:
        if value is None:
            return ()
        items = as_tuple(value)
        return tuple(
            item
            if isinstance(item, RetrievalDiagnostic)
            else RetrievalDiagnostic.model_validate(item)
            for item in items
        )

    @field_validator("limitations", mode="before")
    @classmethod
    def normalize_limitations(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        return tuple(str(item) for item in as_tuple(value))


def retrieval_result_payload(result: RetrievalResult) -> dict[str, Any]:
    """Stable JSON-serializable retrieval result (no embedding arrays)."""

    return result.model_dump(mode="json")


def retrieval_request_payload(request: RetrievalRequest) -> dict[str, Any]:
    return request.model_dump(mode="json")


def build_result_fingerprint(
    *,
    query_fingerprint: str,
    scope: RetrievalScope,
    hit_record_ids: Sequence[str],
    status: RetrievalStatus,
) -> str:
    return fingerprint_payload(
        {
            "query_fingerprint": query_fingerprint,
            "scope": scope.model_dump(mode="json"),
            "hit_record_ids": list(hit_record_ids),
            "status": status.value,
        }
    )
