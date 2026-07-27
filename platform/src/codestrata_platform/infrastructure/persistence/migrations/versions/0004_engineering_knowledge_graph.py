"""Engineering Knowledge Graph PostgreSQL schema.

Revision ID: 0004_engineering_knowledge_graph
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_engineering_knowledge_graph"
down_revision: str | None = "0003_engineering_intelligence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "engineering_knowledge_graphs",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column("projection_id", sa.String(length=160), nullable=False),
        sa.Column(
            "organization_id",
            sa.String(length=160),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.String(length=160),
            sa.ForeignKey("workspaces.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "repository_id",
            sa.String(length=160),
            sa.ForeignKey("repositories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "assessment_id",
            sa.String(length=160),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "engineering_snapshot_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_snapshots.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("engineering_snapshot_version", sa.Integer(), nullable=False),
        sa.Column("intelligence_revision", sa.Integer(), nullable=False),
        sa.Column("graph_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("projection_key", sa.String(length=128), nullable=False),
        sa.Column("projection_schema_version", sa.String(length=64), nullable=False),
        sa.Column("projector_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("optimistic_version", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint(
            "projection_key",
            name="uq_engineering_knowledge_graphs_projection_key",
        ),
        sa.UniqueConstraint(
            "engineering_snapshot_id",
            "projector_version",
            "projection_schema_version",
            name="uq_engineering_knowledge_graphs_snapshot_projector",
        ),
    )
    op.create_index(
        "ix_engineering_knowledge_graphs_repository_id",
        "engineering_knowledge_graphs",
        ["repository_id"],
    )
    op.create_index(
        "ix_engineering_knowledge_graphs_snapshot_id",
        "engineering_knowledge_graphs",
        ["engineering_snapshot_id"],
    )
    op.create_index(
        "ix_engineering_knowledge_graphs_status",
        "engineering_knowledge_graphs",
        ["status"],
    )

    op.create_table(
        "engineering_graph_projections",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "graph_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_knowledge_graphs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("projection_key", sa.String(length=128), nullable=False),
        sa.Column("projection_schema_version", sa.String(length=64), nullable=False),
        sa.Column("projector_version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "projection_key",
            name="uq_engineering_graph_projections_projection_key",
        ),
    )
    op.create_index(
        "ix_engineering_graph_projections_graph_id",
        "engineering_graph_projections",
        ["graph_id"],
    )

    op.create_table(
        "engineering_graph_nodes",
        sa.Column("node_id", sa.String(length=256), primary_key=True),
        sa.Column(
            "graph_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_knowledge_graphs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("node_type", sa.String(length=64), nullable=False),
        sa.Column("canonical_type", sa.String(length=128), nullable=False),
        sa.Column("canonical_id", sa.String(length=256), nullable=False),
        sa.Column("display_name", sa.String(length=2000), nullable=False),
        sa.Column("properties_json", sa.JSON(), nullable=False),
        sa.Column("source_reference_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_engineering_graph_nodes_graph_type",
        "engineering_graph_nodes",
        ["graph_id", "node_type"],
    )
    op.create_index(
        "ix_engineering_graph_nodes_canonical",
        "engineering_graph_nodes",
        ["canonical_type", "canonical_id"],
    )

    op.create_table(
        "engineering_graph_edges",
        sa.Column("edge_id", sa.String(length=256), primary_key=True),
        sa.Column(
            "graph_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_knowledge_graphs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_node_id", sa.String(length=256), nullable=False),
        sa.Column("target_node_id", sa.String(length=256), nullable=False),
        sa.Column("edge_type", sa.String(length=128), nullable=False),
        sa.Column("properties_json", sa.JSON(), nullable=False),
        sa.Column("source_reference_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["graph_id", "source_node_id"],
            ["engineering_graph_nodes.graph_id", "engineering_graph_nodes.node_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["graph_id", "target_node_id"],
            ["engineering_graph_nodes.graph_id", "engineering_graph_nodes.node_id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_engineering_graph_edges_graph_type",
        "engineering_graph_edges",
        ["graph_id", "edge_type"],
    )
    op.create_index(
        "ix_engineering_graph_edges_source",
        "engineering_graph_edges",
        ["graph_id", "source_node_id"],
    )
    op.create_index(
        "ix_engineering_graph_edges_target",
        "engineering_graph_edges",
        ["graph_id", "target_node_id"],
    )


def downgrade() -> None:
    op.drop_table("engineering_graph_edges")
    op.drop_table("engineering_graph_nodes")
    op.drop_table("engineering_graph_projections")
    op.drop_table("engineering_knowledge_graphs")
