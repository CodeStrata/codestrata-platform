"""Application-layer errors for Executive Intelligence."""

from __future__ import annotations

from codestrata_platform.application.common.errors import NotFoundError, ValidationError


class ExecutiveIntelligenceDisabledError(ValidationError):
    """Raised when Executive Intelligence is disabled by configuration."""


class ExecutiveIntelligenceNotFoundError(NotFoundError):
    def __init__(self, executive_intelligence_id: str) -> None:
        super().__init__(
            f"Executive intelligence '{executive_intelligence_id}' was not found",
            reason_code="executive_intelligence_not_found",
        )


class ExecutiveIntelligenceNotReadyError(ValidationError):
    """Raised when the source portfolio snapshot is not completed."""
