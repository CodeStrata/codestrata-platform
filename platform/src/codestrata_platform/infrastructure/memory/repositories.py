"""In-memory RepositoryRepository."""

from __future__ import annotations

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository import Repository, RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


class InMemoryRepositoryRepository:
    """Temporary store for Repository aggregates."""

    def __init__(self) -> None:
        self._items: dict[str, Repository] = {}

    def get(self, repository_id: RepositoryId) -> Repository | None:
        item = self._items.get(repository_id.value)
        return item.snapshot() if item is not None else None

    def save(self, repository: Repository) -> None:
        self._items[repository.repository_id.value] = repository.snapshot()

    def list_by_workspace(self, workspace_id: WorkspaceId) -> tuple[Repository, ...]:
        return tuple(
            item.snapshot()
            for item in self._items.values()
            if item.workspace_id == workspace_id
        )

    def list_by_organization(self, organization_id: OrganizationId) -> tuple[Repository, ...]:
        return tuple(
            item.snapshot()
            for item in self._items.values()
            if item.organization_id == organization_id
        )
