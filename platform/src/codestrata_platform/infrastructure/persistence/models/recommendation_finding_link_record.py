"""Recommendation-to-finding link persistence record."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from codestrata_platform.infrastructure.persistence.models.base import Base


class RecommendationFindingLinkRecord(Base):
    __tablename__ = "recommendation_finding_links"

    recommendation_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    finding_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    assessment_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assessments.id", ondelete="RESTRICT"),
        nullable=False,
    )
