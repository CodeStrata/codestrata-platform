"""Knowledge corpus aggregate (Phase 5.2)."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aimf.domain.graph.validation import as_tuple, optional_nonblank, require_nonblank
from aimf.domain.knowledge.identifiers import fingerprint_payload
from aimf.domain.knowledge.metadata import KnowledgeMetadata
from aimf.domain.knowledge.models import KnowledgeChunk, KnowledgeDocument
from aimf.domain.knowledge.schemas import (
    KNOWLEDGE_CORPUS_SCHEMA_NAME,
    KNOWLEDGE_CORPUS_SCHEMA_VERSION,
)


def build_corpus_id(*, repository_id: str, scan_id: str, fingerprint: str) -> str:
    """Deterministic corpus identity from isolation keys and content fingerprint."""

    repo = require_nonblank(repository_id, label="repository_id")
    scan = require_nonblank(scan_id, label="scan_id")
    fp = require_nonblank(fingerprint, label="fingerprint")
    material = f"knowledge-corpus\n{repo}\n{scan}\n{fp}"
    token = hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]
    return f"kcorp:{token}"


class KnowledgeDiagnostic(BaseModel):
    """One projection/chunking diagnostic or limitation note."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    message: str
    source_type: str | None = None
    source_id: str | None = None
    severity: str = "info"

    @field_validator("code", "message", "severity", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="diagnostic field")

    @field_validator("source_type", "source_id", mode="before")
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="diagnostic optional field")


class KnowledgeCorpusCoverage(BaseModel):
    """Counts of projected sources by kind."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document_count: int = Field(default=0, ge=0)
    chunk_count: int = Field(default=0, ge=0)
    by_source_type: dict[str, int] = Field(default_factory=dict)
    skipped_empty: int = Field(default=0, ge=0)
    skipped_disabled: int = Field(default=0, ge=0)
    skipped_unsupported: int = Field(default=0, ge=0)
    oversize_units: int = Field(default=0, ge=0)
    fallback_chunks: int = Field(default=0, ge=0)

    @field_validator("by_source_type", mode="before")
    @classmethod
    def normalize_counts(cls, value: object) -> dict[str, int]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise ValueError("by_source_type must be a mapping")
        return {
            str(key): int(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }


class KnowledgeCorpus(BaseModel):
    """In-memory projected knowledge documents and deterministic chunks."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    corpus_id: str
    schema_name: str = KNOWLEDGE_CORPUS_SCHEMA_NAME
    schema_version: str = KNOWLEDGE_CORPUS_SCHEMA_VERSION
    projection_schema_name: str = "knowledge-projection"
    projection_schema_version: str = "1.0.0"
    chunker_schema_name: str = "deterministic-chunker"
    chunker_schema_version: str = "1.0.0"
    documents: tuple[KnowledgeDocument, ...] = ()
    chunks: tuple[KnowledgeChunk, ...] = ()
    coverage: KnowledgeCorpusCoverage = Field(default_factory=KnowledgeCorpusCoverage)
    diagnostics: tuple[KnowledgeDiagnostic, ...] = ()
    limitations: tuple[str, ...] = ()
    metadata: KnowledgeMetadata = Field(default_factory=KnowledgeMetadata)
    fingerprint: str

    @field_validator(
        "corpus_id",
        "schema_name",
        "schema_version",
        "projection_schema_name",
        "projection_schema_version",
        "chunker_schema_name",
        "chunker_schema_version",
        "fingerprint",
        mode="before",
    )
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="corpus field")

    @field_validator("documents", "chunks", "diagnostics", "limitations", mode="before")
    @classmethod
    def normalize_sequences(cls, value: object) -> tuple[Any, ...]:
        return as_tuple(value)

    @classmethod
    def create(
        cls,
        *,
        documents: Sequence[KnowledgeDocument],
        chunks: Sequence[KnowledgeChunk],
        coverage: KnowledgeCorpusCoverage,
        diagnostics: Sequence[KnowledgeDiagnostic] = (),
        limitations: Sequence[str] = (),
        metadata: KnowledgeMetadata | None = None,
        projection_schema_version: str = "1.0.0",
        chunker_schema_version: str = "1.0.0",
    ) -> KnowledgeCorpus:
        """Build a corpus with stable ordering, fingerprint, and ID."""

        ordered_docs = tuple(
            sorted(
                documents,
                key=lambda item: (str(item.source_type), item.source_id, item.document_id),
            )
        )
        ordered_chunks = tuple(
            sorted(
                chunks,
                key=lambda item: (item.document_id, item.sequence, item.chunk_id),
            )
        )
        ordered_diags = tuple(
            sorted(
                diagnostics,
                key=lambda item: (
                    item.code,
                    item.source_type or "",
                    item.source_id or "",
                    item.message,
                ),
            )
        )
        ordered_limits = tuple(
            sorted({require_nonblank(item, label="limitation") for item in limitations})
        )
        meta = metadata or KnowledgeMetadata()
        fingerprint = fingerprint_payload(
            {
                "schema_name": KNOWLEDGE_CORPUS_SCHEMA_NAME,
                "schema_version": KNOWLEDGE_CORPUS_SCHEMA_VERSION,
                "documents": [doc.fingerprint for doc in ordered_docs],
                "chunks": [chunk.fingerprint for chunk in ordered_chunks],
                "coverage": coverage.model_dump(mode="json"),
                "diagnostics": [d.model_dump(mode="json") for d in ordered_diags],
                "limitations": list(ordered_limits),
                "metadata": meta.model_dump(mode="json"),
            }
        )
        repository_id = meta.repository_id or "unknown-repository"
        scan_id = meta.scan_id or "unknown-scan"
        corpus_id = build_corpus_id(
            repository_id=repository_id,
            scan_id=scan_id,
            fingerprint=fingerprint,
        )
        return cls(
            corpus_id=corpus_id,
            documents=ordered_docs,
            chunks=ordered_chunks,
            coverage=coverage,
            diagnostics=ordered_diags,
            limitations=ordered_limits,
            metadata=meta,
            fingerprint=fingerprint,
            projection_schema_version=projection_schema_version,
            chunker_schema_version=chunker_schema_version,
        )


def knowledge_corpus_payload(corpus: KnowledgeCorpus) -> dict[str, Any]:
    """Stable JSON-compatible corpus payload."""

    return corpus.model_dump(mode="json")
