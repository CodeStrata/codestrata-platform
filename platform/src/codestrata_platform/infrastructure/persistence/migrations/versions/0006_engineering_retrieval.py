"""Engineering Retrieval Index persistence schema.

Revision ID: 0006_engineering_retrieval

Uses JSONB embeddings by default so Platform migrations succeed on PostgreSQL
without pgvector. When the vector extension is available (e.g. Docker image
``pgvector/pgvector``), an additional ``embedding_vector`` column and HNSW
index are created for ANN retrieval.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_engineering_retrieval"
down_revision: str | None = "0005_graph_intelligence_analysis"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_VECTOR_DIM = 384


def _try_enable_pgvector(connection) -> bool:
    connection.execute(sa.text("SAVEPOINT try_pgvector_extension"))
    try:
        connection.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
        row = connection.execute(
            sa.text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        ).first()
        connection.execute(sa.text("RELEASE SAVEPOINT try_pgvector_extension"))
        return row is not None
    except Exception:  # noqa: BLE001 - optional capability
        connection.execute(sa.text("ROLLBACK TO SAVEPOINT try_pgvector_extension"))
        return False


def upgrade() -> None:
    connection = op.get_bind()
    has_pgvector = _try_enable_pgvector(connection)

    op.create_table(
        "engineering_retrieval_indexes",
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
        sa.Column(
            "engineering_snapshot_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_snapshots.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("engineering_snapshot_version", sa.Integer(), nullable=False),
        sa.Column(
            "knowledge_graph_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_knowledge_graphs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("knowledge_graph_version", sa.Integer(), nullable=False),
        sa.Column("index_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("retrieval_schema_version", sa.String(length=64), nullable=False),
        sa.Column("chunking_policy_version", sa.String(length=64), nullable=False),
        sa.Column("embedding_provider_id", sa.String(length=64), nullable=False),
        sa.Column("embedding_model_id", sa.String(length=128), nullable=False),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False),
        sa.Column("projection_key", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("optimistic_version", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint(
            "projection_key",
            name="uq_engineering_retrieval_indexes_projection_key",
        ),
    )
    op.create_index(
        "ix_engineering_retrieval_indexes_repository_id",
        "engineering_retrieval_indexes",
        ["repository_id"],
    )
    op.create_index(
        "ix_engineering_retrieval_indexes_snapshot_id",
        "engineering_retrieval_indexes",
        ["engineering_snapshot_id"],
    )
    op.create_index(
        "ix_engineering_retrieval_indexes_graph_id",
        "engineering_retrieval_indexes",
        ["knowledge_graph_id"],
    )
    op.create_index(
        "ix_engineering_retrieval_indexes_status",
        "engineering_retrieval_indexes",
        ["status"],
    )

    op.create_table(
        "engineering_retrieval_documents",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "index_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_retrieval_indexes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("canonical_type", sa.String(length=64), nullable=False),
        sa.Column("canonical_id", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("structured_content", sa.JSON(), nullable=False),
        sa.Column("source_references", sa.JSON(), nullable=False),
        sa.Column("graph_node_ids", sa.JSON(), nullable=False),
        sa.Column("graph_edge_ids", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "index_id",
            "checksum",
            name="uq_engineering_retrieval_documents_index_checksum",
        ),
    )
    op.create_index(
        "ix_engineering_retrieval_documents_index_id",
        "engineering_retrieval_documents",
        ["index_id"],
    )
    op.create_index(
        "ix_engineering_retrieval_documents_content_type",
        "engineering_retrieval_documents",
        ["content_type"],
    )
    op.create_index(
        "ix_engineering_retrieval_documents_canonical",
        "engineering_retrieval_documents",
        ["canonical_type", "canonical_id"],
    )
    op.create_index(
        "ix_engineering_retrieval_documents_checksum",
        "engineering_retrieval_documents",
        ["checksum"],
    )

    op.create_table(
        "engineering_retrieval_chunks",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_retrieval_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "index_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_retrieval_indexes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_estimate", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("search_vector_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_references", sa.JSON(), nullable=False),
        sa.Column("graph_node_ids", sa.JSON(), nullable=False),
        sa.Column("graph_edge_ids", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "document_id",
            "checksum",
            name="uq_engineering_retrieval_chunks_document_checksum",
        ),
    )
    op.execute(
        "ALTER TABLE engineering_retrieval_chunks "
        "ADD COLUMN search_vector tsvector "
        "GENERATED ALWAYS AS (to_tsvector('english', coalesce(search_vector_text, ''))) STORED"
    )
    op.create_index(
        "ix_engineering_retrieval_chunks_index_id",
        "engineering_retrieval_chunks",
        ["index_id"],
    )
    op.create_index(
        "ix_engineering_retrieval_chunks_document_id",
        "engineering_retrieval_chunks",
        ["document_id"],
    )
    op.create_index(
        "ix_engineering_retrieval_chunks_checksum",
        "engineering_retrieval_chunks",
        ["checksum"],
    )
    op.execute(
        "CREATE INDEX ix_engineering_retrieval_chunks_search_vector "
        "ON engineering_retrieval_chunks USING GIN (search_vector)"
    )

    if has_pgvector:
        op.execute(
            f"ALTER TABLE engineering_retrieval_chunks "
            f"ADD COLUMN embedding_vector vector({_VECTOR_DIM})"
        )
        op.execute(
            """
            DO $$
            BEGIN
                CREATE INDEX ix_engineering_retrieval_chunks_embedding_hnsw
                ON engineering_retrieval_chunks
                USING hnsw (embedding_vector vector_cosine_ops);
            EXCEPTION
                WHEN OTHERS THEN
                    NULL;
            END $$;
            """
        )

    op.create_table(
        "engineering_retrieval_index_runs",
        sa.Column("id", sa.String(length=160), primary_key=True),
        sa.Column(
            "index_id",
            sa.String(length=160),
            sa.ForeignKey("engineering_retrieval_indexes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("projection_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("document_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedded_chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("diagnostics", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_engineering_retrieval_index_runs_index_id",
        "engineering_retrieval_index_runs",
        ["index_id"],
    )
    op.create_index(
        "ix_engineering_retrieval_index_runs_projection_key",
        "engineering_retrieval_index_runs",
        ["projection_key"],
    )


def downgrade() -> None:
    op.drop_table("engineering_retrieval_index_runs")
    op.drop_table("engineering_retrieval_chunks")
    op.drop_table("engineering_retrieval_documents")
    op.drop_table("engineering_retrieval_indexes")
