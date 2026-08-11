"""PostgreSQL connection helpers for the pgvector knowledge store."""

from __future__ import annotations

from typing import Any

from codestrata_platform.rag.vector_store.resolution import (
    VectorStoreConnectivityError,
    VectorStoreExtensionError,
)
from codestrata.security.database_url import redact_database_url, sanitize_exception_message


def require_psycopg() -> Any:
    """Import psycopg lazily with a clear error when the optional extra is missing."""

    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover - exercised when extra missing
        raise ImportError(
            "knowledge.vector_store.provider='pgvector' requires the optional "
            "dependency group 'pgvector' (pip install 'codestrata[pgvector]')"
        ) from exc
    return psycopg


def register_vector(connection: Any) -> None:
    """Register the pgvector type adapters on an open connection."""

    try:
        from pgvector.psycopg import register_vector
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "knowledge.vector_store.provider='pgvector' requires the optional "
            "dependency group 'pgvector' (pip install 'codestrata[pgvector]')"
        ) from exc
    register_vector(connection)


def connect(
    connection_string: str,
    *,
    connect_timeout_seconds: int = 10,
) -> Any:
    """Open a psycopg connection with pgvector adapters registered."""

    compact = connection_string.strip()
    if not compact:
        raise ValueError(
            "a database URL is required when provider='pgvector' "
            "(set CODESTRATA_DATABASE_URL)"
        )
    # Accept SQLAlchemy-style dialect URLs used elsewhere in the monorepo.
    lowered = compact.lower()
    if lowered.startswith("postgresql+psycopg://"):
        compact = "postgresql://" + compact.split("://", 1)[1]
    elif lowered.startswith("postgres://"):
        compact = "postgresql://" + compact.split("://", 1)[1]
    psycopg = require_psycopg()
    timeout = max(1, int(connect_timeout_seconds))
    try:
        connection = psycopg.connect(
            compact,
            autocommit=False,
            connect_timeout=timeout,
        )
    except Exception as exc:
        message = sanitize_exception_message(str(exc), database_url=compact)
        raise VectorStoreConnectivityError(
            "PostgreSQL is unreachable for provider='pgvector'. "
            f"Endpoint: {redact_database_url(compact)}. Details: {message}"
        ) from None
    try:
        register_vector(connection)
    except Exception:
        connection.close()
        raise
    return connection


def verify_vector_extension(connection: Any) -> str:
    """Ensure the ``vector`` extension is installed; return its version."""

    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT extversion
            FROM pg_extension
            WHERE extname = 'vector'
            """
        )
        row = cur.fetchone()
    if row is None:
        raise VectorStoreExtensionError(
            "PostgreSQL extension 'vector' (pgvector) is not installed. "
            "Use the pgvector/pgvector Docker image locally, or enable the "
            "extension on the hosted database: CREATE EXTENSION vector;"
        )
    return str(row[0])


def postgres_server_version(connection: Any) -> str | None:
    """Return a short PostgreSQL version string when available."""

    try:
        with connection.cursor() as cur:
            cur.execute("SHOW server_version")
            row = cur.fetchone()
        return str(row[0]) if row else None
    except Exception:  # noqa: BLE001
        return None
