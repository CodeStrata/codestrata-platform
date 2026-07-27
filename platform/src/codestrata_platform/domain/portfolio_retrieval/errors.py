"""Portfolio retrieval domain errors."""

from __future__ import annotations

from codestrata_platform.domain.errors import (
    DomainError,
    InvalidValueError,
    InvariantViolationError,
)


class PortfolioRetrievalError(DomainError):
    """Base portfolio retrieval domain error."""


class PortfolioRetrievalInvariantError(InvariantViolationError):
    """Raised when portfolio retrieval index invariants are violated."""


class PortfolioRetrievalLimitError(InvalidValueError):
    """Raised when portfolio retrieval limits are exceeded."""
