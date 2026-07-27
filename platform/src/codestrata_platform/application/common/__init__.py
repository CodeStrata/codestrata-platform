"""Shared application primitives (errors, pagination)."""

from __future__ import annotations

from codestrata_platform.application.common.errors import (
    ApplicationError,
    ConflictError,
    NotFoundError,
    PayloadTooLargeError,
    ValidationError,
)
from codestrata_platform.application.common.pagination import PageRequest, PageResult

__all__ = [
    "ApplicationError",
    "ConflictError",
    "NotFoundError",
    "PageRequest",
    "PageResult",
    "PayloadTooLargeError",
    "ValidationError",
]
