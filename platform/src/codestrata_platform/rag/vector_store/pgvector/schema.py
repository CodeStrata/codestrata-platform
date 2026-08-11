"""PostgreSQL + pgvector schema definitions (Phase 5.4)."""

from __future__ import annotations

SCHEMA_VERSION = 1
SCHEMA_VERSION_KEY = "knowledge_pgvector_schema_version"
DIMENSION_KEY = "knowledge_pgvector_dimension"


def quoted_ident(name: str) -> str:
    """Quote a PostgreSQL identifier (schema/table) safely."""

    compact = name.strip()
    if not compact or not all(ch.isalnum() or ch == "_" for ch in compact):
        raise ValueError(f"invalid SQL identifier: {name!r}")
    return f'"{compact}"'


def build_schema_statements(
    *,
    schema: str,
    dimension: int,
    hnsw: bool,
) -> tuple[str, ...]:
    """Return deterministic DDL statements for one schema version."""

    if dimension <= 0:
        raise ValueError("dimension must be positive")
    s = quoted_ident(schema)
    statements = [
        "CREATE EXTENSION IF NOT EXISTS vector",
        f"CREATE SCHEMA IF NOT EXISTS {s}",
        f"""
        CREATE TABLE IF NOT EXISTS {s}.schema_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS {s}.knowledge_documents (
            document_id TEXT PRIMARY KEY,
            schema_name TEXT,
            schema_version TEXT,
            source_type TEXT,
            source_id TEXT,
            title TEXT,
            content TEXT,
            fingerprint TEXT,
            tenant_id TEXT,
            repository_id TEXT,
            scan_id TEXT,
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS {s}.knowledge_chunks (
            chunk_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            sequence INTEGER NOT NULL DEFAULT 0,
            content TEXT,
            fingerprint TEXT,
            tenant_id TEXT,
            repository_id TEXT,
            scan_id TEXT,
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT knowledge_chunks_document_id_fkey
                FOREIGN KEY (document_id)
                REFERENCES {s}.knowledge_documents (document_id)
                ON DELETE CASCADE
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS {s}.knowledge_vectors (
            record_id TEXT PRIMARY KEY,
            embedding vector({dimension}) NOT NULL,
            document_id TEXT,
            chunk_id TEXT,
            entity_id TEXT NOT NULL,
            namespace TEXT NOT NULL DEFAULT 'default',
            tenant_id TEXT,
            repository_id TEXT,
            scan_id TEXT,
            branch TEXT,
            commit_sha TEXT,
            source_type TEXT,
            intelligence_pack TEXT,
            assessment_version TEXT,
            finding_id TEXT,
            rule_id TEXT,
            severity TEXT,
            confidence TEXT,
            file_path TEXT,
            symbol_name TEXT,
            content_hash TEXT,
            sequence INTEGER,
            fingerprint TEXT,
            text TEXT,
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        f"""
        CREATE INDEX IF NOT EXISTS knowledge_vectors_tenant_repo_scan_idx
            ON {s}.knowledge_vectors (tenant_id, repository_id, scan_id)
        """,
        f"""
        CREATE INDEX IF NOT EXISTS knowledge_vectors_namespace_idx
            ON {s}.knowledge_vectors (namespace)
        """,
        f"""
        CREATE INDEX IF NOT EXISTS knowledge_vectors_source_type_idx
            ON {s}.knowledge_vectors (source_type)
        """,
        f"""
        CREATE INDEX IF NOT EXISTS knowledge_vectors_finding_id_idx
            ON {s}.knowledge_vectors (finding_id)
        """,
        f"""
        CREATE INDEX IF NOT EXISTS knowledge_vectors_rule_id_idx
            ON {s}.knowledge_vectors (rule_id)
        """,
        f"""
        CREATE INDEX IF NOT EXISTS knowledge_vectors_file_path_idx
            ON {s}.knowledge_vectors (file_path)
        """,
        f"""
        CREATE INDEX IF NOT EXISTS knowledge_chunks_doc_seq_idx
            ON {s}.knowledge_chunks (document_id, sequence)
        """,
        f"""
        CREATE INDEX IF NOT EXISTS knowledge_documents_tenant_repo_scan_idx
            ON {s}.knowledge_documents (tenant_id, repository_id, scan_id)
        """,
    ]
    if hnsw:
        statements.append(
            f"""
            CREATE INDEX IF NOT EXISTS knowledge_vectors_embedding_hnsw_idx
                ON {s}.knowledge_vectors
                USING hnsw (embedding vector_cosine_ops)
            """
        )
    return tuple(statements)
