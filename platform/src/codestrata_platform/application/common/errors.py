"""Application-layer exceptions (orchestration failures, not domain rules)."""

from __future__ import annotations


class ApplicationError(Exception):
    """Base error for Commercial Platform application orchestration."""

    def __init__(self, message: str, *, reason_code: str | None = None) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class NotFoundError(ApplicationError):
    """Requested aggregate was not found."""


class ConflictError(ApplicationError):
    """Operation conflicts with existing state (e.g. duplicate registration)."""


class ValidationError(ApplicationError):
    """Command or query failed application-level validation (e.g. ownership)."""


class PayloadTooLargeError(ApplicationError):
    """Uploaded artifact exceeds configured maximum size."""
