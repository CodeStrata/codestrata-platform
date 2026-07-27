"""Retrieval domain errors."""

from __future__ import annotations

from codestrata_platform.domain.errors import (
    DomainError,
    InvalidValueError,
    InvariantViolationError,
)


class RetrievalError(DomainError):
    """Base retrieval domain error."""


class RetrievalInvariantError(InvariantViolationError):
    """Raised when retrieval index invariants are violated."""


class RetrievalLimitError(InvalidValueError):
    """Raised when retrieval limits are exceeded."""
