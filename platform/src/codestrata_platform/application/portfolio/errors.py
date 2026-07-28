"""Application-layer portfolio errors."""

from __future__ import annotations

from codestrata_platform.application.common.errors import ApplicationError, NotFoundError


class PortfolioApplicationError(ApplicationError):
    """Base application error for portfolio operations."""


class PortfolioNotFoundError(NotFoundError):
    def __init__(self, portfolio_id: str) -> None:
        super().__init__(
            f"Portfolio '{portfolio_id}' was not found",
            reason_code="portfolio_not_found",
        )


class PortfolioSnapshotNotFoundError(NotFoundError):
    def __init__(self, portfolio_snapshot_id: str) -> None:
        super().__init__(
            f"Portfolio snapshot '{portfolio_snapshot_id}' was not found",
            reason_code="portfolio_snapshot_not_found",
        )
