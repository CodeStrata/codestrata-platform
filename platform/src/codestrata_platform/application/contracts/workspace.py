"""WorkspaceService contract."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.application.commands.workspace import (
    ActivateWorkspaceCommand,
    CreateWorkspaceCommand,
    DeactivateWorkspaceCommand,
    RenameWorkspaceCommand,
)
from codestrata_platform.application.common.pagination import PageResult
from codestrata_platform.application.models.workspace import WorkspaceSummary
from codestrata_platform.application.queries.workspace import WorkspaceQuery
from codestrata_platform.domain.workspace import WorkspaceId


class WorkspaceService(Protocol):
    """Application contract for workspace lifecycle operations."""

    def create_workspace(self, command: CreateWorkspaceCommand) -> WorkspaceSummary:
        """Create an active workspace under an organization."""

    def get_workspace(self, workspace_id: WorkspaceId) -> WorkspaceSummary:
        """Return a workspace or raise when missing."""

    def list_workspaces(self, query: WorkspaceQuery) -> PageResult[WorkspaceSummary]:
        """List workspaces matching the query."""

    def rename_workspace(self, command: RenameWorkspaceCommand) -> WorkspaceSummary:
        """Rename a workspace."""

    def activate_workspace(self, command: ActivateWorkspaceCommand) -> WorkspaceSummary:
        """Activate a workspace."""

    def deactivate_workspace(self, command: DeactivateWorkspaceCommand) -> WorkspaceSummary:
        """Deactivate a workspace."""
