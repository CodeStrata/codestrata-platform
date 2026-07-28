"""Executive Intelligence persistence records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from codestrata_platform.infrastructure.persistence.models.base import Base


class EngineeringExecutiveIntelligenceSnapshotRecord(Base):
    __tablename__ = "engineering_executive_intelligence_snapshots"
    __table_args__ = (
        # Only completed projections are unique so FAILED retries can rebuild.
        Index(
            "uq_engineering_executive_intelligence_projection_key_completed",
            "projection_key",
            unique=True,
            postgresql_where="status = 'completed'",
            sqlite_where="status = 'completed'",
        ),
        Index(
            "ix_engineering_executive_intelligence_portfolio_id",
            "portfolio_id",
        ),
        Index(
            "ix_engineering_executive_intelligence_status",
            "status",
        ),
        Index(
            "ix_engineering_executive_intelligence_organization_id",
            "organization_id",
        ),
        Index(
            "ix_engineering_executive_intelligence_workspace_id",
            "workspace_id",
        ),
        Index(
            "ix_engineering_executive_intelligence_snapshot_id",
            "portfolio_snapshot_id",
        ),
    )

    executive_intelligence_id: Mapped[str] = mapped_column(String(160), primary_key=True)
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
    portfolio_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_portfolios.portfolio_id", ondelete="RESTRICT"),
        nullable=False,
    )
    portfolio_snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_portfolio_snapshots.portfolio_snapshot_id", ondelete="RESTRICT"),
        nullable=False,
    )
    portfolio_snapshot_version: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    projection_key: Mapped[str] = mapped_column(String(128), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    limitations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    optimistic_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class EngineeringExecutiveMetricRecord(Base):
    __tablename__ = "engineering_executive_metrics"
    __table_args__ = (
        UniqueConstraint(
            "executive_intelligence_id",
            "key",
            name="uq_engineering_executive_metric_key",
        ),
        Index(
            "ix_engineering_executive_metrics_exec_intel_id",
            "executive_intelligence_id",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    executive_intelligence_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey(
            "engineering_executive_intelligence_snapshots.executive_intelligence_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_band: Mapped[str] = mapped_column(String(32), nullable=False)
    coverage: Mapped[float] = mapped_column(Float, nullable=False)
    inputs: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    calculation_rule: Mapped[str] = mapped_column(Text, nullable=False)
    limitations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    policy_version: Mapped[str] = mapped_column(String(64), nullable=False)


class EngineeringExecutiveFindingRecord(Base):
    __tablename__ = "engineering_executive_findings"
    __table_args__ = (
        Index(
            "ix_engineering_executive_findings_exec_intel_id",
            "executive_intelligence_id",
        ),
        Index(
            "ix_engineering_executive_findings_category",
            "category",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    executive_intelligence_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey(
            "engineering_executive_intelligence_snapshots.executive_intelligence_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity_band: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_band: Mapped[str] = mapped_column(String(32), nullable=False)
    affected_repository_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    source_references: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    evidence: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    policy_version: Mapped[str] = mapped_column(String(64), nullable=False)


class EngineeringExecutiveRecommendationRecord(Base):
    __tablename__ = "engineering_executive_recommendations"
    __table_args__ = (
        Index(
            "ix_engineering_executive_recommendations_exec_intel_id",
            "executive_intelligence_id",
        ),
        Index(
            "ix_engineering_executive_recommendations_theme",
            "theme",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    executive_intelligence_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey(
            "engineering_executive_intelligence_snapshots.executive_intelligence_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    theme: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    affected_repository_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_band: Mapped[str] = mapped_column(String(32), nullable=False)
    expected_impact: Mapped[str] = mapped_column(String(32), nullable=False)
    source_references: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    priority_score: Mapped[int] = mapped_column(Integer, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(64), nullable=False)


class EngineeringExecutiveObservationRecord(Base):
    __tablename__ = "engineering_executive_observations"
    __table_args__ = (
        UniqueConstraint(
            "executive_intelligence_id",
            "observation_key",
            name="uq_engineering_executive_observation_key",
        ),
        Index(
            "ix_engineering_executive_observations_exec_intel_id",
            "executive_intelligence_id",
        ),
    )

    id: Mapped[str] = mapped_column(String(200), primary_key=True)
    executive_intelligence_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey(
            "engineering_executive_intelligence_snapshots.executive_intelligence_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    observation_key: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    related_metric_keys: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    related_finding_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_band: Mapped[str] = mapped_column(String(32), nullable=False)


__all__ = [
    "EngineeringExecutiveFindingRecord",
    "EngineeringExecutiveIntelligenceSnapshotRecord",
    "EngineeringExecutiveMetricRecord",
    "EngineeringExecutiveObservationRecord",
    "EngineeringExecutiveRecommendationRecord",
]
