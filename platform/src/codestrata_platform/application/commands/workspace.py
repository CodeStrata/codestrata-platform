"""Workspace lifecycle commands."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class CreateWorkspaceCommand:
    organization_id: OrganizationId
    name: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class RenameWorkspaceCommand:
    workspace_id: WorkspaceId
    name: str


@dataclass(frozen=True, slots=True)
class ActivateWorkspaceCommand:
    workspace_id: WorkspaceId


@dataclass(frozen=True, slots=True)
class DeactivateWorkspaceCommand:
    workspace_id: WorkspaceId
