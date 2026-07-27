"""Executive Intelligence domain errors."""

from __future__ import annotations

from codestrata_platform.domain.errors import DomainError


class ExecutiveIntelligenceError(DomainError):
    """Base error for Executive Intelligence invariants."""


class ExecutiveIntelligenceInvariantError(ExecutiveIntelligenceError):
    """Raised when an executive intelligence invariant is violated."""
