"""Workspace query models."""

from __future__ import annotations

from dataclasses import dataclass, field

from codestrata_platform.application.common.pagination import PageRequest
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.workspace import WorkspaceStatus


@dataclass(frozen=True, slots=True)
class WorkspaceQuery:
    organization_id: OrganizationId | None = None
    status: WorkspaceStatus | None = None
    page: PageRequest = field(default_factory=PageRequest)
