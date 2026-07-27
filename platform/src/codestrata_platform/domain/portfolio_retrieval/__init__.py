"""Portfolio Retrieval domain package."""

from __future__ import annotations

from codestrata_platform.domain.portfolio_retrieval.chunk import (
    PortfolioRetrievalChunk,
    estimate_tokens,
)
from codestrata_platform.domain.portfolio_retrieval.citation import PortfolioRetrievalCitation
from codestrata_platform.domain.portfolio_retrieval.document import PortfolioRetrievalDocument
from codestrata_platform.domain.portfolio_retrieval.errors import (
    PortfolioRetrievalError,
    PortfolioRetrievalInvariantError,
    PortfolioRetrievalLimitError,
)
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    ChunkChecksum,
    EmbeddingDimension,
    EmbeddingModelId,
    EmbeddingProviderId,
    EmbeddingVector,
    PortfolioContextId,
    PortfolioRetrievalChunkId,
    PortfolioRetrievalDocumentId,
    PortfolioRetrievalIndexId,
    PortfolioRetrievalProjectionKey,
    deterministic_portfolio_chunk_id,
    deterministic_portfolio_document_id,
    deterministic_portfolio_index_id,
)
from codestrata_platform.domain.portfolio_retrieval.index import PortfolioRetrievalIndex
from codestrata_platform.domain.portfolio_retrieval.lifecycle import (
    PortfolioRetrievalIndexStatus,
    PortfolioRetrievalIndexVersion,
    PortfolioRetrievalStalenessReason,
    RepositoryBalanceMode,
)
from codestrata_platform.domain.portfolio_retrieval.ports import (
    PortfolioRetrievalChunkRepository,
    PortfolioRetrievalDocumentRepository,
    PortfolioRetrievalIndexRepository,
    PortfolioRetrievalQueryRepository,
    PortfolioRetrievalSourceRepository,
    PortfolioRetrievalSourceSnapshot,
)
from codestrata_platform.domain.portfolio_retrieval.query import (
    PortfolioRetrievalQuery,
    PortfolioRetrievalScore,
)
from codestrata_platform.domain.portfolio_retrieval.ranking import RepositoryContribution
from codestrata_platform.domain.portfolio_retrieval.result import (
    PortfolioRetrievalHit,
    PortfolioRetrievalSearchResult,
)
from codestrata_platform.domain.portfolio_retrieval.scope import PortfolioRetrievalScope
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType

__all__ = [
    "ChunkChecksum",
    "EmbeddingDimension",
    "EmbeddingModelId",
    "EmbeddingProviderId",
    "EmbeddingVector",
    "PortfolioContextId",
    "PortfolioRetrievalChunk",
    "PortfolioRetrievalChunkId",
    "PortfolioRetrievalChunkRepository",
    "PortfolioRetrievalCitation",
    "PortfolioRetrievalContentType",
    "PortfolioRetrievalDocument",
    "PortfolioRetrievalDocumentId",
    "PortfolioRetrievalDocumentRepository",
    "PortfolioRetrievalError",
    "PortfolioRetrievalHit",
    "PortfolioRetrievalIndex",
    "PortfolioRetrievalIndexId",
    "PortfolioRetrievalIndexRepository",
    "PortfolioRetrievalIndexStatus",
    "PortfolioRetrievalIndexVersion",
    "PortfolioRetrievalInvariantError",
    "PortfolioRetrievalLimitError",
    "PortfolioRetrievalProjectionKey",
    "PortfolioRetrievalQuery",
    "PortfolioRetrievalQueryRepository",
    "PortfolioRetrievalScope",
    "PortfolioRetrievalScore",
    "PortfolioRetrievalSearchResult",
    "PortfolioRetrievalSourceRepository",
    "PortfolioRetrievalSourceSnapshot",
    "PortfolioRetrievalStalenessReason",
    "RepositoryBalanceMode",
    "RepositoryContribution",
    "deterministic_portfolio_chunk_id",
    "deterministic_portfolio_document_id",
    "deterministic_portfolio_index_id",
    "estimate_tokens",
]
