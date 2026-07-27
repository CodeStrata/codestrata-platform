"""Portfolio domain errors."""

from __future__ import annotations

from codestrata_platform.domain.errors import DomainError


class PortfolioDomainError(DomainError):
    """Base error for portfolio domain violations."""


class PortfolioMembershipError(PortfolioDomainError):
    """Raised when membership rules are violated."""


class PortfolioSnapshotError(PortfolioDomainError):
    """Raised when portfolio snapshot lifecycle rules are violated."""


class PortfolioAggregationError(PortfolioDomainError):
    """Raised when deterministic aggregation invariants fail."""
