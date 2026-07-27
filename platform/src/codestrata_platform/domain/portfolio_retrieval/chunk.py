"""Portfolio retrieval chunk value objects."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio_retrieval.citation import PortfolioRetrievalCitation
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    ChunkChecksum,
    EmbeddingVector,
    PortfolioRetrievalChunkId,
    PortfolioRetrievalDocumentId,
    PortfolioRetrievalIndexId,
)
from codestrata_platform.domain.portfolio_retrieval.ranking import (
    HARD_MAX_CONTRIBUTING_REPOSITORIES,
)
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.chunk import estimate_tokens
from codestrata_platform.domain.retrieval.document import sanitize_retrieval_text

HARD_MAX_TOKENS = 1000
DEFAULT_TARGET_MIN_TOKENS = 350
DEFAULT_TARGET_MAX_TOKENS = 700


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalChunk:
    chunk_id: PortfolioRetrievalChunkId
    document_id: PortfolioRetrievalDocumentId
    index_id: PortfolioRetrievalIndexId
    portfolio_id: PortfolioId
    portfolio_snapshot_id: PortfolioSnapshotId
    ordinal: int
    text: str
    token_estimate: int
    checksum: ChunkChecksum
    repository_ids: tuple[RepositoryId, ...] = ()
    primary_repository_id: RepositoryId | None = None
    embedding: EmbeddingVector | None = None
    citations: tuple[PortfolioRetrievalCitation, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.ordinal < 0:
            raise InvalidValueError(
                "chunk ordinal must be >= 0",
                reason_code="invalid_portfolio_retrieval_chunk_ordinal",
            )
        text = sanitize_retrieval_text(self.text, max_length=HARD_MAX_TOKENS * 4)
        tokens = estimate_tokens(text)
        if tokens > HARD_MAX_TOKENS:
            raise InvalidValueError(
                f"chunk exceeds hard maximum of {HARD_MAX_TOKENS} tokens",
                reason_code="portfolio_retrieval_chunk_too_large",
            )
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "token_estimate", tokens)
        expected = ChunkChecksum.from_text(text)
        if self.checksum.value != expected.value:
            raise InvalidValueError(
                "chunk checksum does not match text",
                reason_code="portfolio_retrieval_chunk_checksum_mismatch",
            )
        if len(self.repository_ids) > HARD_MAX_CONTRIBUTING_REPOSITORIES:
            raise InvalidValueError(
                "repository_ids exceeds maximum contributing repositories of "
                f"{HARD_MAX_CONTRIBUTING_REPOSITORIES}",
                reason_code="portfolio_retrieval_chunk_repositories_too_large",
            )
        if self.primary_repository_id is not None and self.repository_ids:
            if self.primary_repository_id not in self.repository_ids:
                raise InvalidValueError(
                    "primary_repository_id must be included in repository_ids",
                    reason_code="portfolio_retrieval_chunk_primary_repository_missing",
                )
        if not self.citations:
            raise InvalidValueError(
                "portfolio retrieval chunks require citations",
                reason_code="missing_portfolio_retrieval_chunk_citations",
            )
