"""Persistence package for retrieval repositories."""

from __future__ import annotations

from codestrata_platform.infrastructure.persistence.repositories import (
    SqlAlchemyRetrievalIndexRepository,
)

# Alias names matching the package layout in the phase brief.
SqlAlchemyRetrievalQueryRepository = SqlAlchemyRetrievalIndexRepository

__all__ = [
    "SqlAlchemyRetrievalIndexRepository",
    "SqlAlchemyRetrievalQueryRepository",
]
