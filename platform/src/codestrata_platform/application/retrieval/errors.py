"""Application errors for engineering retrieval."""

from __future__ import annotations

from codestrata_platform.application.common.errors import ApplicationError, ValidationError


class RetrievalApplicationError(ApplicationError):
    """Base application error for retrieval indexing."""


class RetrievalNotReadyError(ValidationError):
    """Raised when source snapshot/graph/index is not ready."""


class RetrievalConfigurationError(ValidationError):
    """Raised when embedding/indexing configuration is invalid."""
