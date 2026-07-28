"""Application errors for graph intelligence."""

from __future__ import annotations

from codestrata_platform.application.common.errors import (
    ApplicationError,
    NotFoundError,
    ValidationError,
)


class GraphIntelligenceError(ApplicationError):
    """Base application error for graph intelligence."""


class GraphNotReadyError(ValidationError):
    """Raised when the graph is not completed (not for tenant isolation)."""


class GraphNotFoundError(NotFoundError):
    """Raised when a graph is missing or not owned by the claimed tenant."""

    def __init__(self, graph_id: str) -> None:
        super().__init__(
            f"Knowledge graph not found: {graph_id}",
            reason_code="knowledge_graph_not_found",
        )


class GraphIntelligenceLimitError(ValidationError):
    """Raised when request limits exceed hard bounds."""
