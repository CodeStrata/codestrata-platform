"""Engineering answering persistence schema.

Revision ID: 0007_engineering_answering
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_engineering_answering"
down_revision: str | None = "0006_engineering_retrieval"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "engineering_answer_runs",
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
            nullable=True,
        ),
        sa.Column(
            "retrieval_index_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_retrieval_indexes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("retrieval_index_version", sa.Integer(), nullable=False),
        sa.Column(
            "engineering_snapshot_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_snapshots.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "knowledge_graph_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_knowledge_graphs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("question_type", sa.String(length=64), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("normalized_question_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("projection_key", sa.String(length=128), nullable=False),
        sa.Column("provider_id", sa.String(length=64), nullable=False),
        sa.Column("model_id", sa.String(length=128), nullable=False),
        sa.Column("prompt_template_version", sa.String(length=64), nullable=False),
        sa.Column("answer_policy_version", sa.String(length=64), nullable=False),
        sa.Column("grounding_status", sa.String(length=64), nullable=True),
        sa.Column("confidence_level", sa.String(length=32), nullable=True),
        sa.Column("confidence_score", sa.Integer(), nullable=True),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("follow_up_questions", sa.JSON(), nullable=False),
        sa.Column("diagnostics", sa.JSON(), nullable=False),
        sa.Column("usage_metadata", sa.JSON(), nullable=False),
        sa.Column("provider_request_id", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("optimistic_version", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("projection_key", name="uq_engineering_answer_runs_projection_key"),
    )
    op.create_index(
        "ix_engineering_answer_runs_repository_id",
        "engineering_answer_runs",
        ["repository_id"],
    )
    op.create_index(
        "ix_engineering_answer_runs_retrieval_index_id",
        "engineering_answer_runs",
        ["retrieval_index_id"],
    )
    op.create_index(
        "ix_engineering_answer_runs_status",
        "engineering_answer_runs",
        ["status"],
    )

    op.create_table(
        "engineering_answer_citations",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "answer_run_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_answer_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(length=32), nullable=False),
        sa.Column("retrieval_document_id", sa.String(length=160), nullable=False),
        sa.Column("retrieval_chunk_id", sa.String(length=160), nullable=False),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("canonical_type", sa.String(length=64), nullable=False),
        sa.Column("canonical_id", sa.String(length=160), nullable=False),
        sa.Column("source_references", sa.JSON(), nullable=False),
        sa.Column("graph_node_ids", sa.JSON(), nullable=False),
        sa.Column("graph_edge_ids", sa.JSON(), nullable=False),
        sa.Column("retrieval_score", sa.Float(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_engineering_answer_citations_answer_run_id",
        "engineering_answer_citations",
        ["answer_run_id"],
    )

    op.create_table(
        "engineering_answer_feedback",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "answer_run_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_answer_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("feedback_category", sa.String(length=64), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_engineering_answer_feedback_answer_run_id",
        "engineering_answer_feedback",
        ["answer_run_id"],
    )


def downgrade() -> None:
    op.drop_table("engineering_answer_feedback")
    op.drop_table("engineering_answer_citations")
    op.drop_table("engineering_answer_runs")
