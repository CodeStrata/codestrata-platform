"""Assessment persistence record."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from codestrata_platform.infrastructure.persistence.models.base import Base


class AssessmentRecord(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    repository_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("repositories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    engine_version: Mapped[str] = mapped_column(String(64), nullable=False)
    assessment_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    generated_reports_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    references_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    repository = relationship("RepositoryRecord", back_populates="assessments")
