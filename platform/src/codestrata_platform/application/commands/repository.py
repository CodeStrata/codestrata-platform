"""Repository registry commands."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository import (
    RepositoryId,
    RepositoryProvider,
    RepositoryVisibility,
)
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class RegisterRepositoryCommand:
    workspace_id: WorkspaceId
    organization_id: OrganizationId
    display_name: str
    provider: RepositoryProvider
    repository_url: str
    default_branch: str = "main"
    visibility: RepositoryVisibility = RepositoryVisibility.PRIVATE
    description: str | None = None
    metadata: Mapping[str, str] | None = None


@dataclass(frozen=True, slots=True)
class RenameRepositoryCommand:
    repository_id: RepositoryId
    display_name: str


@dataclass(frozen=True, slots=True)
class ArchiveRepositoryCommand:
    repository_id: RepositoryId


@dataclass(frozen=True, slots=True)
class UpdateRepositoryMetadataCommand:
    repository_id: RepositoryId
    updates: Mapping[str, str]
