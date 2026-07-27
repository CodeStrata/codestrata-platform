"""Infrastructure portfolio retrieval package."""

from __future__ import annotations

from codestrata_platform.infrastructure.portfolio_retrieval.embeddings import (
    create_portfolio_embedding_provider,
)
from codestrata_platform.infrastructure.portfolio_retrieval.search import search_portfolio_index

__all__ = [
    "create_portfolio_embedding_provider",
    "search_portfolio_index",
]
