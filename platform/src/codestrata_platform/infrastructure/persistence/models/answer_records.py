"""Engineering answering persistence records."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from codestrata_platform.infrastructure.persistence.models.base import Base


class EngineeringAnswerRunRecord(Base):
    __tablename__ = "engineering_answer_runs"
    __table_args__ = (
        UniqueConstraint(
            "projection_key",
            name="uq_engineering_answer_runs_projection_key",
        ),
        Index("ix_engineering_answer_runs_repository_id", "repository_id"),
        Index("ix_engineering_answer_runs_retrieval_index_id", "retrieval_index_id"),
        Index("ix_engineering_answer_runs_status", "status"),
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
    assessment_id: Mapped[str | None] = mapped_column(
        String(160),
        ForeignKey("assessments.id", ondelete="RESTRICT"),
        nullable=True,
    )
    retrieval_index_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_retrieval_indexes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    retrieval_index_version: Mapped[int] = mapped_column(Integer, nullable=False)
    engineering_snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
    )
    knowledge_graph_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_knowledge_graphs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    question_type: Mapped[str] = mapped_column(String(64), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_question_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    projection_key: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_id: Mapped[str] = mapped_column(String(64), nullable=False)
    model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_template_version: Mapped[str] = mapped_column(String(64), nullable=False)
    answer_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    grounding_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    follow_up_questions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    diagnostics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    usage_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    provider_request_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    optimistic_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class EngineeringAnswerCitationRecord(Base):
    __tablename__ = "engineering_answer_citations"
    __table_args__ = (Index("ix_engineering_answer_citations_answer_run_id", "answer_run_id"),)

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    answer_run_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_answer_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(32), nullable=False)
    retrieval_document_id: Mapped[str] = mapped_column(String(160), nullable=False)
    retrieval_chunk_id: Mapped[str] = mapped_column(String(160), nullable=False)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_type: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_id: Mapped[str] = mapped_column(String(160), nullable=False)
    source_references: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    graph_node_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    graph_edge_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    retrieval_score: Mapped[float] = mapped_column(Float, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EngineeringAnswerFeedbackRecord(Base):
    __tablename__ = "engineering_answer_feedback"
    __table_args__ = (Index("ix_engineering_answer_feedback_answer_run_id", "answer_run_id"),)

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    answer_run_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_answer_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback_category: Mapped[str] = mapped_column(String(64), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
