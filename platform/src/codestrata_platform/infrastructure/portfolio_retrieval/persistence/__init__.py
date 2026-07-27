"""Persistence package for portfolio retrieval repositories."""

from __future__ import annotations

from codestrata_platform.infrastructure.persistence.repositories import (
    SqlAlchemyPortfolioRetrievalRepository,
)

# Alias names matching the package layout in the phase brief.
SqlAlchemyPortfolioRetrievalQueryRepository = SqlAlchemyPortfolioRetrievalRepository

__all__ = [
    "SqlAlchemyPortfolioRetrievalQueryRepository",
    "SqlAlchemyPortfolioRetrievalRepository",
]
