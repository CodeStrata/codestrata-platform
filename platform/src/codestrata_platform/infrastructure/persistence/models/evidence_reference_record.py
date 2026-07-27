"""Evidence reference persistence record."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from codestrata_platform.infrastructure.persistence.models.base import Base


class EvidenceReferenceRecord(Base):
    __tablename__ = "evidence_references"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    finding_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("findings.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessment_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assessments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    path_reference: Mapped[str] = mapped_column(String(2048), nullable=False)
    line_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    symbol: Mapped[str | None] = mapped_column(String(512), nullable=True)
    component: Mapped[str | None] = mapped_column(String(512), nullable=True)
    evidence_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    redacted_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_artifact_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
