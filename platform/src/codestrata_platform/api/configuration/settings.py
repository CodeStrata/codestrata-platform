"""Infrastructure-free settings surface for the REST API composition root."""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from pathlib import Path

CANONICAL_DATABASE_URL_ENV = "CODESTRATA_DATABASE_URL"
DEPRECATED_PLATFORM_DATABASE_URL_ENV = "CODESTRATA_PLATFORM_DATABASE_URL"
DEPRECATED_PGVECTOR_URL_ENV = "CODESTRATA_PGVECTOR_URL"
_DEFAULT_DOCKER = "postgresql+psycopg://codestrata:codestrata@127.0.0.1:5432/codestrata"


def _normalize_postgres_url(url: str) -> str:
    compact = url.strip()
    if not compact:
        raise RuntimeError("Database URL must be non-blank")
    lowered = compact.lower()
    if lowered.startswith("sqlite"):
        raise RuntimeError(
            "SQLite is not supported for the Commercial Platform. "
            f"Set {CANONICAL_DATABASE_URL_ENV} to a PostgreSQL URL."
        )
    if lowered.startswith("postgres://"):
        return "postgresql+psycopg://" + compact[len("postgres://") :]
    if lowered.startswith("postgresql://") and "+psycopg" not in lowered.split("://", 1)[0]:
        return "postgresql+psycopg://" + compact[len("postgresql://") :]
    if not lowered.startswith("postgresql+psycopg://"):
        raise RuntimeError(
            "Commercial Platform requires postgresql+psycopg://… "
            f"(got {compact.split('://', 1)[0]!r})."
        )
    return compact


def resolve_api_database_url(*, override: str | None = None) -> str:
    if override is not None:
        return _normalize_postgres_url(override)
    canonical = os.environ.get(CANONICAL_DATABASE_URL_ENV, "").strip()
    if canonical:
        return _normalize_postgres_url(canonical)
    deprecated = os.environ.get(DEPRECATED_PLATFORM_DATABASE_URL_ENV, "").strip()
    if deprecated:
        warnings.warn(
            f"{DEPRECATED_PLATFORM_DATABASE_URL_ENV} is deprecated; "
            f"use {CANONICAL_DATABASE_URL_ENV} instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _normalize_postgres_url(deprecated)
    deprecated_pg = os.environ.get(DEPRECATED_PGVECTOR_URL_ENV, "").strip()
    if deprecated_pg:
        warnings.warn(
            f"{DEPRECATED_PGVECTOR_URL_ENV} is deprecated for Platform persistence; "
            f"use {CANONICAL_DATABASE_URL_ENV} instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _normalize_postgres_url(deprecated_pg)
    raise RuntimeError(
        "Commercial Platform requires PostgreSQL. Set "
        f"{CANONICAL_DATABASE_URL_ENV}=postgresql+psycopg://user:password@host:port/database. "
        f"For local Docker Compose use {_DEFAULT_DOCKER}."
    )


@dataclass(frozen=True, slots=True)
class ApiSettings:
    """Transport configuration. Persistence URLs stay infrastructure-owned."""

    database_url: str
    use_memory: bool = False
    artifact_storage_root: Path | None = None
    max_artifact_bytes: int = 10_485_760
    title: str = "CodeStrata Commercial Platform API"
    version: str = "v1"

    @classmethod
    def from_env(cls, *, use_memory: bool = False, database_url: str | None = None) -> ApiSettings:
        root_raw = os.environ.get("CODESTRATA_PLATFORM_ARTIFACT_STORAGE_ROOT", "").strip()
        max_bytes_raw = os.environ.get("CODESTRATA_PLATFORM_MAX_ARTIFACT_BYTES", "").strip()
        if use_memory:
            resolved = (
                database_url
                or os.environ.get(CANONICAL_DATABASE_URL_ENV, "").strip()
                or _DEFAULT_DOCKER
            )
            if resolved.lower().startswith("sqlite"):
                resolved = _DEFAULT_DOCKER
            else:
                resolved = _normalize_postgres_url(resolved)
        else:
            resolved = resolve_api_database_url(override=database_url)
        return cls(
            database_url=resolved,
            use_memory=use_memory,
            artifact_storage_root=Path(root_raw) if root_raw else None,
            max_artifact_bytes=int(max_bytes_raw) if max_bytes_raw else 10_485_760,
        )
