"""Infrastructure-only database configuration and engine/session factories.

CodeStrata Platform runtime uses PostgreSQL only (SQLAlchemy 2.x + psycopg 3).

SQLite status
-------------
- CodeStrata Platform persistence: **not supported**. SQLite URLs are rejected.
- Engine knowledge store (``engine/.../knowledge_store``, ``knowledge.sqlite``):
  **intentional** Community Engine local durable store — unrelated to Platform DB.
- In-memory Platform tests use process memory repositories, not SQLite.
"""

from __future__ import annotations

import logging
import os
import warnings
from collections.abc import Callable

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

CANONICAL_DATABASE_URL_ENV = "CODESTRATA_DATABASE_URL"
DEPRECATED_PLATFORM_DATABASE_URL_ENV = "CODESTRATA_PLATFORM_DATABASE_URL"
DEPRECATED_PGVECTOR_URL_ENV = "CODESTRATA_PGVECTOR_URL"

# Local Docker Compose defaults (credentials live in docker-compose.yml only).
_LOCAL_DOCKER_POSTGRES_HINT = (
    "postgresql+psycopg://codestrata:***@127.0.0.1:5432/codestrata"
)
DEFAULT_DOCKER_POSTGRES_URL = (
    "postgresql+psycopg://codestrata:codestrata@127.0.0.1:5432/codestrata"
)


class DatabaseConfigurationError(RuntimeError):
    """Raised when Platform database configuration is missing or invalid."""


def _normalize_postgres_url(url: str) -> str:
    compact = url.strip()
    if not compact:
        raise DatabaseConfigurationError("Database URL must be non-blank")
    lowered = compact.lower()
    if lowered.startswith("sqlite"):
        raise DatabaseConfigurationError(
            "SQLite is not supported for CodeStrata Platform. "
            f"Set {CANONICAL_DATABASE_URL_ENV} to a PostgreSQL URL "
            f"(e.g. {_LOCAL_DOCKER_POSTGRES_HINT})."
        )
    if lowered.startswith("postgres://"):
        compact = "postgresql+psycopg://" + compact[len("postgres://") :]
    elif lowered.startswith("postgresql://") and "+psycopg" not in lowered.split("://", 1)[0]:
        compact = "postgresql+psycopg://" + compact[len("postgresql://") :]
    elif not lowered.startswith("postgresql+psycopg://"):
        raise DatabaseConfigurationError(
            "CodeStrata Platform requires postgresql+psycopg://… "
            f"(got scheme from {compact.split('://', 1)[0]!r})."
        )
    return compact


def get_database_url(*, override: str | None = None) -> str:
    """Resolve the Platform database URL (never used outside Infrastructure).

    Precedence:
    1. explicit ``override``
    2. ``CODESTRATA_DATABASE_URL``
    3. deprecated ``CODESTRATA_PLATFORM_DATABASE_URL`` (warns)
    4. deprecated ``CODESTRATA_PGVECTOR_URL`` (warns)
    """

    if override is not None:
        return _normalize_postgres_url(override)

    canonical = os.environ.get(CANONICAL_DATABASE_URL_ENV, "").strip()
    if canonical:
        return _normalize_postgres_url(canonical)

    deprecated_platform = os.environ.get(DEPRECATED_PLATFORM_DATABASE_URL_ENV, "").strip()
    if deprecated_platform:
        warnings.warn(
            f"{DEPRECATED_PLATFORM_DATABASE_URL_ENV} is deprecated; "
            f"use {CANONICAL_DATABASE_URL_ENV} instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _normalize_postgres_url(deprecated_platform)

    deprecated_pgvector = os.environ.get(DEPRECATED_PGVECTOR_URL_ENV, "").strip()
    if deprecated_pgvector:
        warnings.warn(
            f"{DEPRECATED_PGVECTOR_URL_ENV} is deprecated for Platform persistence; "
            f"use {CANONICAL_DATABASE_URL_ENV} instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _normalize_postgres_url(deprecated_pgvector)

    raise DatabaseConfigurationError(
        "CodeStrata Platform requires PostgreSQL. Set "
        f"{CANONICAL_DATABASE_URL_ENV}=postgresql+psycopg://user:***@host:port/database. "
        f"For local Docker Compose use {_LOCAL_DOCKER_POSTGRES_HINT}."
    )


def create_engine_from_url(url: str | None = None, *, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine configured for Platform PostgreSQL persistence."""

    database_url = get_database_url(override=url)
    return create_engine(
        database_url,
        echo=echo,
        future=True,
        pool_pre_ping=True,
        # Prefer public for Platform tables. Keep codestrata on the path so a
        # pgvector extension installed into the user schema remains visible.
        connect_args={"options": "-csearch_path=public,codestrata"},
    )


def create_session_factory(engine: Engine) -> Callable[[], Session]:
    """Return a session factory bound to ``engine``."""

    factory = sessionmaker(bind=engine, expire_on_commit=False, class_=Session, future=True)
    return factory


def ensure_pgvector_extension(engine: Engine) -> None:
    """Ensure the pgvector extension is available when the server supports it."""

    try:
        with engine.begin() as connection:
            connection.execute(
                text("CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public")
            )
    except Exception as error:  # noqa: BLE001 - optional shared Docker capability
        # Extension may already exist in another schema (e.g. user schema).
        try:
            with engine.begin() as connection:
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception:  # noqa: BLE001
            from codestrata.security.database_url import sanitize_exception_message

            logger.warning(
                "pgvector extension not available: %s",
                sanitize_exception_message(str(error)),
            )


def create_platform_schema(engine: Engine) -> None:
    """Apply Platform schema via Alembic migrations (PostgreSQL only)."""

    from codestrata_platform.infrastructure.persistence.migrations.runner import (
        upgrade_head,
    )

    # Retrieval migrations reference the vector type; install before upgrade.
    ensure_pgvector_extension(engine)
    upgrade_head(engine)
    ensure_pgvector_extension(engine)
