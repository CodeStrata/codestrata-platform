"""Organization REST controllers."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.dto.common import PageResponseDto
from codestrata_platform.api.dto.request.organization import (
    CreateOrganizationRequest,
    UpdateOrganizationRequest,
)
from codestrata_platform.api.dto.response.organization import OrganizationResponse
from codestrata_platform.api.dto.response.workspace import WorkspaceResponse
from codestrata_platform.api.mapper import (
    organization_page,
    page_request,
    to_create_organization_command,
    to_organization_response,
    workspace_page,
)
from codestrata_platform.application.commands.organization import (
    ActivateOrganizationCommand,
    DeactivateOrganizationCommand,
    RenameOrganizationCommand,
)
from codestrata_platform.application.common.errors import ValidationError
from codestrata_platform.application.queries.organization import OrganizationQuery
from codestrata_platform.application.queries.workspace import WorkspaceQuery
from codestrata_platform.domain.organization import OrganizationId, OrganizationStatus

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create organization",
)
def create_organization(
    body: CreateOrganizationRequest,
    services: ServicesDep,
) -> OrganizationResponse:
    created = services.organizations.create_organization(to_create_organization_command(body))
    return to_organization_response(created)


@router.get(
    "",
    response_model=PageResponseDto[OrganizationResponse],
    summary="List organizations",
)
def list_organizations(
    services: ServicesDep,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    sort: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
) -> PageResponseDto[OrganizationResponse]:
    org_status = OrganizationStatus(status_filter) if status_filter else None
    result = services.organizations.list_organizations(
        OrganizationQuery(status=org_status, page=page_request(page=page, size=size))
    )
    return organization_page(result, page=page, size=size, sort=sort)


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Get organization",
)
def get_organization(organization_id: str, services: ServicesDep) -> OrganizationResponse:
    model = services.organizations.get_organization(OrganizationId(organization_id))
    return to_organization_response(model)


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Update organization",
)
def update_organization(
    organization_id: str,
    body: UpdateOrganizationRequest,
    services: ServicesDep,
) -> OrganizationResponse:
    org_id = OrganizationId(organization_id)
    model = services.organizations.get_organization(org_id)
    if body.name is not None:
        model = services.organizations.rename_organization(
            RenameOrganizationCommand(organization_id=org_id, name=body.name.strip())
        )
    if body.activate is True:
        model = services.organizations.activate_organization(
            ActivateOrganizationCommand(organization_id=org_id)
        )
    elif body.activate is False:
        model = services.organizations.deactivate_organization(
            DeactivateOrganizationCommand(organization_id=org_id)
        )
    if body.name is None and body.activate is None:
        raise ValidationError(
            "At least one of name or activate must be provided",
            reason_code="empty_patch",
        )
    return to_organization_response(model)


@router.delete(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Archive organization (deactivate)",
)
def archive_organization(organization_id: str, services: ServicesDep) -> OrganizationResponse:
    model = services.organizations.deactivate_organization(
        DeactivateOrganizationCommand(organization_id=OrganizationId(organization_id))
    )
    return to_organization_response(model)


@router.get(
    "/{organization_id}/workspaces",
    response_model=PageResponseDto[WorkspaceResponse],
    summary="List workspaces for an organization",
)
def list_organization_workspaces(
    organization_id: str,
    services: ServicesDep,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    sort: str | None = Query(None),
) -> PageResponseDto[WorkspaceResponse]:
    # Ensure organization exists.
    services.organizations.get_organization(OrganizationId(organization_id))
    result = services.workspaces.list_workspaces(
        WorkspaceQuery(
            organization_id=OrganizationId(organization_id),
            page=page_request(page=page, size=size),
        )
    )
    return workspace_page(result, page=page, size=size, sort=sort)
