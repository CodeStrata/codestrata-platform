"""Resolve vector-store provider, schema, and database URL from env + settings."""

from __future__ import annotations

import os

from codestrata.config.settings import KnowledgeSettings, KnowledgeVectorStoreSettings
from codestrata.security.database_url import redact_database_url

# Canonical environment variables (Phase 5.4.1).
ENV_VECTOR_STORE_PROVIDER = "CODESTRATA_VECTOR_STORE_PROVIDER"
ENV_DATABASE_URL = "CODESTRATA_DATABASE_URL"
ENV_DATABASE_SCHEMA = "CODESTRATA_DATABASE_SCHEMA"

# Deprecated compatibility alias from Phase 5.4.
DEPRECATED_ENV_DATABASE_URL = "CODESTRATA_PGVECTOR_URL"

SUPPORTED_VECTOR_STORE_PROVIDERS = frozenset({"memory", "pgvector"})
DEFAULT_PROVIDER = "memory"
DEFAULT_SCHEMA = "codestrata"
DEFAULT_CONNECTION_STRING_ENV = "CODESTRATA_DATABASE_URL"


class VectorStoreConfigurationError(ValueError):
    """Actionable configuration error that never embeds raw credentials."""


class VectorStoreConnectivityError(RuntimeError):
    """Raised when PostgreSQL is unreachable for the pgvector provider."""


class VectorStoreExtensionError(RuntimeError):
    """Raised when the PostgreSQL ``vector`` extension is missing."""


def _env(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None:
        return None
    compact = value.strip()
    return compact or None


def resolve_vector_store_provider(
    settings: KnowledgeSettings | KnowledgeVectorStoreSettings | None = None,
) -> str:
    """Resolve provider: env → codestrata.toml → default ``memory``."""

    env_provider = _env(ENV_VECTOR_STORE_PROVIDER)
    if env_provider is not None:
        provider = env_provider.lower()
    elif settings is None:
        provider = DEFAULT_PROVIDER
    elif isinstance(settings, KnowledgeSettings):
        provider = settings.vector_store.provider
    else:
        provider = settings.provider

    provider = provider.strip().lower()
    if provider not in SUPPORTED_VECTOR_STORE_PROVIDERS:
        raise VectorStoreConfigurationError(
            f"unsupported knowledge.vector_store.provider: {provider!r} "
            f"(supported: {sorted(SUPPORTED_VECTOR_STORE_PROVIDERS)}; "
            f"set {ENV_VECTOR_STORE_PROVIDER} or [knowledge.vector_store].provider)"
        )
    return provider


def resolve_vector_store_schema(
    settings: KnowledgeSettings | KnowledgeVectorStoreSettings | None = None,
) -> str:
    """Resolve schema: env → codestrata.toml → ``codestrata``."""

    env_schema = _env(ENV_DATABASE_SCHEMA)
    if env_schema is not None:
        schema = env_schema.lower()
    elif settings is None:
        schema = DEFAULT_SCHEMA
    elif isinstance(settings, KnowledgeSettings):
        schema = settings.vector_store.schema_name
    else:
        schema = settings.schema_name

    schema = schema.strip().lower()
    if not schema or not schema.replace("_", "").isalnum():
        raise VectorStoreConfigurationError(
            "knowledge.vector_store.schema must be a nonempty alphanumeric "
            f"identifier (underscores allowed); got {schema!r}"
        )
    return schema


def resolve_database_url(
    settings: KnowledgeSettings | KnowledgeVectorStoreSettings | None = None,
    *,
    programmatic_url: str | None = None,
) -> str | None:
    """Resolve database URL without returning secrets into logs.

    Order:
    1. ``CODESTRATA_DATABASE_URL``
    2. deprecated ``CODESTRATA_PGVECTOR_URL``
    3. ``programmatic_url`` (tests / explicit factory argument)
    4. deprecated ``[knowledge.vector_store].connection_string``
    """

    canonical = _env(ENV_DATABASE_URL)
    if canonical:
        return canonical

    deprecated = _env(DEPRECATED_ENV_DATABASE_URL)
    if deprecated:
        return deprecated

    if programmatic_url is not None:
        compact = programmatic_url.strip()
        if compact:
            return compact

    if settings is None:
        return None
    vector = (
        settings.vector_store if isinstance(settings, KnowledgeSettings) else settings
    )
    # Optional env-name indirection (default CODESTRATA_DATABASE_URL already checked).
    env_name = (vector.connection_string_env or DEFAULT_CONNECTION_STRING_ENV).strip()
    if env_name and env_name != ENV_DATABASE_URL:
        named = _env(env_name)
        if named:
            return named

    deprecated_toml = vector.connection_string.strip()
    return deprecated_toml or None


def resolve_connect_timeout_seconds(
    settings: KnowledgeSettings | KnowledgeVectorStoreSettings | None = None,
) -> int:
    if settings is None:
        return 10
    vector = (
        settings.vector_store if isinstance(settings, KnowledgeSettings) else settings
    )
    return int(vector.connect_timeout_seconds)


def resolve_embedding_dimension(
    settings: KnowledgeSettings | KnowledgeVectorStoreSettings | None = None,
    *,
    default: int = 384,
) -> int:
    if isinstance(settings, KnowledgeSettings):
        return int(settings.embedding.dimension)
    return default


def missing_database_url_error(
    *,
    endpoint_hint: str | None = None,
) -> VectorStoreConfigurationError:
    hint = ""
    if endpoint_hint:
        hint = f" (configured endpoint: {redact_database_url(endpoint_hint)})"
    return VectorStoreConfigurationError(
        "provider='pgvector' requires a database URL. Set "
        f"{ENV_DATABASE_URL}=postgresql://…{hint}. "
        f"Deprecated aliases: {DEPRECATED_ENV_DATABASE_URL} or "
        "[knowledge.vector_store].connection_string (not recommended). "
        "For local Docker see docs/repository-knowledge/vector-store-setup.md."
    )
