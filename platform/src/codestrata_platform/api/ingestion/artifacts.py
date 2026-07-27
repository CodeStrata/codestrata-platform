"""Artifact ingestion controllers."""

from __future__ import annotations

from fastapi import APIRouter, Header, Request, Response, status

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.ingestion.dto import (
    ArtifactDetailsResponse,
    ArtifactSummaryResponse,
    FailArtifactRequest,
    RegisterArtifactRequest,
    RegisterArtifactResponse,
    UploadArtifactResponse,
)
from codestrata_platform.application.commands.artifact import (
    CompleteArtifactCommand,
    FailArtifactCommand,
    RegisterArtifactCommand,
    UploadArtifactCommand,
)
from codestrata_platform.application.models.artifact import ArtifactDetails
from codestrata_platform.application.queries.artifact import (
    GetArtifactQuery,
    ListAssessmentArtifactsQuery,
)
from codestrata_platform.domain.artifact import (
    ArtifactFormat,
    ArtifactType,
    AssessmentArtifactId,
)
from codestrata_platform.domain.assessment.ids import AssessmentId

router = APIRouter(
    prefix="/ingestion/assessments/{assessment_id}/artifacts",
    tags=["Ingestion Artifacts"],
)


@router.post(
    "",
    response_model=RegisterArtifactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register assessment artifact",
)
def register_artifact(
    assessment_id: str,
    body: RegisterArtifactRequest,
    services: ServicesDep,
    response: Response,
) -> RegisterArtifactResponse:
    result = services.artifacts.register_artifact(
        RegisterArtifactCommand(
            assessment_id=AssessmentId(assessment_id.strip()),
            engine_assessment_id=body.engine_assessment_id.strip(),
            artifact_type=ArtifactType(body.artifact_type.strip().lower()),
            format=ArtifactFormat(body.format.strip().lower()),
            schema_version=body.schema_version.strip(),
            checksum=body.checksum.strip().lower(),
            size_bytes=body.size_bytes,
            metadata=body.metadata,
        )
    )
    if not result.created:
        response.status_code = status.HTTP_200_OK
    return RegisterArtifactResponse(
        artifact_id=result.artifact_id.value,
        assessment_id=result.assessment_id.value,
        artifact_type=result.artifact_type.value,
        checksum=result.checksum,
        status=result.status.value,
        version=result.version,
        created=result.created,
    )


@router.put(
    "/{artifact_id}",
    response_model=UploadArtifactResponse,
    summary="Upload artifact content",
)
async def upload_artifact(
    assessment_id: str,
    artifact_id: str,
    request: Request,
    services: ServicesDep,
    x_codestrata_checksum: str = Header(..., alias="X-CodeStrata-Checksum"),
) -> UploadArtifactResponse:
    _ = assessment_id
    content = await request.body()
    result = services.artifacts.upload_artifact(
        UploadArtifactCommand(
            artifact_id=AssessmentArtifactId(artifact_id.strip()),
            content=content,
            declared_checksum=x_codestrata_checksum.strip().lower(),
        )
    )
    return UploadArtifactResponse(
        artifact_id=result.artifact_id.value,
        status=result.status.value,
        checksum=result.checksum,
        size_bytes=result.size_bytes,
        storage_key=result.storage_key,
    )


@router.post(
    "/{artifact_id}/complete",
    response_model=ArtifactDetailsResponse,
    summary="Complete artifact ingestion",
)
def complete_artifact(
    assessment_id: str,
    artifact_id: str,
    services: ServicesDep,
) -> ArtifactDetailsResponse:
    _ = assessment_id
    details = services.artifacts.complete_artifact(
        CompleteArtifactCommand(artifact_id=AssessmentArtifactId(artifact_id.strip()))
    )
    return _details_response(details)


@router.post(
    "/{artifact_id}/fail",
    response_model=ArtifactDetailsResponse,
    summary="Fail artifact ingestion",
)
def fail_artifact(
    assessment_id: str,
    artifact_id: str,
    body: FailArtifactRequest,
    services: ServicesDep,
) -> ArtifactDetailsResponse:
    _ = assessment_id
    details = services.artifacts.fail_artifact(
        FailArtifactCommand(
            artifact_id=AssessmentArtifactId(artifact_id.strip()),
            reason=body.reason,
        )
    )
    return _details_response(details)


@router.get(
    "",
    response_model=list[ArtifactSummaryResponse],
    summary="List assessment artifacts",
)
def list_artifacts(assessment_id: str, services: ServicesDep) -> list[ArtifactSummaryResponse]:
    items = services.artifacts.list_assessment_artifacts(
        ListAssessmentArtifactsQuery(assessment_id=AssessmentId(assessment_id.strip()))
    )
    return [
        ArtifactSummaryResponse(
            artifact_id=item.artifact_id.value,
            assessment_id=item.assessment_id.value,
            artifact_type=item.artifact_type.value,
            format=item.format.value,
            checksum=item.checksum,
            size_bytes=item.size_bytes,
            status=item.status.value,
            version=item.version,
            schema_version=item.schema_version,
        )
        for item in items
    ]


@router.get(
    "/{artifact_id}",
    response_model=ArtifactDetailsResponse,
    summary="Get artifact metadata",
)
def get_artifact(
    assessment_id: str,
    artifact_id: str,
    services: ServicesDep,
) -> ArtifactDetailsResponse:
    _ = assessment_id
    details = services.artifacts.get_artifact(
        GetArtifactQuery(artifact_id=AssessmentArtifactId(artifact_id.strip()))
    )
    return _details_response(details)


def _details_response(details: ArtifactDetails) -> ArtifactDetailsResponse:
    return ArtifactDetailsResponse(
        artifact_id=details.artifact_id.value,
        organization_id=details.organization_id.value,
        workspace_id=details.workspace_id.value,
        repository_id=details.repository_id.value,
        assessment_id=details.assessment_id.value,
        engine_assessment_id=details.engine_assessment_id,
        artifact_type=details.artifact_type.value,
        format=details.format.value,
        schema_version=details.schema_version,
        checksum=details.checksum,
        size_bytes=details.size_bytes,
        status=details.status.value,
        version=details.version,
        metadata=details.metadata,
        storage_key=details.storage_key,
        created_at=details.created_at,
        updated_at=details.updated_at,
        completed_at=details.completed_at,
        failure_reason=details.failure_reason,
    )
