"""Assessment intelligence persistence record."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from codestrata_platform.infrastructure.persistence.models.base import Base


class AssessmentIntelligenceRecord(Base):
    __tablename__ = "assessment_intelligence"
    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "idempotency_key",
            name="uq_intelligence_assessment_idempotency",
        ),
        Index("ix_assessment_intelligence_assessment_id", "assessment_id"),
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
    engine_assessment_id: Mapped[str] = mapped_column(String(160), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(64), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_artifact_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    findings_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    metrics_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    recommendations_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    diagnostics_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    optimistic_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
