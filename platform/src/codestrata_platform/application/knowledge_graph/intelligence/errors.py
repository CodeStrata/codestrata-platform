"""Application errors for graph intelligence."""

from __future__ import annotations

from codestrata_platform.application.common.errors import ApplicationError, ValidationError


class GraphIntelligenceError(ApplicationError):
    """Base application error for graph intelligence."""


class GraphNotReadyError(ValidationError):
    """Raised when the graph is not completed or not owned by the tenant."""


class GraphIntelligenceLimitError(ValidationError):
    """Raised when request limits exceed hard bounds."""
