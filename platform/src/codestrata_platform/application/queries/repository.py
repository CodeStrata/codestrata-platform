"""Repository query models."""

from __future__ import annotations

from dataclasses import dataclass, field

from codestrata_platform.application.common.pagination import PageRequest
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository import RepositoryProvider, RepositoryStatus
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class RepositoryQuery:
    """Filter and paginate registered repositories."""

    workspace_id: WorkspaceId | None = None
    organization_id: OrganizationId | None = None
    status: RepositoryStatus | None = None
    provider: RepositoryProvider | None = None
    page: PageRequest = field(default_factory=PageRequest)
