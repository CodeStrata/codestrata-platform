"""Graph intelligence analysis persistence schema.

Revision ID: 0005_graph_intelligence_analysis
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_graph_intelligence_analysis"
down_revision: str | None = "0004_engineering_knowledge_graph"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "graph_intelligence_runs",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "graph_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_knowledge_graphs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("analysis_type", sa.String(length=64), nullable=False),
        sa.Column("analysis_key", sa.String(length=128), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result_summary", sa.JSON(), nullable=False),
        sa.Column("diagnostics", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.UniqueConstraint("analysis_key", name="uq_graph_intelligence_runs_analysis_key"),
    )
    op.create_index(
        "ix_graph_intelligence_runs_graph_id",
        "graph_intelligence_runs",
        ["graph_id"],
    )
    op.create_index(
        "ix_graph_intelligence_runs_analysis_type",
        "graph_intelligence_runs",
        ["analysis_type"],
    )

    op.create_table(
        "graph_integrity_results",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "graph_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_knowledge_graphs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("integrity_version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("issue_count", sa.Integer(), nullable=False),
        sa.Column("critical_issue_count", sa.Integer(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "graph_id",
            "integrity_version",
            name="uq_graph_integrity_results_graph_version",
        ),
    )
    op.create_index(
        "ix_graph_integrity_results_graph_id",
        "graph_integrity_results",
        ["graph_id"],
    )


def downgrade() -> None:
    op.drop_table("graph_integrity_results")
    op.drop_table("graph_intelligence_runs")
