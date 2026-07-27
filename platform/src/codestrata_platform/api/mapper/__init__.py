"""API mappers: DTO ↔ Application commands/models."""

from __future__ import annotations

from codestrata_platform.api.dto.common import PageMetaDto, PageResponseDto
from codestrata_platform.api.dto.request.assessment import (
    CompleteAssessmentRequest,
    RegisterAssessmentRequest,
)
from codestrata_platform.api.dto.request.organization import CreateOrganizationRequest
from codestrata_platform.api.dto.request.repository import RegisterRepositoryRequest
from codestrata_platform.api.dto.request.workspace import CreateWorkspaceRequest
from codestrata_platform.api.dto.response.assessment import AssessmentResponse
from codestrata_platform.api.dto.response.organization import OrganizationResponse
from codestrata_platform.api.dto.response.repository import (
    RepositoryResponse,
    RepositorySummaryResponse,
)
from codestrata_platform.api.dto.response.workspace import WorkspaceResponse
from codestrata_platform.application.commands.assessment import (
    CompleteAssessmentCommand,
    RegisterAssessmentCommand,
)
from codestrata_platform.application.commands.organization import CreateOrganizationCommand
from codestrata_platform.application.commands.repository import RegisterRepositoryCommand
from codestrata_platform.application.commands.workspace import CreateWorkspaceCommand
from codestrata_platform.application.common.pagination import PageRequest, PageResult
from codestrata_platform.application.models.assessment import AssessmentSummary
from codestrata_platform.application.models.organization import OrganizationSummary
from codestrata_platform.application.models.repository import (
    RepositoryDetails,
    RepositorySummary,
)
from codestrata_platform.application.models.workspace import WorkspaceSummary
from codestrata_platform.domain.assessment import AssessmentReference, GeneratedReport
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository import RepositoryProvider, RepositoryVisibility
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


def page_request(*, page: int, size: int) -> PageRequest:
    return PageRequest(offset=(page - 1) * size, limit=size)


def page_meta(*, page: int, size: int, total: int, sort: str | None = None) -> PageMetaDto:
    total_pages = (total + size - 1) // size if size else 0
    next_page = page + 1 if page < total_pages else None
    previous_page = page - 1 if page > 1 else None
    return PageMetaDto(
        page=page,
        size=size,
        total=total,
        sort=sort,
        next=next_page,
        previous=previous_page,
    )


def to_organization_response(model: OrganizationSummary) -> OrganizationResponse:
    return OrganizationResponse(
        id=model.organization_id.value,
        name=model.name,
        status=model.status.value,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_workspace_response(model: WorkspaceSummary) -> WorkspaceResponse:
    return WorkspaceResponse(
        id=model.workspace_id.value,
        organization_id=model.organization_id.value,
        name=model.name,
        description=model.description,
        status=model.status.value,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_repository_response(model: RepositoryDetails) -> RepositoryResponse:
    return RepositoryResponse(
        id=model.repository_id.value,
        workspace_id=model.workspace_id.value,
        organization_id=model.organization_id.value,
        display_name=model.display_name,
        provider=model.provider.value,
        repository_url=model.repository_url,
        default_branch=model.default_branch,
        visibility=model.visibility.value,
        description=model.description,
        status=model.status.value,
        metadata=dict(model.metadata),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_repository_summary_response(model: RepositorySummary) -> RepositorySummaryResponse:
    return RepositorySummaryResponse(
        id=model.repository_id.value,
        workspace_id=model.workspace_id.value,
        organization_id=model.organization_id.value,
        display_name=model.display_name,
        provider=model.provider.value,
        repository_url=model.repository_url,
        status=model.status.value,
        visibility=model.visibility.value,
    )


def to_assessment_response(model: AssessmentSummary) -> AssessmentResponse:
    return AssessmentResponse(
        id=model.assessment_id.value,
        repository_id=model.repository_id.value,
        workspace_id=model.workspace_id.value,
        engine_version=model.engine_version,
        assessment_version=model.assessment_version,
        status=model.status.value,
        started_at=model.started_at,
        completed_at=model.completed_at,
        failure_reason=model.failure_reason,
        report_count=model.report_count,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_create_organization_command(body: CreateOrganizationRequest) -> CreateOrganizationCommand:
    return CreateOrganizationCommand(name=body.name.strip())


def to_create_workspace_command(body: CreateWorkspaceRequest) -> CreateWorkspaceCommand:
    return CreateWorkspaceCommand(
        organization_id=OrganizationId(body.organization_id.strip()),
        name=body.name.strip(),
        description=body.description,
    )


def to_register_repository_command(body: RegisterRepositoryRequest) -> RegisterRepositoryCommand:
    return RegisterRepositoryCommand(
        workspace_id=WorkspaceId(body.workspace_id.strip()),
        organization_id=OrganizationId(body.organization_id.strip()),
        display_name=body.display_name.strip(),
        provider=RepositoryProvider(body.provider.strip().lower()),
        repository_url=str(body.repository_url).rstrip("/"),
        default_branch=body.default_branch.strip(),
        visibility=RepositoryVisibility(body.visibility.strip().lower()),
        description=body.description,
        metadata=body.metadata,
    )


def to_register_assessment_command(body: RegisterAssessmentRequest) -> RegisterAssessmentCommand:
    return RegisterAssessmentCommand(
        repository_id=RepositoryId(body.repository_id.strip()),
        workspace_id=WorkspaceId(body.workspace_id.strip()),
        engine_version=body.engine_version.strip(),
        assessment_version=body.assessment_version.strip(),
    )


def to_complete_assessment_command(
    assessment_id: str,
    body: CompleteAssessmentRequest,
) -> CompleteAssessmentCommand:
    from codestrata_platform.domain.assessment import AssessmentId

    reports = tuple(
        GeneratedReport(report_type=item.report_type, location=item.location)
        for item in body.generated_reports
    )
    refs = tuple(
        AssessmentReference(artifact_uri=item.artifact_uri, label=item.label)
        for item in body.references
    )
    return CompleteAssessmentCommand(
        assessment_id=AssessmentId(assessment_id.strip()),
        generated_reports=reports,
        references=refs,
    )


def organization_page(
    result: PageResult[OrganizationSummary],
    *,
    page: int,
    size: int,
    sort: str | None,
) -> PageResponseDto[OrganizationResponse]:
    return PageResponseDto(
        items=[to_organization_response(item) for item in result.items],
        pagination=page_meta(page=page, size=size, total=result.total, sort=sort),
    )


def workspace_page(
    result: PageResult[WorkspaceSummary],
    *,
    page: int,
    size: int,
    sort: str | None,
) -> PageResponseDto[WorkspaceResponse]:
    return PageResponseDto(
        items=[to_workspace_response(item) for item in result.items],
        pagination=page_meta(page=page, size=size, total=result.total, sort=sort),
    )


def repository_page(
    result: PageResult[RepositorySummary],
    *,
    page: int,
    size: int,
    sort: str | None,
) -> PageResponseDto[RepositorySummaryResponse]:
    return PageResponseDto(
        items=[to_repository_summary_response(item) for item in result.items],
        pagination=page_meta(page=page, size=size, total=result.total, sort=sort),
    )


def assessment_page(
    result: PageResult[AssessmentSummary],
    *,
    page: int,
    size: int,
    sort: str | None,
) -> PageResponseDto[AssessmentResponse]:
    return PageResponseDto(
        items=[to_assessment_response(item) for item in result.items],
        pagination=page_meta(page=page, size=size, total=result.total, sort=sort),
    )
