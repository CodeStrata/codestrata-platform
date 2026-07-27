"""Assessment intelligence PostgreSQL schema.

Revision ID: 0002_assessment_intelligence
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_assessment_intelligence"
down_revision: str | None = "0001_platform_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assessment_intelligence",
        sa.Column("id", sa.String(length=160), primary_key=True),
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
        sa.Column("engine_assessment_id", sa.String(length=160), nullable=False),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("parser_version", sa.String(length=64), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source_artifact_ids_json", sa.JSON(), nullable=False),
        sa.Column("findings_json", sa.JSON(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("recommendations_json", sa.JSON(), nullable=False),
        sa.Column("diagnostics_json", sa.JSON(), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("optimistic_version", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint(
            "assessment_id",
            "idempotency_key",
            name="uq_intelligence_assessment_idempotency",
        ),
    )
    op.create_index(
        "ix_assessment_intelligence_assessment_id",
        "assessment_intelligence",
        ["assessment_id"],
    )

    op.create_table(
        "intelligence_source_artifacts",
        sa.Column(
            "intelligence_id",
            sa.String(length=160),
            sa.ForeignKey("assessment_intelligence.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessment_id",
            sa.String(length=160),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("artifact_id", sa.String(length=160), nullable=False),
        sa.PrimaryKeyConstraint("intelligence_id", "artifact_id"),
        sa.UniqueConstraint(
            "intelligence_id",
            "artifact_id",
            name="uq_intelligence_source_artifacts_intelligence_artifact",
        ),
    )
    op.create_index(
        "ix_intelligence_source_artifacts_assessment_artifact",
        "intelligence_source_artifacts",
        ["assessment_id", "artifact_id"],
    )

    op.create_table(
        "findings",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.String(length=160),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "intelligence_id",
            sa.String(length=160),
            sa.ForeignKey("assessment_intelligence.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("rule_id", sa.String(length=256), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("production_scope", sa.String(length=512), nullable=True),
        sa.Column("affected_component", sa.String(length=512), nullable=True),
        sa.Column("affected_path_reference", sa.String(length=2048), nullable=True),
        sa.Column("remediation_reference", sa.String(length=2048), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "assessment_id",
            "id",
            name="uq_findings_assessment_finding_id",
        ),
    )

    op.create_table(
        "evidence_references",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "finding_id",
            sa.String(length=160),
            sa.ForeignKey("findings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessment_id",
            sa.String(length=160),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("path_reference", sa.String(length=2048), nullable=False),
        sa.Column("line_start", sa.Integer(), nullable=True),
        sa.Column("line_end", sa.Integer(), nullable=True),
        sa.Column("symbol", sa.String(length=512), nullable=True),
        sa.Column("component", sa.String(length=512), nullable=True),
        sa.Column("evidence_type", sa.String(length=128), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("redacted_excerpt", sa.Text(), nullable=True),
        sa.Column("source_artifact_id", sa.String(length=160), nullable=True),
    )

    op.create_table(
        "metrics",
        sa.Column("id", sa.String(length=320), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.String(length=160),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "intelligence_id",
            sa.String(length=160),
            sa.ForeignKey("assessment_intelligence.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("value_kind", sa.String(length=32), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=False),
        sa.Column("unit", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "assessment_id",
            "name",
            name="uq_metrics_assessment_name",
        ),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.String(length=160),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "intelligence_id",
            sa.String(length=160),
            sa.ForeignKey("assessment_intelligence.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("effort", sa.String(length=512), nullable=True),
        sa.Column("impact", sa.String(length=512), nullable=True),
        sa.Column("roadmap_horizon", sa.String(length=512), nullable=True),
        sa.Column("dependencies_json", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "assessment_id",
            "id",
            name="uq_recommendations_assessment_recommendation_id",
        ),
    )

    op.create_table(
        "recommendation_finding_links",
        sa.Column(
            "recommendation_id",
            sa.String(length=160),
            sa.ForeignKey("recommendations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("finding_id", sa.String(length=160), nullable=False),
        sa.Column(
            "assessment_id",
            sa.String(length=160),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("recommendation_id", "finding_id"),
    )


def downgrade() -> None:
    op.drop_table("recommendation_finding_links")
    op.drop_table("recommendations")
    op.drop_table("metrics")
    op.drop_table("evidence_references")
    op.drop_table("findings")
    op.drop_table("intelligence_source_artifacts")
    op.drop_table("assessment_intelligence")
