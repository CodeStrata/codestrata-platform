"""Recommendation persistence record."""

from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from codestrata_platform.infrastructure.persistence.models.base import Base


class RecommendationRecord(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "id",
            name="uq_recommendations_assessment_recommendation_id",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    assessment_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assessments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    intelligence_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assessment_intelligence.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    effort: Mapped[str | None] = mapped_column(String(512), nullable=True)
    impact: Mapped[str | None] = mapped_column(String(512), nullable=True)
    roadmap_horizon: Mapped[str | None] = mapped_column(String(512), nullable=True)
    dependencies_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
