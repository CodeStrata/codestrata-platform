"""Answering domain errors."""

from __future__ import annotations

from codestrata_platform.domain.errors import (
    DomainError,
    InvalidValueError,
    InvariantViolationError,
)


class AnsweringError(DomainError):
    """Base answering domain error."""


class AnsweringInvariantError(InvariantViolationError):
    """Raised when answer-run invariants are violated."""


class AnsweringLimitError(InvalidValueError):
    """Raised when answering limits are exceeded."""


class AnsweringRejectionError(InvalidValueError):
    """Raised when a question or answer is rejected by policy."""
