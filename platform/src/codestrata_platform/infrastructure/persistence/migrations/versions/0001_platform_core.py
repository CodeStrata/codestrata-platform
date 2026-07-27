"""Initial Commercial Platform PostgreSQL schema.

Revision ID: 0001_platform_core
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_platform_core"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "organization_id",
            sa.String(length=160),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_workspaces_organization_id", "workspaces", ["organization_id"])

    op.create_table(
        "repositories",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.String(length=160),
            sa.ForeignKey("workspaces.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            sa.String(length=160),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("display_name", sa.String(length=512), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("repository_url", sa.String(length=2048), nullable=False),
        sa.Column("normalized_url", sa.String(length=2048), nullable=False),
        sa.Column("default_branch", sa.String(length=256), nullable=False),
        sa.Column("visibility", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_repositories_workspace_id", "repositories", ["workspace_id"])
    op.create_index("ix_repositories_organization_id", "repositories", ["organization_id"])
    op.execute(
        """
        CREATE UNIQUE INDEX uq_repositories_workspace_normalized_url_active
        ON repositories (workspace_id, normalized_url)
        WHERE status = 'active'
        """
    )

    op.create_table(
        "assessments",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "repository_id",
            sa.String(length=160),
            sa.ForeignKey("repositories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.String(length=160),
            sa.ForeignKey("workspaces.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("engine_version", sa.String(length=64), nullable=False),
        sa.Column("assessment_version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generated_reports_json", sa.JSON(), nullable=False),
        sa.Column("references_json", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_assessments_repository_id", "assessments", ["repository_id"])
    op.create_index("ix_assessments_workspace_id", "assessments", ["workspace_id"])

    op.create_table(
        "assessment_artifacts",
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
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("format", sa.String(length=32), nullable=False),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("storage_reference", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("optimistic_version", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint(
            "assessment_id",
            "artifact_type",
            "checksum",
            name="uq_artifacts_assessment_type_checksum",
        ),
    )
    op.create_index("ix_artifacts_assessment_id", "assessment_artifacts", ["assessment_id"])


def downgrade() -> None:
    op.drop_table("assessment_artifacts")
    op.drop_table("assessments")
    op.execute("DROP INDEX IF EXISTS uq_repositories_workspace_normalized_url_active")
    op.drop_table("repositories")
    op.drop_table("workspaces")
    op.drop_table("organizations")
