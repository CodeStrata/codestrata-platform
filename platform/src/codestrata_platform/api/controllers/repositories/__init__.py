"""Repository REST controllers."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.dto.common import PageResponseDto
from codestrata_platform.api.dto.request.repository import (
    RegisterRepositoryRequest,
    UpdateRepositoryRequest,
)
from codestrata_platform.api.dto.response.assessment import AssessmentResponse
from codestrata_platform.api.dto.response.repository import (
    RepositoryResponse,
    RepositorySummaryResponse,
)
from codestrata_platform.api.mapper import (
    page_request,
    repository_page,
    to_assessment_response,
    to_register_repository_command,
    to_repository_response,
)
from codestrata_platform.application.commands.repository import (
    ArchiveRepositoryCommand,
    RenameRepositoryCommand,
    UpdateRepositoryMetadataCommand,
)
from codestrata_platform.application.common.errors import ValidationError
from codestrata_platform.application.queries.repository import RepositoryQuery
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository import RepositoryId, RepositoryStatus
from codestrata_platform.domain.workspace.ids import WorkspaceId

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.post(
    "",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register repository",
)
def register_repository(
    body: RegisterRepositoryRequest,
    services: ServicesDep,
) -> RepositoryResponse:
    created = services.repositories.register_repository(to_register_repository_command(body))
    return to_repository_response(created)


@router.get(
    "",
    response_model=PageResponseDto[RepositorySummaryResponse],
    summary="List repositories",
)
def list_repositories(
    services: ServicesDep,
    workspace_id: str | None = Query(None),
    organization_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    sort: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
) -> PageResponseDto[RepositorySummaryResponse]:
    repo_status = RepositoryStatus(status_filter) if status_filter else None
    result = services.repositories.list_repositories(
        RepositoryQuery(
            workspace_id=WorkspaceId(workspace_id) if workspace_id else None,
            organization_id=OrganizationId(organization_id) if organization_id else None,
            status=repo_status,
            page=page_request(page=page, size=size),
        )
    )
    return repository_page(result, page=page, size=size, sort=sort)


@router.get(
    "/{repository_id}",
    response_model=RepositoryResponse,
    summary="Get repository",
)
def get_repository(repository_id: str, services: ServicesDep) -> RepositoryResponse:
    model = services.repositories.get_repository(RepositoryId(repository_id))
    return to_repository_response(model)


@router.patch(
    "/{repository_id}",
    response_model=RepositoryResponse,
    summary="Update repository (rename / metadata)",
)
def update_repository(
    repository_id: str,
    body: UpdateRepositoryRequest,
    services: ServicesDep,
) -> RepositoryResponse:
    repo_id = RepositoryId(repository_id)
    model = services.repositories.get_repository(repo_id)
    if body.display_name is not None:
        model = services.repositories.rename_repository(
            RenameRepositoryCommand(repository_id=repo_id, display_name=body.display_name.strip())
        )
    if body.metadata is not None:
        model = services.repositories.update_repository_metadata(
            UpdateRepositoryMetadataCommand(repository_id=repo_id, updates=body.metadata)
        )
    if body.display_name is None and body.metadata is None:
        raise ValidationError(
            "At least one of display_name or metadata must be provided",
            reason_code="empty_patch",
        )
    return to_repository_response(model)


@router.delete(
    "/{repository_id}",
    response_model=RepositoryResponse,
    summary="Archive repository (logical delete)",
)
def archive_repository(repository_id: str, services: ServicesDep) -> RepositoryResponse:
    model = services.repositories.archive_repository(
        ArchiveRepositoryCommand(repository_id=RepositoryId(repository_id))
    )
    return to_repository_response(model)


@router.get(
    "/{repository_id}/assessments",
    response_model=list[AssessmentResponse],
    summary="Repository assessment history",
)
def list_repository_assessments(
    repository_id: str,
    services: ServicesDep,
) -> list[AssessmentResponse]:
    history = services.assessments.list_assessment_history(RepositoryId(repository_id))
    return [to_assessment_response(item) for item in history]
