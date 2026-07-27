"""Application errors for portfolio answering."""

from __future__ import annotations

from codestrata_platform.application.common.errors import ApplicationError, ValidationError


class PortfolioAnsweringApplicationError(ApplicationError):
    """Base application error for portfolio answering."""


class PortfolioAnsweringDisabledError(ValidationError):
    """Raised when portfolio answering is disabled by configuration."""


class PortfolioAnsweringNotReadyError(ValidationError):
    """Raised when portfolio retrieval index or sources are not ready."""


class PortfolioAnsweringConfigurationError(ValidationError):
    """Raised when LLM/portfolio answering configuration is invalid."""


class PortfolioAnsweringGroundingError(ValidationError):
    """Raised when generated portfolio answers fail grounding validation."""
