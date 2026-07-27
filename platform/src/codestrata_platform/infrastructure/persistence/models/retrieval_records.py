"""Engineering Retrieval Index persistence records."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from codestrata_platform.infrastructure.persistence.models.base import Base


class EngineeringRetrievalIndexRecord(Base):
    __tablename__ = "engineering_retrieval_indexes"
    __table_args__ = (
        UniqueConstraint(
            "projection_key",
            name="uq_engineering_retrieval_indexes_projection_key",
        ),
        Index("ix_engineering_retrieval_indexes_repository_id", "repository_id"),
        Index("ix_engineering_retrieval_indexes_snapshot_id", "engineering_snapshot_id"),
        Index("ix_engineering_retrieval_indexes_graph_id", "knowledge_graph_id"),
        Index("ix_engineering_retrieval_indexes_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    workspace_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False,
    )
    repository_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("repositories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    assessment_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assessments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    engineering_snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
    )
    engineering_snapshot_version: Mapped[int] = mapped_column(Integer, nullable=False)
    knowledge_graph_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_knowledge_graphs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    knowledge_graph_version: Mapped[int] = mapped_column(Integer, nullable=False)
    index_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    retrieval_schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    chunking_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding_provider_id: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding_model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    projection_key: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    optimistic_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class EngineeringRetrievalDocumentRecord(Base):
    __tablename__ = "engineering_retrieval_documents"
    __table_args__ = (
        UniqueConstraint(
            "index_id",
            "checksum",
            name="uq_engineering_retrieval_documents_index_checksum",
        ),
        Index("ix_engineering_retrieval_documents_index_id", "index_id"),
        Index("ix_engineering_retrieval_documents_content_type", "content_type"),
        Index(
            "ix_engineering_retrieval_documents_canonical",
            "canonical_type",
            "canonical_id",
        ),
        Index("ix_engineering_retrieval_documents_checksum", "checksum"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    index_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_retrieval_indexes.id", ondelete="CASCADE"),
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_type: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_id: Mapped[str] = mapped_column(String(160), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    structured_content: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    source_references: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    graph_node_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    graph_edge_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EngineeringRetrievalChunkRecord(Base):
    __tablename__ = "engineering_retrieval_chunks"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "checksum",
            name="uq_engineering_retrieval_chunks_document_checksum",
        ),
        Index("ix_engineering_retrieval_chunks_index_id", "index_id"),
        Index("ix_engineering_retrieval_chunks_document_id", "document_id"),
        Index("ix_engineering_retrieval_chunks_checksum", "checksum"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_retrieval_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    index_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_retrieval_indexes.id", ondelete="CASCADE"),
        nullable=False,
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_estimate: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    search_vector_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_references: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    graph_node_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    graph_edge_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EngineeringRetrievalIndexRunRecord(Base):
    __tablename__ = "engineering_retrieval_index_runs"
    __table_args__ = (
        Index("ix_engineering_retrieval_index_runs_index_id", "index_id"),
        Index("ix_engineering_retrieval_index_runs_projection_key", "projection_key"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    index_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_retrieval_indexes.id", ondelete="CASCADE"),
        nullable=False,
    )
    projection_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    document_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedded_chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnostics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
