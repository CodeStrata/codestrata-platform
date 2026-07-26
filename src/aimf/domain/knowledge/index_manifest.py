"""Knowledge index manifest and result models (Phase 5.3)."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aimf.domain.graph.validation import as_tuple, optional_nonblank, require_nonblank
from aimf.domain.knowledge.embedding import EmbeddingModelIdentity
from aimf.domain.knowledge.identifiers import fingerprint_payload
from aimf.domain.knowledge.schemas import (
    KNOWLEDGE_INDEX_MANIFEST_SCHEMA_NAME,
    KNOWLEDGE_INDEX_MANIFEST_SCHEMA_VERSION,
    KNOWLEDGE_INDEX_RESULT_SCHEMA_NAME,
    KNOWLEDGE_INDEX_RESULT_SCHEMA_VERSION,
    VECTOR_RECORD_SCHEMA_VERSION,
)
from aimf.domain.knowledge.vector import IndexScope


class KnowledgeIndexEntryStatus(StrEnum):
    """Per-chunk indexing outcome."""

    UNCHANGED = "unchanged"
    ADDED = "added"
    UPDATED = "updated"
    REMOVED = "removed"
    SKIPPED = "skipped"
    FAILED = "failed"


class KnowledgeIndexStatus(StrEnum):
    """Overall indexing run status (explicit; never silent partial success)."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    DISABLED = "disabled"
    EMPTY = "empty"


class KnowledgeIndexCoverage(BaseModel):
    """Aggregate indexing statistics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_count: int = Field(default=0, ge=0)
    vector_count: int = Field(default=0, ge=0)
    added: int = Field(default=0, ge=0)
    updated: int = Field(default=0, ge=0)
    unchanged: int = Field(default=0, ge=0)
    removed: int = Field(default=0, ge=0)
    skipped: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    stale_deleted: int = Field(default=0, ge=0)
    batches: int = Field(default=0, ge=0)


class KnowledgeIndexDiagnostic(BaseModel):
    """Indexing diagnostic entry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    message: str
    chunk_id: str | None = None
    record_id: str | None = None
    severity: str = "info"

    @field_validator("code", "message", "severity", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="index diagnostic field")

    @field_validator("chunk_id", "record_id", mode="before")
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="index diagnostic optional field")


