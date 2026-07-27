"""Intelligence source artifact link persistence record."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from codestrata_platform.infrastructure.persistence.models.base import Base


class IntelligenceSourceArtifactRecord(Base):
    __tablename__ = "intelligence_source_artifacts"
    __table_args__ = (
        UniqueConstraint(
            "intelligence_id",
            "artifact_id",
            name="uq_intelligence_source_artifacts_intelligence_artifact",
        ),
        Index(
            "ix_intelligence_source_artifacts_assessment_artifact",
            "assessment_id",
            "artifact_id",
        ),
    )

    intelligence_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assessment_intelligence.id", ondelete="CASCADE"),
        primary_key=True,
    )
    assessment_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assessments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    artifact_id: Mapped[str] = mapped_column(String(160), primary_key=True)
