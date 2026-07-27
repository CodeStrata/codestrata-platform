"""In-memory WorkspaceRepository."""

from __future__ import annotations

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.workspace import Workspace, WorkspaceId


class InMemoryWorkspaceRepository:
    """Temporary store for Workspace aggregates."""

    def __init__(self) -> None:
        self._items: dict[str, Workspace] = {}

    def get(self, workspace_id: WorkspaceId) -> Workspace | None:
        item = self._items.get(workspace_id.value)
        return item.snapshot() if item is not None else None

    def save(self, workspace: Workspace) -> None:
        self._items[workspace.workspace_id.value] = workspace.snapshot()

    def list_by_organization(self, organization_id: OrganizationId) -> tuple[Workspace, ...]:
        return tuple(
            item.snapshot()
            for item in self._items.values()
            if item.organization_id == organization_id
        )
