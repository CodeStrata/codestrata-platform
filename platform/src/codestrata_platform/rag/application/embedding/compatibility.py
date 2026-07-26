"""Embedding configuration fingerprint and index compatibility (Phase 5.8)."""

from __future__ import annotations

from typing import Any

from codestrata_platform.rag.domain.embedding import EmbeddingModelIdentity
from codestrata_platform.rag.domain.identifiers import fingerprint_payload
from codestrata_platform.rag.domain.schemas import VECTOR_RECORD_SCHEMA_VERSION


def embedding_configuration_fingerprint(identity: EmbeddingModelIdentity) -> str:
    """Stable fingerprint for provider/model/dimension/schema compatibility."""

    return fingerprint_payload(
        {
            "provider_id": identity.provider_id,
            "model": identity.model,
            "model_version": identity.model_version,
            "dimension": identity.dimension,
            "vector_record_schema_version": VECTOR_RECORD_SCHEMA_VERSION,
        }
    )


def embedding_metadata_stamp(identity: EmbeddingModelIdentity) -> dict[str, Any]:
    """Metadata fields stamped onto indexed vector records."""

    return {
        "embedding_provider": identity.provider_id,
        "embedding_model": identity.model,
        "embedding_model_version": identity.model_version,
        "embedding_dimension": identity.dimension,
        "embedding_config_fingerprint": embedding_configuration_fingerprint(identity),
        "vector_record_schema_version": VECTOR_RECORD_SCHEMA_VERSION,
    }


class EmbeddingIndexCompatibilityError(ValueError):
    """Raised when a query embedding configuration does not match the index."""


def assert_index_compatible(
    *,
    query_identity: EmbeddingModelIdentity,
    record_metadata: dict[str, Any] | None,
) -> None:
    """Reject queries against vectors stamped with a different embedding config.

    Records without stamps are allowed (legacy deterministic indexes) only when
    the query provider is also deterministic.
    """

    meta = dict(record_metadata or {})
    stamped_provider = meta.get("embedding_provider")
    stamped_fingerprint = meta.get("embedding_config_fingerprint")
    if stamped_provider is None and stamped_fingerprint is None:
        if query_identity.provider_id == "deterministic":
            return
        raise EmbeddingIndexCompatibilityError(
            "Indexed vectors lack embedding identity metadata and cannot be "
            "queried with a production embedding provider. Reindex the "
            "repository with the configured embedding provider."
        )

    expected = embedding_configuration_fingerprint(query_identity)
    if stamped_fingerprint and stamped_fingerprint != expected:
        raise EmbeddingIndexCompatibilityError(
            "Embedding configuration is incompatible with the indexed vectors "
            f"(index fingerprint {stamped_fingerprint!r} != query "
            f"{expected!r}). Reindex the repository with the current "
            "embedding provider/model/dimension before searching."
        )
    if stamped_provider and stamped_provider != query_identity.provider_id:
        raise EmbeddingIndexCompatibilityError(
            "Embedding provider is incompatible with the indexed vectors "
            f"(index {stamped_provider!r} != query "
            f"{query_identity.provider_id!r}). Reindex required."
        )
    stamped_dim = meta.get("embedding_dimension")
    if stamped_dim is not None and int(stamped_dim) != query_identity.dimension:
        raise EmbeddingIndexCompatibilityError(
            "Embedding dimension is incompatible with the indexed vectors "
            f"(index {stamped_dim} != query {query_identity.dimension}). "
            "Reindex required."
        )
