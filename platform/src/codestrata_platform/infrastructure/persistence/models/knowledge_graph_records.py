"""Engineering Knowledge Graph persistence records."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from codestrata_platform.infrastructure.persistence.models.base import Base


class EngineeringKnowledgeGraphRecord(Base):
    __tablename__ = "engineering_knowledge_graphs"
    __table_args__ = (
        UniqueConstraint(
            "projection_key",
            name="uq_engineering_knowledge_graphs_projection_key",
        ),
        UniqueConstraint(
            "engineering_snapshot_id",
            "projector_version",
            "projection_schema_version",
            name="uq_engineering_knowledge_graphs_snapshot_projector",
        ),
        Index("ix_engineering_knowledge_graphs_repository_id", "repository_id"),
        Index("ix_engineering_knowledge_graphs_snapshot_id", "engineering_snapshot_id"),
        Index("ix_engineering_knowledge_graphs_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    projection_id: Mapped[str] = mapped_column(String(160), nullable=False)
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
    engineering_snapshot_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
    )
    engineering_snapshot_version: Mapped[int] = mapped_column(Integer, nullable=False)
    intelligence_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    graph_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    projection_key: Mapped[str] = mapped_column(String(128), nullable=False)
    projection_schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    projector_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    optimistic_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class EngineeringGraphProjectionRecord(Base):
    __tablename__ = "engineering_graph_projections"
    __table_args__ = (
        UniqueConstraint(
            "projection_key",
            name="uq_engineering_graph_projections_projection_key",
        ),
        Index("ix_engineering_graph_projections_graph_id", "graph_id"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    graph_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_knowledge_graphs.id", ondelete="CASCADE"),
        nullable=False,
    )
    projection_key: Mapped[str] = mapped_column(String(128), nullable=False)
    projection_schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    projector_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EngineeringGraphNodeRecord(Base):
    __tablename__ = "engineering_graph_nodes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["graph_id"],
            ["engineering_knowledge_graphs.id"],
            ondelete="CASCADE",
        ),
        Index("ix_engineering_graph_nodes_graph_type", "graph_id", "node_type"),
        Index(
            "ix_engineering_graph_nodes_canonical",
            "canonical_type",
            "canonical_id",
        ),
    )

    node_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    graph_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    node_type: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_type: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_id: Mapped[str] = mapped_column(String(256), nullable=False)
    display_name: Mapped[str] = mapped_column(String(2000), nullable=False)
    properties_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    source_reference_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EngineeringGraphEdgeRecord(Base):
    __tablename__ = "engineering_graph_edges"
    __table_args__ = (
        ForeignKeyConstraint(
            ["graph_id", "source_node_id"],
            ["engineering_graph_nodes.graph_id", "engineering_graph_nodes.node_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["graph_id", "target_node_id"],
            ["engineering_graph_nodes.graph_id", "engineering_graph_nodes.node_id"],
            ondelete="CASCADE",
        ),
        Index("ix_engineering_graph_edges_graph_type", "graph_id", "edge_type"),
        Index("ix_engineering_graph_edges_source", "graph_id", "source_node_id"),
        Index("ix_engineering_graph_edges_target", "graph_id", "target_node_id"),
    )

    edge_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    graph_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("engineering_knowledge_graphs.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_node_id: Mapped[str] = mapped_column(String(256), nullable=False)
    target_node_id: Mapped[str] = mapped_column(String(256), nullable=False)
    edge_type: Mapped[str] = mapped_column(String(128), nullable=False)
    properties_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    source_reference_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
