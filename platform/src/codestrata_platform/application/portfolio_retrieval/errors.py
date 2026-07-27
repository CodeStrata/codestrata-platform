"""Application errors for portfolio retrieval indexing."""

from __future__ import annotations

from codestrata_platform.application.common.errors import ApplicationError, ValidationError


class PortfolioRetrievalApplicationError(ApplicationError):
    """Base application error for portfolio retrieval indexing."""


class PortfolioRetrievalDisabledError(ValidationError):
    """Raised when portfolio retrieval indexing is disabled by configuration."""


class PortfolioRetrievalNotReadyError(ValidationError):
    """Raised when the source portfolio/portfolio snapshot/index is not ready."""


class PortfolioRetrievalConfigurationError(ValidationError):
    """Raised when embedding/indexing configuration is invalid."""
