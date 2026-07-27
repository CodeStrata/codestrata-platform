"""Engineering snapshot persistence record."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from codestrata_platform.infrastructure.persistence.models.base import Base


class EngineeringSnapshotRecord(Base):
    __tablename__ = "engineering_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "assessment_intelligence_id",
            "assessment_revision",
            name="uq_engineering_snapshots_intelligence_revision",
        ),
        UniqueConstraint(
            "assessment_id",
            "version",
            name="uq_engineering_snapshots_assessment_version",
        ),
        Index("ix_engineering_snapshots_assessment_id", "assessment_id"),
        Index("ix_engineering_snapshots_status", "status"),
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
    assessment_intelligence_id: Mapped[str] = mapped_column(String(160), nullable=False)
    assessment_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_artifact_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    technologies_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    components_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    findings_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    recommendations_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    metrics_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    evidence_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    relationships_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    tags_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    optimistic_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class EngineeringTechnologyRecord(Base):
    __tablename__ = "engineering_technologies"
    __table_args__ = (
        UniqueConstraint(
            "snapshot_id",
            "canonical_key",
            name="uq_engineering_technologies_snapshot_key",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessment_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assessments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    canonical_key: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)


class EngineeringFindingRecord(Base):
    __tablename__ = "engineering_findings"
    __table_args__ = (
        UniqueConstraint(
            "snapshot_id",
            "source_finding_id",
            name="uq_engineering_findings_snapshot_source",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessment_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assessments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_finding_id: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(4000), nullable=False)
    summary: Mapped[str] = mapped_column(String(4000), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(256), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class EngineeringRecommendationRecord(Base):
    __tablename__ = "engineering_recommendations"
    __table_args__ = (
        UniqueConstraint(
            "snapshot_id",
            "source_recommendation_id",
            name="uq_engineering_recommendations_snapshot_source",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessment_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assessments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_recommendation_id: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(4000), nullable=False)
    rationale: Mapped[str] = mapped_column(String(4000), nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    related_finding_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)


class EngineeringMetricRecord(Base):
    __tablename__ = "engineering_metrics"
    __table_args__ = (
        UniqueConstraint(
            "snapshot_id",
            "name",
            name="uq_engineering_metrics_snapshot_name",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessment_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assessments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[str] = mapped_column(String(4000), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)


class EngineeringEvidenceRecord(Base):
    __tablename__ = "engineering_evidence"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessment_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assessments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    reference: Mapped[str] = mapped_column(String(2048), nullable=False)
    line_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    symbol: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_artifact_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)


class EngineeringRelationshipRecord(Base):
    __tablename__ = "engineering_relationships"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessment_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assessments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(160), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str] = mapped_column(String(160), nullable=False)
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)


class EngineeringTagRecord(Base):
    __tablename__ = "engineering_tags"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "name", name="uq_engineering_tags_snapshot_name"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessment_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assessments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)


class EngineeringComponentRecord(Base):
    __tablename__ = "engineering_components"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "name", name="uq_engineering_components_snapshot_name"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessment_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assessments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    path_reference: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)


class EngineeringTaxonomyRecord(Base):
    __tablename__ = "engineering_taxonomy"

    canonical_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    aliases_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