class KnowledgeIndexEntry(BaseModel):
    """One chunk/record row in the index manifest (no embedding payload)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_id: str
    document_id: str
    record_id: str
    chunk_fingerprint: str
    status: KnowledgeIndexEntryStatus
    sequence: int = Field(ge=0)
    source_type: str | None = None

    @field_validator(
        "chunk_id",
        "document_id",
        "record_id",
        "chunk_fingerprint",
        mode="before",
    )
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="index entry field")

    @field_validator("source_type", mode="before")
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="source_type")


def build_manifest_id(
    *,
    scope: IndexScope,
    fingerprint: str,
) -> str:
    """Deterministic manifest identity from scope and content fingerprint."""

    material = (
        "knowledge-index-manifest\n"
        f"{scope.tenant_id or ''}\n"
        f"{scope.repository_id or ''}\n"
        f"{scope.scan_id or ''}\n"
        f"{scope.namespace}\n"
        f"{fingerprint}"
    )
    token = hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]
    return f"kidx:{token}"


class KnowledgeIndexManifest(BaseModel):
    """Durable index inventory without raw embedding arrays."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest_id: str
    schema_name: str = KNOWLEDGE_INDEX_MANIFEST_SCHEMA_NAME
    schema_version: str = KNOWLEDGE_INDEX_MANIFEST_SCHEMA_VERSION
    corpus_id: str | None = None
    scope: IndexScope
    embedding_identity: EmbeddingModelIdentity
    vector_record_schema_version: str = VECTOR_RECORD_SCHEMA_VERSION
    entries: tuple[KnowledgeIndexEntry, ...] = ()
    coverage: KnowledgeIndexCoverage = Field(default_factory=KnowledgeIndexCoverage)
    diagnostics: tuple[KnowledgeIndexDiagnostic, ...] = ()
    limitations: tuple[str, ...] = ()
    fingerprint: str

    @field_validator(
        "manifest_id",
        "schema_name",
        "schema_version",
        "vector_record_schema_version",
        "fingerprint",
        mode="before",
    )
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="index manifest field")

    @field_validator("corpus_id", mode="before")
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="corpus_id")

    @field_validator("entries", "diagnostics", "limitations", mode="before")
    @classmethod
    def normalize_sequences(cls, value: object) -> tuple[Any, ...]:
        return as_tuple(value)

    @classmethod
    def create(
        cls,
        *,
        scope: IndexScope,
        embedding_identity: EmbeddingModelIdentity,
        entries: Sequence[KnowledgeIndexEntry],
        coverage: KnowledgeIndexCoverage,
        diagnostics: Sequence[KnowledgeIndexDiagnostic] = (),
        limitations: Sequence[str] = (),
        corpus_id: str | None = None,
        vector_record_schema_version: str = VECTOR_RECORD_SCHEMA_VERSION,
    ) -> KnowledgeIndexManifest:
        ordered_entries = tuple(
            sorted(
                entries,
                key=lambda item: (item.document_id, item.sequence, item.chunk_id),
            )
        )
        ordered_diags = tuple(
            sorted(
                diagnostics,
                key=lambda item: (
                    item.code,
                    item.chunk_id or "",
                    item.record_id or "",
                    item.message,
                ),
            )
        )
        ordered_limits = tuple(
            sorted({require_nonblank(item, label="limitation") for item in limitations})
        )
        fingerprint = fingerprint_payload(
            {
                "schema_name": KNOWLEDGE_INDEX_MANIFEST_SCHEMA_NAME,
                "schema_version": KNOWLEDGE_INDEX_MANIFEST_SCHEMA_VERSION,
                "scope": scope.model_dump(mode="json"),
                "embedding_identity": embedding_identity.model_dump(mode="json"),
                "vector_record_schema_version": vector_record_schema_version,
                "entries": [e.model_dump(mode="json") for e in ordered_entries],
                "coverage": coverage.model_dump(mode="json"),
                "diagnostics": [d.model_dump(mode="json") for d in ordered_diags],
                "limitations": list(ordered_limits),
                "corpus_id": corpus_id,
            }
        )
        return cls(
            manifest_id=build_manifest_id(scope=scope, fingerprint=fingerprint),
            corpus_id=corpus_id,
            scope=scope,
            embedding_identity=embedding_identity,
            vector_record_schema_version=vector_record_schema_version,
            entries=ordered_entries,
            coverage=coverage,
            diagnostics=ordered_diags,
            limitations=ordered_limits,
            fingerprint=fingerprint,
        )

    def is_compatible_with(self, other: KnowledgeIndexManifest) -> bool:
        """Return True when embedding identity and vector schema match."""

        left = self.embedding_identity
        right = other.embedding_identity
        return (
            left.provider_id == right.provider_id
            and left.model == right.model
            and left.model_version == right.model_version
            and left.dimension == right.dimension
            and self.vector_record_schema_version == other.vector_record_schema_version
        )


class KnowledgeIndexResult(BaseModel):
    """In-memory indexing outcome for one KnowledgeIndexer run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_name: str = KNOWLEDGE_INDEX_RESULT_SCHEMA_NAME
    schema_version: str = KNOWLEDGE_INDEX_RESULT_SCHEMA_VERSION
    status: KnowledgeIndexStatus
    manifest: KnowledgeIndexManifest
    indexed_record_ids: tuple[str, ...] = ()
    diagnostics: tuple[KnowledgeIndexDiagnostic, ...] = ()
    limitations: tuple[str, ...] = ()

    @field_validator("schema_name", "schema_version", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="index result field")

    @field_validator("indexed_record_ids", "diagnostics", "limitations", mode="before")
    @classmethod
    def normalize_sequences(cls, value: object) -> tuple[Any, ...]:
        return as_tuple(value)


def knowledge_index_manifest_payload(manifest: KnowledgeIndexManifest) -> dict[str, Any]:
    """Stable JSON payload for the index manifest artifact (no embeddings)."""

    return manifest.model_dump(mode="json")


def knowledge_index_result_payload(result: KnowledgeIndexResult) -> dict[str, Any]:
    """Stable JSON payload for indexing result summaries (no embeddings)."""

    return result.model_dump(mode="json")
