"""Portfolio retrieval result value objects."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.portfolio_retrieval.citation import PortfolioRetrievalCitation
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    PortfolioContextId,
    PortfolioRetrievalChunkId,
    PortfolioRetrievalDocumentId,
)
from codestrata_platform.domain.portfolio_retrieval.query import PortfolioRetrievalScore
from codestrata_platform.domain.portfolio_retrieval.ranking import (
    HARD_MAX_CONTRIBUTING_REPOSITORIES,
    RepositoryContribution,
)
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType
from codestrata_platform.domain.repository.ids import RepositoryId


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalHit:
    result_id: PortfolioContextId
    chunk_id: PortfolioRetrievalChunkId
    document_id: PortfolioRetrievalDocumentId
    content_type: PortfolioRetrievalContentType
    canonical_type: str
    canonical_id: str
    title: str
    text: str
    score: PortfolioRetrievalScore
    repository_ids: tuple[RepositoryId, ...] = ()
    primary_repository_id: RepositoryId | None = None
    repository_contributions: tuple[RepositoryContribution, ...] = ()
    citations: tuple[PortfolioRetrievalCitation, ...] = ()

    def __post_init__(self) -> None:
        if len(self.repository_contributions) > HARD_MAX_CONTRIBUTING_REPOSITORIES:
            raise InvalidValueError(
                "repository_contributions exceeds maximum contributing repositories of "
                f"{HARD_MAX_CONTRIBUTING_REPOSITORIES}",
                reason_code="portfolio_retrieval_hit_contributions_too_large",
            )


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalSearchResult:
    hits: tuple[PortfolioRetrievalHit, ...]
    mode: str
    top_k: int
