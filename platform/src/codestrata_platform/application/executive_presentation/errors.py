"""Application-layer errors for Executive Presentation."""

from __future__ import annotations

from codestrata_platform.application.common.errors import NotFoundError, ValidationError


class ExecutivePresentationDisabledError(ValidationError):
    """Raised when Executive Presentation is disabled by configuration."""


class ExecutivePresentationNotReadyError(ValidationError):
    """Raised when the source Executive Intelligence snapshot is not completed."""


class ExecutivePresentationNotFoundError(NotFoundError):
    def __init__(self, reference: str) -> None:
        super().__init__(
            f"Executive presentation for '{reference}' was not found",
            reason_code="executive_presentation_not_found",
        )
