"""Concrete WorkspaceService."""

from __future__ import annotations

from codestrata_platform.application.commands.workspace import (
    ActivateWorkspaceCommand,
    CreateWorkspaceCommand,
    DeactivateWorkspaceCommand,
    RenameWorkspaceCommand,
)
from codestrata_platform.application.common.errors import NotFoundError, ValidationError
from codestrata_platform.application.common.pagination import PageResult
from codestrata_platform.application.models.workspace import WorkspaceSummary
from codestrata_platform.application.queries.workspace import WorkspaceQuery
from codestrata_platform.domain.organization import OrganizationRepository, OrganizationStatus
from codestrata_platform.domain.workspace import (
    Workspace,
    WorkspaceId,
    WorkspaceRepository,
)


class DefaultWorkspaceService:
    """Orchestrates Workspace aggregate operations via domain ports."""

    def __init__(
        self,
        *,
        workspaces: WorkspaceRepository,
        organizations: OrganizationRepository,
    ) -> None:
        self._workspaces = workspaces
        self._organizations = organizations

    def create_workspace(self, command: CreateWorkspaceCommand) -> WorkspaceSummary:
        organization = self._organizations.get(command.organization_id)
        if organization is None:
            raise NotFoundError(
                f"Organization not found: {command.organization_id.value}",
                reason_code="organization_not_found",
            )
        if organization.status is not OrganizationStatus.ACTIVE:
            raise ValidationError(
                "Cannot create a workspace under an inactive organization",
                reason_code="organization_inactive",
            )

        workspace = Workspace.create(
            organization_id=command.organization_id,
            name=command.name,
            description=command.description,
        )
        self._workspaces.save(workspace)
        return WorkspaceSummary.from_aggregate(workspace)

    def get_workspace(self, workspace_id: WorkspaceId) -> WorkspaceSummary:
        workspace = self._require_workspace(workspace_id)
        return WorkspaceSummary.from_aggregate(workspace)

    def list_workspaces(self, query: WorkspaceQuery) -> PageResult[WorkspaceSummary]:
        if query.organization_id is None:
            raise ValidationError(
                "WorkspaceQuery requires organization_id",
                reason_code="workspace_query_scope_required",
            )
        candidates = self._workspaces.list_by_organization(query.organization_id)
        filtered = [
            workspace
            for workspace in candidates
            if query.status is None or workspace.status is query.status
        ]
        total = len(filtered)
        page = query.page
        window = filtered[page.offset : page.offset + page.limit]
        items = tuple(WorkspaceSummary.from_aggregate(item) for item in window)
        return PageResult(items=items, total=total, offset=page.offset, limit=page.limit)

    def rename_workspace(self, command: RenameWorkspaceCommand) -> WorkspaceSummary:
        workspace = self._require_workspace(command.workspace_id)
        workspace.rename(command.name)
        self._workspaces.save(workspace)
        return WorkspaceSummary.from_aggregate(workspace)

    def activate_workspace(self, command: ActivateWorkspaceCommand) -> WorkspaceSummary:
        workspace = self._require_workspace(command.workspace_id)
        workspace.activate()
        self._workspaces.save(workspace)
        return WorkspaceSummary.from_aggregate(workspace)

    def deactivate_workspace(self, command: DeactivateWorkspaceCommand) -> WorkspaceSummary:
        workspace = self._require_workspace(command.workspace_id)
        workspace.deactivate()
        self._workspaces.save(workspace)
        return WorkspaceSummary.from_aggregate(workspace)

    def _require_workspace(self, workspace_id: WorkspaceId) -> Workspace:
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            raise NotFoundError(
                f"Workspace not found: {workspace_id.value}",
                reason_code="workspace_not_found",
            )
        return workspace
