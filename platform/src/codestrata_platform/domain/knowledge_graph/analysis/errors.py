"""Graph intelligence analysis errors."""

from __future__ import annotations

from codestrata_platform.domain.errors import DomainError, InvalidValueError


class GraphAnalysisError(DomainError):
    """Base error for graph intelligence analysis."""


class GraphAnalysisLimitError(InvalidValueError):
    """Raised when analysis limits are exceeded or invalid."""


class GraphAnalysisInvariantError(GraphAnalysisError):
    """Raised when analysis invariants are violated."""
