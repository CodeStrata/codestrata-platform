"""Persistence port for the Workspace aggregate."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.workspace.aggregate import Workspace
from codestrata_platform.domain.workspace.ids import WorkspaceId


class WorkspaceRepository(Protocol):
    """Workspace port — no persistence implementation in Phase 8.1.1."""

    def get(self, workspace_id: WorkspaceId) -> Workspace | None:
        """Load a workspace by id, or None when absent."""

    def save(self, workspace: Workspace) -> None:
        """Insert or update a workspace aggregate."""

    def list_by_organization(
        self,
        organization_id: OrganizationId,
    ) -> tuple[Workspace, ...]:
        """List workspaces owned by an organization."""
