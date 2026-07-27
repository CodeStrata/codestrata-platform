"""Workspace REST controllers."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.dto.common import PageResponseDto
from codestrata_platform.api.dto.request.workspace import (
    CreateWorkspaceRequest,
    UpdateWorkspaceRequest,
)
from codestrata_platform.api.dto.response.repository import RepositorySummaryResponse
from codestrata_platform.api.dto.response.workspace import WorkspaceResponse
from codestrata_platform.api.mapper import (
    page_request,
    repository_page,
    to_create_workspace_command,
    to_workspace_response,
    workspace_page,
)
from codestrata_platform.application.commands.workspace import (
    ActivateWorkspaceCommand,
    DeactivateWorkspaceCommand,
    RenameWorkspaceCommand,
)
from codestrata_platform.application.common.errors import ValidationError
from codestrata_platform.application.queries.repository import RepositoryQuery
from codestrata_platform.application.queries.workspace import WorkspaceQuery
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.workspace import WorkspaceId, WorkspaceStatus

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workspace",
)
def create_workspace(body: CreateWorkspaceRequest, services: ServicesDep) -> WorkspaceResponse:
    created = services.workspaces.create_workspace(to_create_workspace_command(body))
    return to_workspace_response(created)


@router.get(
    "",
    response_model=PageResponseDto[WorkspaceResponse],
    summary="List workspaces",
)
def list_workspaces(
    services: ServicesDep,
    organization_id: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    sort: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
) -> PageResponseDto[WorkspaceResponse]:
    ws_status = WorkspaceStatus(status_filter) if status_filter else None
    result = services.workspaces.list_workspaces(
        WorkspaceQuery(
            organization_id=OrganizationId(organization_id),
            status=ws_status,
            page=page_request(page=page, size=size),
        )
    )
    return workspace_page(result, page=page, size=size, sort=sort)


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Get workspace",
)
def get_workspace(workspace_id: str, services: ServicesDep) -> WorkspaceResponse:
    model = services.workspaces.get_workspace(WorkspaceId(workspace_id))
    return to_workspace_response(model)


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Update workspace",
)
def update_workspace(
    workspace_id: str,
    body: UpdateWorkspaceRequest,
    services: ServicesDep,
) -> WorkspaceResponse:
    ws_id = WorkspaceId(workspace_id)
    model = services.workspaces.get_workspace(ws_id)
    if body.name is not None:
        model = services.workspaces.rename_workspace(
            RenameWorkspaceCommand(workspace_id=ws_id, name=body.name.strip())
        )
    if body.activate is True:
        model = services.workspaces.activate_workspace(ActivateWorkspaceCommand(workspace_id=ws_id))
    elif body.activate is False:
        model = services.workspaces.deactivate_workspace(
            DeactivateWorkspaceCommand(workspace_id=ws_id)
        )
    if body.name is None and body.activate is None:
        raise ValidationError(
            "At least one of name or activate must be provided",
            reason_code="empty_patch",
        )
    return to_workspace_response(model)


@router.delete(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Archive workspace (deactivate)",
)
def archive_workspace(workspace_id: str, services: ServicesDep) -> WorkspaceResponse:
    model = services.workspaces.deactivate_workspace(
        DeactivateWorkspaceCommand(workspace_id=WorkspaceId(workspace_id))
    )
    return to_workspace_response(model)


@router.get(
    "/{workspace_id}/repositories",
    response_model=PageResponseDto[RepositorySummaryResponse],
    summary="List repositories in a workspace",
)
def list_workspace_repositories(
    workspace_id: str,
    services: ServicesDep,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    sort: str | None = Query(None),
) -> PageResponseDto[RepositorySummaryResponse]:
    services.workspaces.get_workspace(WorkspaceId(workspace_id))
    result = services.repositories.list_repositories(
        RepositoryQuery(
            workspace_id=WorkspaceId(workspace_id),
            page=page_request(page=page, size=size),
        )
    )
    return repository_page(result, page=page, size=size, sort=sort)
