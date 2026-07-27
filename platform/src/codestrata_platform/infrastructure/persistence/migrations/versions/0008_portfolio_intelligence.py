"""Portfolio intelligence persistence schema.

Revision ID: 0008_portfolio_intelligence
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_portfolio_intelligence"
down_revision: str | None = "0007_engineering_answering"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "engineering_portfolios",
        sa.Column("portfolio_id", sa.String(length=160), primary_key=True),
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
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("max_repositories", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("optimistic_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_engineering_portfolios_organization_id",
        "engineering_portfolios",
        ["organization_id"],
    )
    op.create_index(
        "ix_engineering_portfolios_workspace_id",
        "engineering_portfolios",
        ["workspace_id"],
    )
    op.create_index(
        "ix_engineering_portfolios_status",
        "engineering_portfolios",
        ["status"],
    )

    op.create_table(
        "engineering_portfolio_memberships",
        sa.Column("membership_id", sa.String(length=160), primary_key=True),
        sa.Column(
            "portfolio_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_portfolios.portfolio_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "repository_id",
            sa.String(length=160),
            sa.ForeignKey("repositories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("criticality", sa.String(length=32), nullable=False),
        sa.Column("business_capability", sa.String(length=256), nullable=True),
        sa.Column("owner_reference", sa.String(length=256), nullable=True),
        sa.Column("lifecycle_status", sa.String(length=64), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_engineering_portfolio_memberships_portfolio_id",
        "engineering_portfolio_memberships",
        ["portfolio_id"],
    )
    op.create_index(
        "ix_engineering_portfolio_memberships_repository_id",
        "engineering_portfolio_memberships",
        ["repository_id"],
    )
    # PostgreSQL treats NULLs as distinct in UNIQUE constraints; enforce active
    # uniqueness with a partial unique index instead.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_engineering_portfolio_memberships_active
        ON engineering_portfolio_memberships (portfolio_id, repository_id)
        WHERE removed_at IS NULL
        """
    )

    op.create_table(
        "engineering_portfolio_snapshots",
        sa.Column("portfolio_snapshot_id", sa.String(length=160), primary_key=True),
        sa.Column(
            "portfolio_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_portfolios.portfolio_id", ondelete="RESTRICT"),
            nullable=False,
        ),
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
        sa.Column("snapshot_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("projection_key", sa.String(length=128), nullable=False),
        sa.Column("portfolio_schema_version", sa.String(length=64), nullable=False),
        sa.Column("aggregation_policy_version", sa.String(length=64), nullable=False),
        sa.Column("repository_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "available_repository_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "unavailable_repository_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("optimistic_version", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint(
            "projection_key",
            name="uq_engineering_portfolio_snapshots_projection_key",
        ),
    )
    op.create_index(
        "ix_engineering_portfolio_snapshots_portfolio_id",
        "engineering_portfolio_snapshots",
        ["portfolio_id"],
    )
    op.create_index(
        "ix_engineering_portfolio_snapshots_status",
        "engineering_portfolio_snapshots",
        ["status"],
    )
    op.create_index(
        "ix_engineering_portfolio_snapshots_organization_id",
        "engineering_portfolio_snapshots",
        ["organization_id"],
    )
    op.create_index(
        "ix_engineering_portfolio_snapshots_workspace_id",
        "engineering_portfolio_snapshots",
        ["workspace_id"],
    )

    op.create_table(
        "engineering_portfolio_repository_snapshots",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "portfolio_snapshot_id",
            sa.String(length=160),
            sa.ForeignKey(
                "engineering_portfolio_snapshots.portfolio_snapshot_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "repository_id",
            sa.String(length=160),
            sa.ForeignKey("repositories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("assessment_id", sa.String(length=160), nullable=True),
        sa.Column("engineering_snapshot_id", sa.String(length=160), nullable=True),
        sa.Column("engineering_snapshot_version", sa.Integer(), nullable=True),
        sa.Column("knowledge_graph_id", sa.String(length=160), nullable=True),
        sa.Column("knowledge_graph_version", sa.Integer(), nullable=True),
        sa.Column("availability_status", sa.String(length=32), nullable=False),
        sa.Column("criticality", sa.String(length=32), nullable=False),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("graph_intelligence_policy_version", sa.String(length=64), nullable=True),
        sa.UniqueConstraint(
            "portfolio_snapshot_id",
            "repository_id",
            name="uq_portfolio_repo_snapshot",
        ),
    )
    op.create_index(
        "ix_engineering_portfolio_repository_snapshots_repository_id",
        "engineering_portfolio_repository_snapshots",
        ["repository_id"],
    )

    op.create_table(
        "engineering_portfolio_technologies",
        sa.Column("technology_id", sa.String(length=160), primary_key=True),
        sa.Column(
            "portfolio_snapshot_id",
            sa.String(length=160),
            sa.ForeignKey(
                "engineering_portfolio_snapshots.portfolio_snapshot_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("canonical_key", sa.String(length=128), nullable=False),
        sa.Column("normalized_name", sa.String(length=256), nullable=False),
        sa.Column("framework", sa.String(length=128), nullable=True),
        sa.Column("categories", sa.JSON(), nullable=False),
        sa.Column("repository_count", sa.Integer(), nullable=False),
        sa.Column("repository_references", sa.JSON(), nullable=False),
        sa.Column("component_count", sa.Integer(), nullable=False),
        sa.Column("finding_count", sa.Integer(), nullable=False),
        sa.Column("high_critical_finding_count", sa.Integer(), nullable=False),
        sa.Column("recommendation_count", sa.Integer(), nullable=False),
        sa.Column("usage_percentage", sa.Float(), nullable=False),
        sa.Column("production_usage_count", sa.Integer(), nullable=False),
        sa.Column("lifecycle_signal", sa.String(length=32), nullable=False),
        sa.Column("standardization_status", sa.String(length=32), nullable=False),
        sa.Column("source_snapshot_references", sa.JSON(), nullable=False),
        sa.Column("usages", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "portfolio_snapshot_id",
            "canonical_key",
            name="uq_portfolio_technology",
        ),
    )
    op.create_index(
        "ix_engineering_portfolio_technologies_canonical_key",
        "engineering_portfolio_technologies",
        ["canonical_key"],
    )

    op.create_table(
        "engineering_portfolio_findings",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "portfolio_snapshot_id",
            sa.String(length=160),
            sa.ForeignKey(
                "engineering_portfolio_snapshots.portfolio_snapshot_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("recurrence_key", sa.String(length=64), nullable=False),
        sa.Column("rule_id", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("normalized_title_id", sa.String(length=160), nullable=False),
        sa.Column("technology_key", sa.String(length=128), nullable=True),
        sa.Column("repository_count", sa.Integer(), nullable=False),
        sa.Column("finding_count", sa.Integer(), nullable=False),
        sa.Column("affected_repositories", sa.JSON(), nullable=False),
        sa.Column("severity_distribution", sa.JSON(), nullable=False),
        sa.Column("production_count", sa.Integer(), nullable=False),
        sa.Column("evidence_coverage", sa.Float(), nullable=False),
        sa.Column("recommendation_coverage", sa.Float(), nullable=False),
        sa.Column("source_references", sa.JSON(), nullable=False),
        sa.Column("summary_totals", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "portfolio_snapshot_id",
            "recurrence_key",
            name="uq_portfolio_finding",
        ),
    )
    op.create_index(
        "ix_engineering_portfolio_findings_recurrence_key",
        "engineering_portfolio_findings",
        ["recurrence_key"],
    )

    op.create_table(
        "engineering_portfolio_recommendations",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "portfolio_snapshot_id",
            sa.String(length=160),
            sa.ForeignKey(
                "engineering_portfolio_snapshots.portfolio_snapshot_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("recurrence_key", sa.String(length=64), nullable=False),
        sa.Column("canonical_recommendation_id", sa.String(length=160), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("linked_finding_rule", sa.String(length=160), nullable=True),
        sa.Column("target_technology", sa.String(length=128), nullable=True),
        sa.Column("target_component", sa.String(length=160), nullable=True),
        sa.Column("roadmap_horizon", sa.String(length=64), nullable=True),
        sa.Column("repository_count", sa.Integer(), nullable=False),
        sa.Column("recommendation_count", sa.Integer(), nullable=False),
        sa.Column("affected_repositories", sa.JSON(), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False),
        sa.Column("priority_band", sa.String(length=32), nullable=False),
        sa.Column("contributing_factors", sa.JSON(), nullable=False),
        sa.Column("source_references", sa.JSON(), nullable=False),
        sa.Column("coverage_gaps", sa.JSON(), nullable=False),
        sa.Column("summary_totals", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "portfolio_snapshot_id",
            "recurrence_key",
            name="uq_portfolio_recommendation",
        ),
    )
    op.create_index(
        "ix_engineering_portfolio_recommendations_recurrence_key",
        "engineering_portfolio_recommendations",
        ["recurrence_key"],
    )

    op.create_table(
        "engineering_portfolio_risks",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "portfolio_snapshot_id",
            sa.String(length=160),
            sa.ForeignKey(
                "engineering_portfolio_snapshots.portfolio_snapshot_id",
                ondelete="CASCADE",
            ),
            nullable=False,
            unique=True,
        ),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("overall_band", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("severity_distribution", sa.JSON(), nullable=False),
        sa.Column("concentrations", sa.JSON(), nullable=False),
        sa.Column("hotspots", sa.JSON(), nullable=False),
        sa.Column("repository_profiles", sa.JSON(), nullable=False),
        sa.Column("technology_profiles", sa.JSON(), nullable=False),
        sa.Column("systemic_risks", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_engineering_portfolio_risks_severity",
        "engineering_portfolio_risks",
        ["overall_band"],
    )

    op.create_table(
        "engineering_portfolio_modernization_candidates",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "portfolio_snapshot_id",
            sa.String(length=160),
            sa.ForeignKey(
                "engineering_portfolio_snapshots.portfolio_snapshot_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("candidate_id", sa.String(length=64), nullable=False),
        sa.Column("repository_id", sa.String(length=160), nullable=False),
        sa.Column("theme", sa.String(length=64), nullable=False),
        sa.Column("wave", sa.String(length=32), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False),
        sa.Column("priority_band", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("affected_technologies", sa.JSON(), nullable=False),
        sa.Column("related_findings", sa.JSON(), nullable=False),
        sa.Column("related_recommendations", sa.JSON(), nullable=False),
        sa.Column("contributing_factors", sa.JSON(), nullable=False),
        sa.Column("wave_factors", sa.JSON(), nullable=False),
        sa.Column("evidence_coverage", sa.Float(), nullable=False),
        sa.Column("source_snapshot_references", sa.JSON(), nullable=False),
        sa.Column("summary_meta", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "portfolio_snapshot_id",
            "candidate_id",
            name="uq_portfolio_modernization_candidate",
        ),
    )
    op.create_index(
        "ix_engineering_portfolio_modernization_priority",
        "engineering_portfolio_modernization_candidates",
        ["priority_score"],
    )

    op.create_table(
        "engineering_portfolio_analysis_runs",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "portfolio_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_portfolios.portfolio_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "portfolio_snapshot_id",
            sa.String(length=160),
            sa.ForeignKey(
                "engineering_portfolio_snapshots.portfolio_snapshot_id",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("aggregation_policy_version", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("diagnostics", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_engineering_portfolio_analysis_runs_portfolio_id",
        "engineering_portfolio_analysis_runs",
        ["portfolio_id"],
    )
    op.create_index(
        "ix_engineering_portfolio_analysis_runs_status",
        "engineering_portfolio_analysis_runs",
        ["status"],
    )


def downgrade() -> None:
    op.drop_table("engineering_portfolio_analysis_runs")
    op.drop_table("engineering_portfolio_modernization_candidates")
    op.drop_table("engineering_portfolio_risks")
    op.drop_table("engineering_portfolio_recommendations")
    op.drop_table("engineering_portfolio_findings")
    op.drop_table("engineering_portfolio_technologies")
    op.drop_table("engineering_portfolio_repository_snapshots")
    op.drop_table("engineering_portfolio_snapshots")
    op.execute("DROP INDEX IF EXISTS uq_engineering_portfolio_memberships_active")
    op.drop_table("engineering_portfolio_memberships")
    op.drop_table("engineering_portfolios")
