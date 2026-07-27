"""Domain-layer errors for the Commercial Platform foundation."""

from __future__ import annotations


class DomainError(Exception):
    """Base error for Commercial Platform domain violations."""

    def __init__(self, message: str, *, reason_code: str | None = None) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class InvalidValueError(DomainError):
    """Raised when a value object cannot be constructed."""


class InvalidStateTransitionError(DomainError):
    """Raised when an aggregate rejects a lifecycle transition."""


class InvariantViolationError(DomainError):
    """Raised when an aggregate invariant would be violated."""
