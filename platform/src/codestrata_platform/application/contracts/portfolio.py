"""PortfolioService contract."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.workspace.ids import WorkspaceId


class PortfolioService(Protocol):
    """Contract for Portfolio Intelligence across repositories."""

    def summarize_portfolio(
        self,
        *,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId | None = None,
    ) -> object:
        """Produce a portfolio-level intelligence summary."""
