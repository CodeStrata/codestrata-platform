"""Finding persistence record."""

from __future__ import annotations

from sqlalchemy import JSON, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from codestrata_platform.infrastructure.persistence.models.base import Base


class FindingRecord(Base):
    __tablename__ = "findings"
    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "id",
            name="uq_findings_assessment_finding_id",
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
    rule_id: Mapped[str] = mapped_column(String(256), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    production_scope: Mapped[str | None] = mapped_column(String(512), nullable=True)
    affected_component: Mapped[str | None] = mapped_column(String(512), nullable=True)
    affected_path_reference: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    remediation_reference: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
