"""Portfolio intelligence persistence records."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from codestrata_platform.infrastructure.persistence.models.base import Base


class EngineeringPortfolioRecord(Base):
    __tablename__ = "engineering_portfolios"
    __table_args__ = (
        Index("ix_engineering_portfolios_organization_id", "organization_id"),
        Index("ix_engineering_portfolios_workspace_id", "workspace_id"),
        Index("ix_engineering_portfolios_status", "status"),
    )

    portfolio_id: Mapped[str] = mapped_column(String(160), primary_key=True)
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
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    max_repositories: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    optimistic_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class EngineeringPortfolioMembershipRecord(Base):
    __tablename__ = "engineering_portfolio_memberships"
    __table_args__ = (
        # PostgreSQL treats NULLs as distinct in UNIQUE constraints, so active
        # uniqueness (removed_at IS NULL) is enforced via a partial unique index.
        Index(
            "uq_engineering_portfolio_memberships_active",
            "portfolio_id",
            "repository_id",
            unique=True,
            postgresql_where=text("removed_at IS NULL"),
        ),
        Index("ix_engineering_portfolio_memberships_portfolio_id", "portfolio_id"),
        Index("ix_engineering_portfolio_memberships_repository_id", "repository_id"),
    )

    membership_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_portfolios.portfolio_id", ondelete="CASCADE"),
        nullable=False,
    )
    repository_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("repositories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    criticality: Mapped[str] = mapped_column(String(32), nullable=False)
    business_capability: Mapped[str | None] = mapped_column(String(256), nullable=True)
    owner_reference: Mapped[str | None] = mapped_column(String(256), nullable=True)
    lifecycle_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tags: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EngineeringPortfolioSnapshotRecord(Base):
    __tablename__ = "engineering_portfolio_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "projection_key",
            name="uq_engineering_portfolio_snapshots_projection_key",
        ),
        Index("ix_engineering_portfolio_snapshots_portfolio_id", "portfolio_id"),
        Index("ix_engineering_portfolio_snapshots_status", "status"),
        Index("ix_engineering_portfolio_snapshots_organization_id", "organization_id"),
        Index("ix_engineering_portfolio_snapshots_workspace_id", "workspace_id"),
    )

    portfolio_snapshot_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_portfolios.portfolio_id", ondelete="RESTRICT"),
        nullable=False,
    )
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
    snapshot_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    projection_key: Mapped[str] = mapped_column(String(128), nullable=False)
    portfolio_schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregation_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    repository_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_repository_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unavailable_repository_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    optimistic_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class EngineeringPortfolioRepositorySnapshotRecord(Base):
    __tablename__ = "engineering_portfolio_repository_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_snapshot_id",
            "repository_id",
            name="uq_portfolio_repo_snapshot",
        ),
        Index(
            "ix_engineering_portfolio_repository_snapshots_repository_id",
            "repository_id",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    portfolio_snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_portfolio_snapshots.portfolio_snapshot_id", ondelete="CASCADE"),
        nullable=False,
    )
    repository_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("repositories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    assessment_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    engineering_snapshot_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    engineering_snapshot_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    knowledge_graph_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    knowledge_graph_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    availability_status: Mapped[str] = mapped_column(String(32), nullable=False)
    criticality: Mapped[str] = mapped_column(String(32), nullable=False)
    selected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    graph_intelligence_policy_version: Mapped[str | None] = mapped_column(String(64), nullable=True)


class EngineeringPortfolioTechnologyRecord(Base):
    __tablename__ = "engineering_portfolio_technologies"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_snapshot_id",
            "canonical_key",
            name="uq_portfolio_technology",
        ),
        Index(
            "ix_engineering_portfolio_technologies_canonical_key",
            "canonical_key",
        ),
    )

    technology_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    portfolio_snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_portfolio_snapshots.portfolio_snapshot_id", ondelete="CASCADE"),
        nullable=False,
    )
    canonical_key: Mapped[str] = mapped_column(String(128), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(256), nullable=False)
    framework: Mapped[str | None] = mapped_column(String(128), nullable=True)
    categories: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    repository_count: Mapped[int] = mapped_column(Integer, nullable=False)
    repository_references: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    component_count: Mapped[int] = mapped_column(Integer, nullable=False)
    finding_count: Mapped[int] = mapped_column(Integer, nullable=False)
    high_critical_finding_count: Mapped[int] = mapped_column(Integer, nullable=False)
    recommendation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    usage_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    production_usage_count: Mapped[int] = mapped_column(Integer, nullable=False)
    lifecycle_signal: Mapped[str] = mapped_column(String(32), nullable=False)
    standardization_status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_snapshot_references: Mapped[list[Any]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    usages: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)


class EngineeringPortfolioFindingRecord(Base):
    __tablename__ = "engineering_portfolio_findings"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_snapshot_id",
            "recurrence_key",
            name="uq_portfolio_finding",
        ),
        Index(
            "ix_engineering_portfolio_findings_recurrence_key",
            "recurrence_key",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    portfolio_snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_portfolio_snapshots.portfolio_snapshot_id", ondelete="CASCADE"),
        nullable=False,
    )
    recurrence_key: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_title_id: Mapped[str] = mapped_column(String(160), nullable=False)
    technology_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    repository_count: Mapped[int] = mapped_column(Integer, nullable=False)
    finding_count: Mapped[int] = mapped_column(Integer, nullable=False)
    affected_repositories: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    severity_distribution: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    production_count: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    source_references: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    summary_totals: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class EngineeringPortfolioRecommendationRecord(Base):
    __tablename__ = "engineering_portfolio_recommendations"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_snapshot_id",
            "recurrence_key",
            name="uq_portfolio_recommendation",
        ),
        Index(
            "ix_engineering_portfolio_recommendations_recurrence_key",
            "recurrence_key",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    portfolio_snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_portfolio_snapshots.portfolio_snapshot_id", ondelete="CASCADE"),
        nullable=False,
    )
    recurrence_key: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_recommendation_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    linked_finding_rule: Mapped[str | None] = mapped_column(String(160), nullable=True)
    target_technology: Mapped[str | None] = mapped_column(String(128), nullable=True)
    target_component: Mapped[str | None] = mapped_column(String(160), nullable=True)
    roadmap_horizon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    repository_count: Mapped[int] = mapped_column(Integer, nullable=False)
    recommendation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    affected_repositories: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    priority_score: Mapped[int] = mapped_column(Integer, nullable=False)
    priority_band: Mapped[str] = mapped_column(String(32), nullable=False)
    contributing_factors: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    source_references: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    coverage_gaps: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    summary_totals: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class EngineeringPortfolioRiskRecord(Base):
    __tablename__ = "engineering_portfolio_risks"
    __table_args__ = (
        Index("ix_engineering_portfolio_risks_severity", "overall_band"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    portfolio_snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_portfolio_snapshots.portfolio_snapshot_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_band: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    severity_distribution: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    concentrations: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    hotspots: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    repository_profiles: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    technology_profiles: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    systemic_risks: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)


class EngineeringPortfolioModernizationCandidateRecord(Base):
    __tablename__ = "engineering_portfolio_modernization_candidates"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_snapshot_id",
            "candidate_id",
            name="uq_portfolio_modernization_candidate",
        ),
        Index(
            "ix_engineering_portfolio_modernization_priority",
            "priority_score",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    portfolio_snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_portfolio_snapshots.portfolio_snapshot_id", ondelete="CASCADE"),
        nullable=False,
    )
    candidate_id: Mapped[str] = mapped_column(String(64), nullable=False)
    repository_id: Mapped[str] = mapped_column(String(160), nullable=False)
    theme: Mapped[str] = mapped_column(String(64), nullable=False)
    wave: Mapped[str] = mapped_column(String(32), nullable=False)
    priority_score: Mapped[int] = mapped_column(Integer, nullable=False)
    priority_band: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    affected_technologies: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    related_findings: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    related_recommendations: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    contributing_factors: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    wave_factors: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    evidence_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    source_snapshot_references: Mapped[list[Any]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    summary_meta: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class EngineeringPortfolioAnalysisRunRecord(Base):
    __tablename__ = "engineering_portfolio_analysis_runs"
    __table_args__ = (
        Index("ix_engineering_portfolio_analysis_runs_portfolio_id", "portfolio_id"),
        Index("ix_engineering_portfolio_analysis_runs_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_portfolios.portfolio_id", ondelete="CASCADE"),
        nullable=False,
    )
    portfolio_snapshot_id: Mapped[str | None] = mapped_column(
        String(160),
        ForeignKey("engineering_portfolio_snapshots.portfolio_snapshot_id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    aggregation_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnostics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
