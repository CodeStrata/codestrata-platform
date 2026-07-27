"""Engine ingestion controllers — thin adapters over Application Services."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.ingestion.dto import (
    IngestAssessmentRequest,
    IngestAssessmentResponse,
    IngestCompleteAssessmentRequest,
    IngestFailAssessmentRequest,
    IngestRepositoryRequest,
    IngestRepositoryResponse,
)
from codestrata_platform.application.commands.assessment import (
    CompleteAssessmentCommand,
    FailAssessmentCommand,
    RegisterAssessmentCommand,
    StartAssessmentCommand,
)
from codestrata_platform.application.commands.repository import RegisterRepositoryCommand
from codestrata_platform.application.common.errors import ConflictError, NotFoundError
from codestrata_platform.application.common.pagination import PageRequest
from codestrata_platform.application.queries.repository import RepositoryQuery
from codestrata_platform.application.repository.service import normalize_repository_url
from codestrata_platform.domain.assessment import (
    AssessmentId,
    AssessmentReference,
    GeneratedReport,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository import (
    RepositoryId,
    RepositoryProvider,
    RepositoryStatus,
    RepositoryVisibility,
)
from codestrata_platform.domain.workspace.ids import WorkspaceId

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.post(
    "/repositories",
    response_model=IngestRepositoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register repository from Engine",
)
def ingest_register_repository(
    body: IngestRepositoryRequest,
    services: ServicesDep,
) -> IngestRepositoryResponse:
    workspace_id = WorkspaceId(body.workspace_id.strip())
    organization_id = OrganizationId(body.organization_id.strip())
    url = str(body.repository_url).rstrip("/")
    normalized = normalize_repository_url(url)

    existing = services.repositories.list_repositories(
        RepositoryQuery(workspace_id=workspace_id, page=PageRequest(offset=0, limit=500))
    )
    for item in existing.items:
        if (
            item.status is not RepositoryStatus.ARCHIVED
            and normalize_repository_url(item.repository_url) == normalized
        ):
            details = services.repositories.get_repository(item.repository_id)
            return IngestRepositoryResponse(
                repository_id=details.repository_id.value,
                workspace_id=details.workspace_id.value,
                organization_id=details.organization_id.value,
                display_name=details.display_name,
                repository_url=details.repository_url,
                status=details.status.value,
                created=False,
            )

    metadata = dict(body.metadata or {})
    if body.engine_repository_id:
        metadata["engine_repository_id"] = body.engine_repository_id.strip()

    try:
        created = services.repositories.register_repository(
            RegisterRepositoryCommand(
                workspace_id=workspace_id,
                organization_id=organization_id,
                display_name=body.display_name.strip(),
                provider=RepositoryProvider(body.provider.strip().lower()),
                repository_url=url,
                default_branch=body.default_branch.strip(),
                visibility=RepositoryVisibility(body.visibility.strip().lower()),
                description=body.description,
                metadata=metadata or None,
            )
        )
    except ConflictError:
        # Race: another registration landed; re-lookup.
        existing = services.repositories.list_repositories(
            RepositoryQuery(workspace_id=workspace_id, page=PageRequest(offset=0, limit=500))
        )
        for item in existing.items:
            if normalize_repository_url(item.repository_url) == normalized:
                details = services.repositories.get_repository(item.repository_id)
                return IngestRepositoryResponse(
                    repository_id=details.repository_id.value,
                    workspace_id=details.workspace_id.value,
                    organization_id=details.organization_id.value,
                    display_name=details.display_name,
                    repository_url=details.repository_url,
                    status=details.status.value,
                    created=False,
                )
        raise

    return IngestRepositoryResponse(
        repository_id=created.repository_id.value,
        workspace_id=created.workspace_id.value,
        organization_id=created.organization_id.value,
        display_name=created.display_name,
        repository_url=created.repository_url,
        status=created.status.value,
        created=True,
    )


@router.get(
    "/repositories/lookup",
    response_model=IngestRepositoryResponse,
    summary="Lookup repository by workspace and URL",
)
def ingest_lookup_repository(
    services: ServicesDep,
    workspace_id: str = Query(..., min_length=1),
    repository_url: str = Query(..., min_length=1),
) -> IngestRepositoryResponse:
    ws_id = WorkspaceId(workspace_id.strip())
    normalized = normalize_repository_url(repository_url)
    listed = services.repositories.list_repositories(
        RepositoryQuery(workspace_id=ws_id, page=PageRequest(offset=0, limit=500))
    )
    for item in listed.items:
        if (
            item.status is not RepositoryStatus.ARCHIVED
            and normalize_repository_url(item.repository_url) == normalized
        ):
            details = services.repositories.get_repository(item.repository_id)
            return IngestRepositoryResponse(
                repository_id=details.repository_id.value,
                workspace_id=details.workspace_id.value,
                organization_id=details.organization_id.value,
                display_name=details.display_name,
                repository_url=details.repository_url,
                status=details.status.value,
                created=False,
            )
    raise NotFoundError(
        f"Repository not found for URL in workspace {workspace_id}",
        reason_code="repository_not_found",
    )


@router.post(
    "/assessments",
    response_model=IngestAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register assessment from Engine",
)
def ingest_register_assessment(
    body: IngestAssessmentRequest,
    services: ServicesDep,
) -> IngestAssessmentResponse:
    metadata = dict(body.metadata or {})
    metadata["engine_assessment_id"] = body.engine_assessment_id.strip()
    if body.technology_summary:
        metadata["technology_summary"] = body.technology_summary.strip()
    if body.started_at is not None:
        metadata["engine_started_at"] = body.started_at.isoformat()

    created = services.assessments.create_assessment(
        RegisterAssessmentCommand(
            repository_id=RepositoryId(body.repository_id.strip()),
            workspace_id=WorkspaceId(body.workspace_id.strip()),
            engine_version=body.engine_version.strip(),
            assessment_version=body.assessment_version.strip(),
            metadata=metadata,
        )
    )
    return IngestAssessmentResponse(
        assessment_id=created.assessment_id.value,
        repository_id=created.repository_id.value,
        workspace_id=created.workspace_id.value,
        engine_assessment_id=body.engine_assessment_id.strip(),
        engine_version=created.engine_version,
        assessment_version=created.assessment_version,
        status=created.status.value,
    )


@router.post(
    "/assessments/{assessment_id}/start",
    response_model=IngestAssessmentResponse,
    summary="Start ingested assessment",
)
def ingest_start_assessment(
    assessment_id: str,
    services: ServicesDep,
) -> IngestAssessmentResponse:
    model = services.assessments.start_assessment(
        StartAssessmentCommand(assessment_id=AssessmentId(assessment_id.strip()))
    )
    return IngestAssessmentResponse(
        assessment_id=model.assessment_id.value,
        repository_id=model.repository_id.value,
        workspace_id=model.workspace_id.value,
        engine_assessment_id="",
        engine_version=model.engine_version,
        assessment_version=model.assessment_version,
        status=model.status.value,
    )


@router.post(
    "/assessments/{assessment_id}/complete",
    response_model=IngestAssessmentResponse,
    summary="Complete ingested assessment",
)
def ingest_complete_assessment(
    assessment_id: str,
    body: IngestCompleteAssessmentRequest,
    services: ServicesDep,
) -> IngestAssessmentResponse:
    reports = tuple(
        GeneratedReport(report_type=item.report_type, location=item.location)
        for item in body.generated_reports
    )
    refs = tuple(
        AssessmentReference(artifact_uri=item.artifact_uri, label=item.label)
        for item in body.references
    )
    model = services.assessments.complete_assessment(
        CompleteAssessmentCommand(
            assessment_id=AssessmentId(assessment_id.strip()),
            generated_reports=reports,
            references=refs,
        )
    )
    return IngestAssessmentResponse(
        assessment_id=model.assessment_id.value,
        repository_id=model.repository_id.value,
        workspace_id=model.workspace_id.value,
        engine_assessment_id="",
        engine_version=model.engine_version,
        assessment_version=model.assessment_version,
        status=model.status.value,
    )


@router.post(
    "/assessments/{assessment_id}/fail",
    response_model=IngestAssessmentResponse,
    summary="Fail ingested assessment",
)
def ingest_fail_assessment(
    assessment_id: str,
    body: IngestFailAssessmentRequest,
    services: ServicesDep,
) -> IngestAssessmentResponse:
    model = services.assessments.fail_assessment(
        FailAssessmentCommand(
            assessment_id=AssessmentId(assessment_id.strip()),
            reason=body.reason,
        )
    )
    return IngestAssessmentResponse(
        assessment_id=model.assessment_id.value,
        repository_id=model.repository_id.value,
        workspace_id=model.workspace_id.value,
        engine_assessment_id="",
        engine_version=model.engine_version,
        assessment_version=model.assessment_version,
        status=model.status.value,
    )
