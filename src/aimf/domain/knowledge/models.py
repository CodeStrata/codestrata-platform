"""Canonical knowledge document and chunk models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aimf.domain.graph.validation import require_nonblank
from aimf.domain.knowledge.enums import KnowledgeSourceType
from aimf.domain.knowledge.identifiers import (
    build_chunk_id,
    build_document_id,
    content_hash,
    fingerprint_payload,
)
from aimf.domain.knowledge.metadata import KnowledgeMetadata, KnowledgeTraceability
from aimf.domain.knowledge.schemas import (
    KNOWLEDGE_CHUNK_SCHEMA_NAME,
    KNOWLEDGE_CHUNK_SCHEMA_VERSION,
    KNOWLEDGE_DOCUMENT_SCHEMA_NAME,
    KNOWLEDGE_DOCUMENT_SCHEMA_VERSION,
)


class KnowledgeDocument(BaseModel):
    """Canonical knowledge document produced from assessment/report artifacts.

    This phase defines the contract only. Document construction from repositories,
    chunking, embeddings, and indexing are deferred.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    document_id: str
    schema_name: str = KNOWLEDGE_DOCUMENT_SCHEMA_NAME
    schema_version: str = KNOWLEDGE_DOCUMENT_SCHEMA_VERSION
    source_type: KnowledgeSourceType
    source_id: str
    title: str
    content: str
    metadata: KnowledgeMetadata = Field(default_factory=KnowledgeMetadata)
    traceability: KnowledgeTraceability
    fingerprint: str

    @field_validator(
        "document_id",
        "schema_name",
        "schema_version",
        "source_id",
        "title",
        "content",
        "fingerprint",
        mode="before",
    )
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="knowledge document field")

    @classmethod
    def create(
        cls,
        *,
        source_type: KnowledgeSourceType,
        source_id: str,
        title: str,
        content: str,
        traceability: KnowledgeTraceability,
        metadata: KnowledgeMetadata | None = None,
        schema_name: str = KNOWLEDGE_DOCUMENT_SCHEMA_NAME,
        schema_version: str = KNOWLEDGE_DOCUMENT_SCHEMA_VERSION,
    ) -> KnowledgeDocument:
        """Construct a document with deterministic ID and fingerprint."""

        meta = metadata or KnowledgeMetadata()
        digest = content_hash(content)
        document_id = build_document_id(
            source_type=str(source_type),
            source_id=source_id,
            content_digest=digest,
        )
        fingerprint = fingerprint_payload(
            {
                "schema_name": schema_name,
                "schema_version": schema_version,
                "source_type": str(source_type),
                "source_id": source_id,
                "title": title,
                "content": content,
                "metadata": meta.model_dump(mode="json"),
                "traceability": traceability.model_dump(mode="json"),
            }
        )
        return cls(
            document_id=document_id,
            schema_name=schema_name,
            schema_version=schema_version,
            source_type=source_type,
            source_id=source_id,
            title=title,
            content=content,
            metadata=meta,
            traceability=traceability,
            fingerprint=fingerprint,
        )


class KnowledgeChunk(BaseModel):
    """Bounded slice of a knowledge document for future indexing.

    Chunk generation is out of scope for this phase; the model exists so later
    indexing/retrieval can consume a stable contract.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_id: str
    document_id: str
    schema_name: str = KNOWLEDGE_CHUNK_SCHEMA_NAME
    schema_version: str = KNOWLEDGE_CHUNK_SCHEMA_VERSION
    sequence: int
    content: str
    token_count: int | None = None
    char_count: int | None = None
    byte_count: int | None = None
    metadata: KnowledgeMetadata = Field(default_factory=KnowledgeMetadata)
    traceability: KnowledgeTraceability
    fingerprint: str

    @field_validator(
        "chunk_id",
        "document_id",
        "schema_name",
        "schema_version",
        "content",
        "fingerprint",
        mode="before",
    )
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="knowledge chunk field")

    @field_validator("sequence")
    @classmethod
    def validate_sequence(cls, value: int) -> int:
        if value < 0:
            raise ValueError("sequence must be non-negative")
        return value

    @field_validator("token_count", "char_count", "byte_count")
    @classmethod
    def validate_nonnegative_size(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 0:
            raise ValueError("size metadata must be non-negative")
        return value

    @model_validator(mode="after")
    def default_char_count(self) -> KnowledgeChunk:
        if self.char_count is None:
            object.__setattr__(self, "char_count", len(self.content))
        if self.byte_count is None:
            object.__setattr__(self, "byte_count", len(self.content.encode("utf-8")))
        return self

    @classmethod
    def create(
        cls,
        *,
        document_id: str,
        sequence: int,
        content: str,
        traceability: KnowledgeTraceability,
        metadata: KnowledgeMetadata | None = None,
        token_count: int | None = None,
        char_count: int | None = None,
        byte_count: int | None = None,
        schema_name: str = KNOWLEDGE_CHUNK_SCHEMA_NAME,
        schema_version: str = KNOWLEDGE_CHUNK_SCHEMA_VERSION,
    ) -> KnowledgeChunk:
        """Construct a chunk with deterministic ID and fingerprint."""

        meta = metadata or KnowledgeMetadata()
        digest = content_hash(content)
        chunk_id = build_chunk_id(
            document_id=document_id,
            sequence=sequence,
            content_digest=digest,
        )
        resolved_char = char_count if char_count is not None else len(content)
        resolved_byte = byte_count if byte_count is not None else len(content.encode("utf-8"))
        fingerprint = fingerprint_payload(
            {
                "schema_name": schema_name,
                "schema_version": schema_version,
                "document_id": document_id,
                "sequence": sequence,
                "content": content,
                "token_count": token_count,
                "char_count": resolved_char,
                "byte_count": resolved_byte,
                "metadata": meta.model_dump(mode="json"),
                "traceability": traceability.model_dump(mode="json"),
            }
        )
        return cls(
            chunk_id=chunk_id,
            document_id=document_id,
            schema_name=schema_name,
            schema_version=schema_version,
            sequence=sequence,
            content=content,
            token_count=token_count,
            char_count=resolved_char,
            byte_count=resolved_byte,
            metadata=meta,
            traceability=traceability,
            fingerprint=fingerprint,
        )


def knowledge_document_payload(document: KnowledgeDocument) -> dict[str, Any]:
    """Stable JSON-compatible payload for a knowledge document."""

    return document.model_dump(mode="json")


def knowledge_chunk_payload(chunk: KnowledgeChunk) -> dict[str, Any]:
    """Stable JSON-compatible payload for a knowledge chunk."""

    return chunk.model_dump(mode="json")
