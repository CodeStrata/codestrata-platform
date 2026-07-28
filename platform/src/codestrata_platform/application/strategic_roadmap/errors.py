"""Application-layer errors for Strategic Portfolio Roadmap."""

from __future__ import annotations

from codestrata_platform.application.common.errors import NotFoundError, ValidationError


class StrategicRoadmapDisabledError(ValidationError):
    """Raised when Strategic Portfolio Roadmap is disabled by configuration."""


class StrategicRoadmapNotReadyError(ValidationError):
    """Raised when the source Executive Intelligence snapshot is not completed."""


class StrategicRoadmapNotFoundError(NotFoundError):
    def __init__(self, reference: str) -> None:
        super().__init__(
            f"Strategic roadmap for '{reference}' was not found",
            reason_code="strategic_roadmap_not_found",
        )
