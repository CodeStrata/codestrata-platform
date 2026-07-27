"""Knowledge graph domain errors."""

from __future__ import annotations

from codestrata_platform.domain.errors import DomainError, InvariantViolationError


class GraphInvariantError(InvariantViolationError):
    """Raised when graph structure violates CEIM projection invariants."""


class GraphProjectionError(DomainError):
    """Raised when graph projection cannot complete."""
