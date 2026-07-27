"""Portfolio answering domain errors."""

from __future__ import annotations

from codestrata_platform.domain.errors import (
    DomainError,
    InvalidValueError,
    InvariantViolationError,
)


class PortfolioAnsweringError(DomainError):
    """Base portfolio answering domain error."""


class PortfolioAnsweringInvariantError(InvariantViolationError):
    """Raised when portfolio answer-run invariants are violated."""


class PortfolioAnsweringLimitError(InvalidValueError):
    """Raised when portfolio answering limits are exceeded."""


class PortfolioAnsweringRejectionError(InvalidValueError):
    """Raised when a portfolio question or answer is rejected by policy."""
