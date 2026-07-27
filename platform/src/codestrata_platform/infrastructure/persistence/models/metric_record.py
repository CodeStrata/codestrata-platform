"""Metric persistence record."""

from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from codestrata_platform.infrastructure.persistence.models.base import Base


class MetricRecord(Base):
    __tablename__ = "metrics"
    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "name",
            name="uq_metrics_assessment_name",
        ),
    )

    id: Mapped[str] = mapped_column(String(320), primary_key=True)
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
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    value_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    value_text: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
