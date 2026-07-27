"""McpService contract (future capability)."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.workspace.ids import WorkspaceId


class McpService(Protocol):
    """Contract for Commercial Platform MCP surfaces.

    No implementation in Phase 8.1.1.
    """

    def list_tools(
        self,
        *,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
    ) -> tuple[str, ...]:
        """List MCP tools available for a workspace."""
