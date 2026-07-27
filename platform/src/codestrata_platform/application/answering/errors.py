"""Application errors for engineering answering."""

from __future__ import annotations

from codestrata_platform.application.common.errors import ApplicationError, ValidationError


class AnsweringApplicationError(ApplicationError):
    """Base application error for answering."""


class AnsweringDisabledError(ValidationError):
    """Raised when answering is disabled by configuration."""


class AnsweringNotReadyError(ValidationError):
    """Raised when retrieval index or sources are not ready."""


class AnsweringConfigurationError(ValidationError):
    """Raised when LLM/answering configuration is invalid."""


class AnsweringGroundingError(ValidationError):
    """Raised when generated answers fail grounding validation."""
