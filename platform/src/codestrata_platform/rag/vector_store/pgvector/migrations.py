"""Schema migrations for the PostgreSQL + pgvector knowledge store."""

from __future__ import annotations

from typing import Any

from codestrata_platform.rag.vector_store.pgvector.schema import (
    DIMENSION_KEY,
    SCHEMA_VERSION,
    SCHEMA_VERSION_KEY,
    build_schema_statements,
    quoted_ident,
)


class PgVectorSchemaError(RuntimeError):
    """Raised when the pgvector schema cannot be migrated or validated."""


def read_metadata(connection: Any, *, schema: str, key: str) -> str | None:
    s = quoted_ident(schema)
    with connection.cursor() as cur:
        cur.execute(
            f"SELECT value FROM {s}.schema_metadata WHERE key = %s",
            (key,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return str(row[0])


def write_metadata(connection: Any, *, schema: str, key: str, value: str) -> None:
    s = quoted_ident(schema)
    with connection.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO {s}.schema_metadata(key, value)
            VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """,
            (key, value),
        )


def apply_migrations(
    connection: Any,
    *,
    schema: str,
    dimension: int,
    hnsw: bool,
) -> int:
    """Apply deterministic schema migrations; return active schema version."""

    from codestrata_platform.rag.vector_store.resolution import VectorStoreExtensionError

    try:
        with connection.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {quoted_ident(schema)}")
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {quoted_ident(schema)}.schema_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
    except Exception as exc:
        message = str(exc).lower()
        if "extension" in message and "vector" in message:
            raise VectorStoreExtensionError(
                "PostgreSQL extension 'vector' (pgvector) could not be created. "
                "Use the pgvector/pgvector Docker image locally, or enable the "
                "extension on the hosted database: CREATE EXTENSION vector;"
            ) from None
        raise

    current_raw = read_metadata(connection, schema=schema, key=SCHEMA_VERSION_KEY)
    current = int(current_raw) if current_raw is not None else 0
    if current > SCHEMA_VERSION:
        raise PgVectorSchemaError(
            f"pgvector schema version {current} is newer than supported "
            f"version {SCHEMA_VERSION}"
        )

    stored_dimension = read_metadata(connection, schema=schema, key=DIMENSION_KEY)
    if stored_dimension is not None and int(stored_dimension) != dimension:
        raise PgVectorSchemaError(
            f"pgvector embedding dimension mismatch: store has {stored_dimension}, "
            f"configured dimension is {dimension}"
        )

    # Shared Docker DBs can lose the embedding column when another suite runs
    # ``DROP SCHEMA public CASCADE`` (vector type lives in public). Rebuild.
    if _knowledge_vectors_missing_embedding(connection, schema=schema):
        with connection.cursor() as cur:
            cur.execute(
                f"DROP TABLE IF EXISTS {quoted_ident(schema)}.knowledge_vectors CASCADE"
            )
        write_metadata(
            connection,
            schema=schema,
            key=SCHEMA_VERSION_KEY,
            value="0",
        )
        current = 0

    if current < SCHEMA_VERSION:
        for statement in build_schema_statements(
            schema=schema,
            dimension=dimension,
            hnsw=hnsw,
        ):
            with connection.cursor() as cur:
                cur.execute(statement)
        write_metadata(
            connection,
            schema=schema,
            key=SCHEMA_VERSION_KEY,
            value=str(SCHEMA_VERSION),
        )
        write_metadata(
            connection,
            schema=schema,
            key=DIMENSION_KEY,
            value=str(dimension),
        )
        connection.commit()
        return SCHEMA_VERSION

    if stored_dimension is None:
        write_metadata(
            connection,
            schema=schema,
            key=DIMENSION_KEY,
            value=str(dimension),
        )
        connection.commit()
    return current


def _knowledge_vectors_missing_embedding(connection: Any, *, schema: str) -> bool:
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = 'knowledge_vectors'
            """,
            (schema,),
        )
        if cur.fetchone() is None:
            return False
        cur.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = 'knowledge_vectors'
              AND column_name = 'embedding'
            """,
            (schema,),
        )
        return cur.fetchone() is None
