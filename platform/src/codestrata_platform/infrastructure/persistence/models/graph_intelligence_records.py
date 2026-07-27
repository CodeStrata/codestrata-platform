"""ORM records for graph intelligence analysis cache."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from codestrata_platform.infrastructure.persistence.models.base import Base


class GraphIntelligenceRunRecord(Base):
    __tablename__ = "graph_intelligence_runs"
    __table_args__ = (
        UniqueConstraint("analysis_key", name="uq_graph_intelligence_runs_analysis_key"),
        Index("ix_graph_intelligence_runs_graph_id", "graph_id"),
        Index("ix_graph_intelligence_runs_analysis_type", "analysis_type"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    graph_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_knowledge_graphs.id", ondelete="CASCADE"),
        nullable=False,
    )
    analysis_type: Mapped[str] = mapped_column(String(64), nullable=False)
    analysis_key: Mapped[str] = mapped_column(String(128), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    result_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    diagnostics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class GraphIntegrityResultRecord(Base):
    __tablename__ = "graph_integrity_results"
    __table_args__ = (
        UniqueConstraint(
            "graph_id",
            "integrity_version",
            name="uq_graph_integrity_results_graph_version",
        ),
        Index("ix_graph_integrity_results_graph_id", "graph_id"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    graph_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_knowledge_graphs.id", ondelete="CASCADE"),
        nullable=False,
    )
    integrity_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    issue_count: Mapped[int] = mapped_column(Integer, nullable=False)
    critical_issue_count: Mapped[int] = mapped_column(Integer, nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
