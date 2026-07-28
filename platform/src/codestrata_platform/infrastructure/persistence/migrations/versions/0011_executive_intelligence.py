"""Executive Intelligence persistence schema.

Revision ID: 0011_executive_intelligence
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_executive_intelligence"
down_revision: str | None = "0010_portfolio_answering"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "engineering_executive_intelligence_snapshots",
        sa.Column("executive_intelligence_id", sa.String(length=160), primary_key=True),
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
            "portfolio_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_portfolios.portfolio_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "portfolio_snapshot_id",
            sa.String(length=160),
            sa.ForeignKey(
                "engineering_portfolio_snapshots.portfolio_snapshot_id",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column("portfolio_snapshot_version", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("projection_key", sa.String(length=128), nullable=False),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("optimistic_version", sa.Integer(), nullable=False, server_default="0"),
    )
    # Completed projection keys are unique; FAILED rows may share a key so retries work.
    op.create_index(
        "uq_engineering_executive_intelligence_projection_key_completed",
        "engineering_executive_intelligence_snapshots",
        ["projection_key"],
        unique=True,
        postgresql_where=sa.text("status = 'completed'"),
    )
    op.create_index(
        "ix_engineering_executive_intelligence_portfolio_id",
        "engineering_executive_intelligence_snapshots",
        ["portfolio_id"],
    )
    op.create_index(
        "ix_engineering_executive_intelligence_status",
        "engineering_executive_intelligence_snapshots",
        ["status"],
    )
    op.create_index(
        "ix_engineering_executive_intelligence_organization_id",
        "engineering_executive_intelligence_snapshots",
        ["organization_id"],
    )
    op.create_index(
        "ix_engineering_executive_intelligence_workspace_id",
        "engineering_executive_intelligence_snapshots",
        ["workspace_id"],
    )
    op.create_index(
        "ix_engineering_executive_intelligence_snapshot_id",
        "engineering_executive_intelligence_snapshots",
        ["portfolio_snapshot_id"],
    )

    op.create_table(
        "engineering_executive_metrics",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "executive_intelligence_id",
            sa.String(length=160),
            sa.ForeignKey(
                "engineering_executive_intelligence_snapshots.executive_intelligence_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("confidence_band", sa.String(length=32), nullable=False),
        sa.Column("coverage", sa.Float(), nullable=False),
        sa.Column("inputs", sa.JSON(), nullable=False),
        sa.Column("calculation_rule", sa.Text(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.UniqueConstraint(
            "executive_intelligence_id",
            "key",
            name="uq_engineering_executive_metric_key",
        ),
    )
    op.create_index(
        "ix_engineering_executive_metrics_exec_intel_id",
        "engineering_executive_metrics",
        ["executive_intelligence_id"],
    )

    op.create_table(
        "engineering_executive_findings",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "executive_intelligence_id",
            sa.String(length=160),
            sa.ForeignKey(
                "engineering_executive_intelligence_snapshots.executive_intelligence_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("severity_band", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("confidence_band", sa.String(length=32), nullable=False),
        sa.Column("affected_repository_ids", sa.JSON(), nullable=False),
        sa.Column("source_references", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
    )
    op.create_index(
        "ix_engineering_executive_findings_exec_intel_id",
        "engineering_executive_findings",
        ["executive_intelligence_id"],
    )
    op.create_index(
        "ix_engineering_executive_findings_category",
        "engineering_executive_findings",
        ["category"],
    )

    op.create_table(
        "engineering_executive_recommendations",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "executive_intelligence_id",
            sa.String(length=160),
            sa.ForeignKey(
                "engineering_executive_intelligence_snapshots.executive_intelligence_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("theme", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("affected_repository_ids", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("confidence_band", sa.String(length=32), nullable=False),
        sa.Column("expected_impact", sa.String(length=32), nullable=False),
        sa.Column("source_references", sa.JSON(), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
    )
    op.create_index(
        "ix_engineering_executive_recommendations_exec_intel_id",
        "engineering_executive_recommendations",
        ["executive_intelligence_id"],
    )
    op.create_index(
        "ix_engineering_executive_recommendations_theme",
        "engineering_executive_recommendations",
        ["theme"],
    )

    op.create_table(
        "engineering_executive_observations",
        sa.Column("id", sa.String(length=200), primary_key=True),
        sa.Column(
            "executive_intelligence_id",
            sa.String(length=160),
            sa.ForeignKey(
                "engineering_executive_intelligence_snapshots.executive_intelligence_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("observation_key", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("related_metric_keys", sa.JSON(), nullable=False),
        sa.Column("related_finding_ids", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("confidence_band", sa.String(length=32), nullable=False),
        sa.UniqueConstraint(
            "executive_intelligence_id",
            "observation_key",
            name="uq_engineering_executive_observation_key",
        ),
    )
    op.create_index(
        "ix_engineering_executive_observations_exec_intel_id",
        "engineering_executive_observations",
        ["executive_intelligence_id"],
    )


def downgrade() -> None:
    op.drop_table("engineering_executive_observations")
    op.drop_table("engineering_executive_recommendations")
    op.drop_table("engineering_executive_findings")
    op.drop_table("engineering_executive_metrics")
    op.drop_table("engineering_executive_intelligence_snapshots")
