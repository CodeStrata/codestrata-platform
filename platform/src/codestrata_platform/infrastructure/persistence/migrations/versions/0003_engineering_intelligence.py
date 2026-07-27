"""Engineering intelligence PostgreSQL schema.

Revision ID: 0003_engineering_intelligence
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from codestrata_platform.domain.engineering.taxonomy import CANONICAL_TECHNOLOGIES

revision: str = "0003_engineering_intelligence"
down_revision: str | None = "0002_assessment_intelligence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "engineering_snapshots",
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
        sa.Column("assessment_intelligence_id", sa.String(length=160), nullable=False),
        sa.Column("assessment_revision", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source_artifact_ids_json", sa.JSON(), nullable=False),
        sa.Column("technologies_json", sa.JSON(), nullable=False),
        sa.Column("components_json", sa.JSON(), nullable=False),
        sa.Column("findings_json", sa.JSON(), nullable=False),
        sa.Column("recommendations_json", sa.JSON(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.Column("relationships_json", sa.JSON(), nullable=False),
        sa.Column("tags_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("optimistic_version", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint(
            "assessment_id",
            "assessment_intelligence_id",
            "assessment_revision",
            name="uq_engineering_snapshots_intelligence_revision",
        ),
        sa.UniqueConstraint(
            "assessment_id",
            "version",
            name="uq_engineering_snapshots_assessment_version",
        ),
    )
    op.create_index(
        "ix_engineering_snapshots_assessment_id",
        "engineering_snapshots",
        ["assessment_id"],
    )
    op.create_index(
        "ix_engineering_snapshots_status",
        "engineering_snapshots",
        ["status"],
    )

    op.create_table(
        "engineering_technologies",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "snapshot_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessment_id",
            sa.String(length=160),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("canonical_key", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=256), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "snapshot_id",
            "canonical_key",
            name="uq_engineering_technologies_snapshot_key",
        ),
    )

    op.create_table(
        "engineering_findings",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "snapshot_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessment_id",
            sa.String(length=160),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("source_finding_id", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=4000), nullable=False),
        sa.Column("summary", sa.String(length=4000), nullable=False),
        sa.Column("rule_id", sa.String(length=256), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "snapshot_id",
            "source_finding_id",
            name="uq_engineering_findings_snapshot_source",
        ),
    )

    op.create_table(
        "engineering_recommendations",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "snapshot_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessment_id",
            sa.String(length=160),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("source_recommendation_id", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=4000), nullable=False),
        sa.Column("rationale", sa.String(length=4000), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("related_finding_ids_json", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "snapshot_id",
            "source_recommendation_id",
            name="uq_engineering_recommendations_snapshot_source",
        ),
    )

    op.create_table(
        "engineering_metrics",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "snapshot_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessment_id",
            sa.String(length=160),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("value", sa.String(length=4000), nullable=False),
        sa.Column("unit", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "snapshot_id",
            "name",
            name="uq_engineering_metrics_snapshot_name",
        ),
    )

    op.create_table(
        "engineering_evidence",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "snapshot_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessment_id",
            sa.String(length=160),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("reference", sa.String(length=2048), nullable=False),
        sa.Column("line_start", sa.Integer(), nullable=True),
        sa.Column("line_end", sa.Integer(), nullable=True),
        sa.Column("symbol", sa.String(length=512), nullable=True),
        sa.Column("source_artifact_id", sa.String(length=160), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )

    op.create_table(
        "engineering_relationships",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "snapshot_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessment_id",
            sa.String(length=160),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("relationship_type", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=160), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=160), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )

    op.create_table(
        "engineering_tags",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "snapshot_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessment_id",
            sa.String(length=160),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.UniqueConstraint(
            "snapshot_id",
            "name",
            name="uq_engineering_tags_snapshot_name",
        ),
    )

    op.create_table(
        "engineering_components",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "snapshot_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_snapshots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessment_id",
            sa.String(length=160),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("path_reference", sa.String(length=2048), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "snapshot_id",
            "name",
            name="uq_engineering_components_snapshot_name",
        ),
    )

    op.create_table(
        "engineering_taxonomy",
        sa.Column("canonical_key", sa.String(length=128), primary_key=True),
        sa.Column("display_name", sa.String(length=256), nullable=False),
        sa.Column("aliases_json", sa.JSON(), nullable=False),
    )

    taxonomy_table = sa.table(
        "engineering_taxonomy",
        sa.column("canonical_key", sa.String),
        sa.column("display_name", sa.String),
        sa.column("aliases_json", sa.JSON),
    )
    op.bulk_insert(
        taxonomy_table,
        [
            {
                "canonical_key": key,
                "display_name": display_name,
                "aliases_json": [],
            }
            for key, display_name in sorted(CANONICAL_TECHNOLOGIES.items())
        ],
    )


def downgrade() -> None:
    op.drop_table("engineering_components")
    op.drop_table("engineering_tags")
    op.drop_table("engineering_relationships")
    op.drop_table("engineering_evidence")
    op.drop_table("engineering_metrics")
    op.drop_table("engineering_recommendations")
    op.drop_table("engineering_findings")
    op.drop_table("engineering_technologies")
    op.drop_table("engineering_snapshots")
    op.drop_table("engineering_taxonomy")
