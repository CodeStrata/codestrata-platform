"""Persistence port for the Repository aggregate."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.aggregate import Repository
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


class RepositoryRepository(Protocol):
    """Repository port — no persistence implementation in Phase 8.1.1."""

    def get(self, repository_id: RepositoryId) -> Repository | None:
        """Load a repository by id, or None when absent."""

    def save(self, repository: Repository) -> None:
        """Insert or update a repository aggregate."""

    def list_by_workspace(self, workspace_id: WorkspaceId) -> tuple[Repository, ...]:
        """List repositories registered in a workspace."""

    def list_by_organization(
        self,
        organization_id: OrganizationId,
    ) -> tuple[Repository, ...]:
        """List repositories owned under an organization."""
