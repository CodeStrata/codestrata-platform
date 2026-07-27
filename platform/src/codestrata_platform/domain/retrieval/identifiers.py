"""Deterministic retrieval identifiers."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.shared.ids import PlatformId

_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,240}$")
MAX_EMBEDDING_DIMENSION = 4096
DEFAULT_EMBEDDING_DIMENSION = 384


def _stable_token(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]


def _is_finite(number: float) -> bool:
    return number == number and number not in {float("inf"), float("-inf")}


@dataclass(frozen=True, slots=True)
class RetrievalIndexId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class RetrievalDocumentId:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact or not _TOKEN.match(compact):
            raise InvalidValueError(
                "retrieval document id is invalid",
                reason_code="invalid_retrieval_document_id",
            )
        object.__setattr__(self, "value", compact)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class RetrievalChunkId:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact or not _TOKEN.match(compact):
            raise InvalidValueError(
                "retrieval chunk id is invalid",
                reason_code="invalid_retrieval_chunk_id",
            )
        object.__setattr__(self, "value", compact)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class RetrievalResultId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)


@dataclass(frozen=True, slots=True)
class EmbeddingProviderId:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip().lower()
        if not compact:
            raise InvalidValueError(
                "embedding provider id must be non-blank",
                reason_code="empty_embedding_provider_id",
            )
        object.__setattr__(self, "value", compact)


@dataclass(frozen=True, slots=True)
class EmbeddingModelId:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact:
            raise InvalidValueError(
                "embedding model id must be non-blank",
                reason_code="empty_embedding_model_id",
            )
        object.__setattr__(self, "value", compact)


@dataclass(frozen=True, slots=True)
class EmbeddingDimension:
    value: int

    def __post_init__(self) -> None:
        if self.value < 1 or self.value > MAX_EMBEDDING_DIMENSION:
            raise InvalidValueError(
                f"embedding dimension must be between 1 and {MAX_EMBEDDING_DIMENSION}",
                reason_code="invalid_embedding_dimension",
            )


@dataclass(frozen=True, slots=True)
class EmbeddingVector:
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.values:
            raise InvalidValueError(
                "embedding vector must be non-empty",
                reason_code="empty_embedding_vector",
            )
        if len(self.values) > MAX_EMBEDDING_DIMENSION:
            raise InvalidValueError(
                "embedding vector exceeds maximum dimension",
                reason_code="embedding_dimension_too_large",
            )
        normalized: list[float] = []
        for item in self.values:
            if not isinstance(item, (int, float)) or isinstance(item, bool):
                raise InvalidValueError(
                    "embedding values must be numeric",
                    reason_code="invalid_embedding_value_type",
                )
            number = float(item)
            if not _is_finite(number):
                raise InvalidValueError(
                    "embedding values must be finite",
                    reason_code="non_finite_embedding_value",
                )
            normalized.append(number)
        object.__setattr__(self, "values", tuple(normalized))

    @property
    def dimension(self) -> int:
        return len(self.values)


@dataclass(frozen=True, slots=True)
class ChunkChecksum:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip().lower()
        if len(compact) != 64 or any(ch not in "0123456789abcdef" for ch in compact):
            raise InvalidValueError(
                "chunk checksum must be a sha256 hex digest",
                reason_code="invalid_chunk_checksum",
            )
        object.__setattr__(self, "value", compact)

    @classmethod
    def from_text(cls, text: str) -> ChunkChecksum:
        return cls(hashlib.sha256(text.encode("utf-8")).hexdigest())


@dataclass(frozen=True, slots=True)
class RetrievalProjectionKey:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact or len(compact) > 128:
            raise InvalidValueError(
                "projection key is invalid",
                reason_code="invalid_retrieval_projection_key",
            )
        object.__setattr__(self, "value", compact)

    @classmethod
    def from_parts(
        cls,
        *,
        engineering_snapshot_id: str,
        engineering_snapshot_version: int,
        knowledge_graph_id: str,
        knowledge_graph_version: int,
        retrieval_schema_version: str,
        chunking_policy_version: str,
        embedding_provider_id: str,
        embedding_model_id: str,
        embedding_dimension: int,
    ) -> RetrievalProjectionKey:
        digest = hashlib.sha256(
            "|".join(
                [
                    engineering_snapshot_id.strip(),
                    str(engineering_snapshot_version),
                    knowledge_graph_id.strip(),
                    str(knowledge_graph_version),
                    retrieval_schema_version.strip(),
                    chunking_policy_version.strip(),
                    embedding_provider_id.strip(),
                    embedding_model_id.strip(),
                    str(embedding_dimension),
                ]
            ).encode("utf-8")
        ).hexdigest()
        return cls(digest)


def deterministic_index_id(
    *,
    repository_id: str,
    snapshot_id: str,
    graph_id: str,
    projection_key: str,
) -> RetrievalIndexId:
    token = _stable_token(repository_id, snapshot_id, graph_id, projection_key)
    return RetrievalIndexId(f"eng-retrieval:{token}")


def deterministic_document_id(
    *,
    index_id: str,
    content_type: str,
    canonical_id: str,
) -> RetrievalDocumentId:
    token = _stable_token(index_id, content_type, canonical_id)
    return RetrievalDocumentId(f"retrieval-doc:{token}")


def deterministic_chunk_id(
    *,
    document_id: str,
    ordinal: int,
    checksum: str,
) -> RetrievalChunkId:
    token = _stable_token(document_id, str(ordinal), checksum)
    return RetrievalChunkId(f"retrieval-chunk:{token}")
