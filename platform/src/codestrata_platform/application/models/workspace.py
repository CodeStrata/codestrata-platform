"""Workspace application models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.workspace import Workspace, WorkspaceId, WorkspaceStatus


@dataclass(frozen=True, slots=True)
class WorkspaceSummary:
    workspace_id: WorkspaceId
    organization_id: OrganizationId
    name: str
    description: str | None
    status: WorkspaceStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_aggregate(cls, workspace: Workspace) -> WorkspaceSummary:
        return cls(
            workspace_id=workspace.workspace_id,
            organization_id=workspace.organization_id,
            name=workspace.name,
            description=workspace.description,
            status=workspace.status,
            created_at=workspace.audit.created_at.value,
            updated_at=workspace.audit.updated_at.value,
        )
