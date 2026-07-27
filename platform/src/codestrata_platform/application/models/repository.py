"""Repository application models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository import (
    Repository,
    RepositoryId,
    RepositoryProvider,
    RepositoryStatus,
    RepositoryVisibility,
)
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class RepositorySummary:
    repository_id: RepositoryId
    workspace_id: WorkspaceId
    organization_id: OrganizationId
    display_name: str
    provider: RepositoryProvider
    repository_url: str
    status: RepositoryStatus
    visibility: RepositoryVisibility


@dataclass(frozen=True, slots=True)
class RepositoryDetails:
    repository_id: RepositoryId
    workspace_id: WorkspaceId
    organization_id: OrganizationId
    display_name: str
    provider: RepositoryProvider
    repository_url: str
    default_branch: str
    visibility: RepositoryVisibility
    description: str | None
    status: RepositoryStatus
    metadata: Mapping[str, str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_aggregate(cls, repository: Repository) -> RepositoryDetails:
        return cls(
            repository_id=repository.repository_id,
            workspace_id=repository.workspace_id,
            organization_id=repository.organization_id,
            display_name=repository.display_name,
            provider=repository.provider,
            repository_url=repository.repository_url,
            default_branch=repository.default_branch,
            visibility=repository.visibility,
            description=repository.description,
            status=repository.status,
            metadata=dict(repository.metadata.attributes),
            created_at=repository.audit.created_at.value,
            updated_at=repository.audit.updated_at.value,
        )

    def to_summary(self) -> RepositorySummary:
        return RepositorySummary(
            repository_id=self.repository_id,
            workspace_id=self.workspace_id,
            organization_id=self.organization_id,
            display_name=self.display_name,
            provider=self.provider,
            repository_url=self.repository_url,
            status=self.status,
            visibility=self.visibility,
        )
