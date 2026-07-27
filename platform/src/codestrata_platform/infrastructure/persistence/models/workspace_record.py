"""Workspace persistence record."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from codestrata_platform.infrastructure.persistence.models.base import Base


class WorkspaceRecord(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    organization = relationship("OrganizationRecord", back_populates="workspaces")
    repositories = relationship("RepositoryRecord", back_populates="workspace")
