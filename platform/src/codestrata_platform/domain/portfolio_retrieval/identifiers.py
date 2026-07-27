"""Deterministic portfolio retrieval identifiers.

Embedding-related value objects (``EmbeddingProviderId``, ``EmbeddingModelId``,
``EmbeddingDimension``, ``EmbeddingVector``, ``ChunkChecksum``) are owned by the
canonical Engineering Retrieval domain and are re-exported here so portfolio
retrieval modules can depend on a single local module without duplicating the
value objects.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.retrieval.identifiers import (
    ChunkChecksum,
    EmbeddingDimension,
    EmbeddingModelId,
    EmbeddingProviderId,
    EmbeddingVector,
)
from codestrata_platform.domain.shared.ids import PlatformId

__all__ = [
    "ChunkChecksum",
    "EmbeddingDimension",
    "EmbeddingModelId",
    "EmbeddingProviderId",
    "EmbeddingVector",
    "PortfolioContextId",
    "PortfolioRetrievalChunkId",
    "PortfolioRetrievalDocumentId",
    "PortfolioRetrievalIndexId",
    "PortfolioRetrievalProjectionKey",
    "deterministic_portfolio_chunk_id",
    "deterministic_portfolio_document_id",
    "deterministic_portfolio_index_id",
]

_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,240}$")


def _stable_token(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalIndexId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalDocumentId:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact or not _TOKEN.match(compact):
            raise InvalidValueError(
                "portfolio retrieval document id is invalid",
                reason_code="invalid_portfolio_retrieval_document_id",
            )
        object.__setattr__(self, "value", compact)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalChunkId:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact or not _TOKEN.match(compact):
            raise InvalidValueError(
                "portfolio retrieval chunk id is invalid",
                reason_code="invalid_portfolio_retrieval_chunk_id",
            )
        object.__setattr__(self, "value", compact)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PortfolioContextId:
    """Identity of a single retrieved portfolio-context result entry."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalProjectionKey:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact or len(compact) > 128:
            raise InvalidValueError(
                "portfolio retrieval projection key is invalid",
                reason_code="invalid_portfolio_retrieval_projection_key",
            )
        object.__setattr__(self, "value", compact)

    @classmethod
    def from_parts(
        cls,
        *,
        portfolio_id: str,
        portfolio_snapshot_id: str,
        portfolio_snapshot_version: int,
        selected_repository_snapshot_identities: tuple[str, ...],
        retrieval_schema_version: str,
        chunking_policy_version: str,
        ranking_policy_version: str,
        embedding_provider_id: str,
        embedding_model_id: str,
        embedding_dimension: int,
    ) -> PortfolioRetrievalProjectionKey:
        identities = ",".join(
            sorted(item.strip() for item in selected_repository_snapshot_identities)
        )
        digest = hashlib.sha256(
            "|".join(
                [
                    portfolio_id.strip(),
                    portfolio_snapshot_id.strip(),
                    str(portfolio_snapshot_version),
                    identities,
                    retrieval_schema_version.strip(),
                    chunking_policy_version.strip(),
                    ranking_policy_version.strip(),
                    embedding_provider_id.strip(),
                    embedding_model_id.strip(),
                    str(embedding_dimension),
                ]
            ).encode("utf-8")
        ).hexdigest()
        return cls(digest)


def deterministic_portfolio_index_id(
    *,
    portfolio_id: str,
    portfolio_snapshot_id: str,
    projection_key: str,
) -> PortfolioRetrievalIndexId:
    token = _stable_token(portfolio_id, portfolio_snapshot_id, projection_key)
    return PortfolioRetrievalIndexId(f"portfolio-retrieval:{token}")


def deterministic_portfolio_document_id(
    *,
    index_id: str,
    content_type: str,
    canonical_id: str,
) -> PortfolioRetrievalDocumentId:
    token = _stable_token(index_id, content_type, canonical_id)
    return PortfolioRetrievalDocumentId(f"portfolio-retrieval-doc:{token}")


def deterministic_portfolio_chunk_id(
    *,
    document_id: str,
    ordinal: int,
    checksum: str,
) -> PortfolioRetrievalChunkId:
    token = _stable_token(document_id, str(ordinal), checksum)
    return PortfolioRetrievalChunkId(f"portfolio-retrieval-chunk:{token}")
