"""Application errors for knowledge graph projection."""

from __future__ import annotations

from codestrata_platform.application.common.errors import ApplicationError, ValidationError


class KnowledgeGraphApplicationError(ApplicationError):
    """Base application error for engineering knowledge graphs."""


class GraphTraversalLimitError(ValidationError):
    """Raised when a graph traversal exceeds configured bounds."""
