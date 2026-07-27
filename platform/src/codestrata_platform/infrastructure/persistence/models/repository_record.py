"""Repository persistence record."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from codestrata_platform.infrastructure.persistence.models.base import Base


class RepositoryRecord(Base):
    __tablename__ = "repositories"
    __table_args__ = (
        # Partial unique index: active repositories only, so archived URLs may be re-registered.
        Index(
            "uq_repositories_workspace_normalized_url_active",
            "workspace_id",
            "normalized_url",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(512), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    repository_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    normalized_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(256), nullable=False)
    visibility: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    workspace = relationship("WorkspaceRecord", back_populates="repositories")
    assessments = relationship("AssessmentRecord", back_populates="repository")
