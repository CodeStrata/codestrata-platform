"""RepositoryService contract."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.application.commands.repository import (
    ArchiveRepositoryCommand,
    RegisterRepositoryCommand,
    RenameRepositoryCommand,
    UpdateRepositoryMetadataCommand,
)
from codestrata_platform.application.common.pagination import PageResult
from codestrata_platform.application.models.repository import (
    RepositoryDetails,
    RepositorySummary,
)
from codestrata_platform.application.queries.repository import RepositoryQuery
from codestrata_platform.domain.repository import RepositoryId


class RepositoryService(Protocol):
    """Application contract for repository registry operations."""

    def register_repository(self, command: RegisterRepositoryCommand) -> RepositoryDetails:
        """Register a repository with the Platform (no clone)."""

    def get_repository(self, repository_id: RepositoryId) -> RepositoryDetails:
        """Return a registered repository or raise when missing."""

    def list_repositories(self, query: RepositoryQuery) -> PageResult[RepositorySummary]:
        """List repositories matching the query."""

    def archive_repository(self, command: ArchiveRepositoryCommand) -> RepositoryDetails:
        """Archive a repository."""

    def rename_repository(self, command: RenameRepositoryCommand) -> RepositoryDetails:
        """Rename a repository display name."""

    def update_repository_metadata(
        self,
        command: UpdateRepositoryMetadataCommand,
    ) -> RepositoryDetails:
        """Merge repository metadata attributes."""
