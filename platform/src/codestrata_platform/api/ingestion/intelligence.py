"""Assessment intelligence ingestion controllers."""

from __future__ import annotations

from fastapi import APIRouter, Body, Response, status

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.ingestion.intelligence_dto import (
    IntelligenceDetailsResponse,
    IntelligenceProcessRequest,
    IntelligenceProcessResponse,
)
from codestrata_platform.application.commands.intelligence import (
    ProcessAssessmentIntelligenceCommand,
)
from codestrata_platform.application.models.intelligence import IntelligenceDetails
from codestrata_platform.application.queries.intelligence import (
    GetLatestAssessmentIntelligenceQuery,
)
from codestrata_platform.domain.assessment.ids import AssessmentId

router = APIRouter(
    prefix="/ingestion/assessments/{assessment_id}/intelligence",
    tags=["Ingestion Intelligence"],
)

_OPTIONAL_PROCESS_BODY = Body(default=None)


@router.post(
    "",
    response_model=IntelligenceProcessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register and process assessment intelligence",
)
def register_and_process_intelligence(
    assessment_id: str,
    services: ServicesDep,
    response: Response,
    body: IntelligenceProcessRequest | None = _OPTIONAL_PROCESS_BODY,
) -> IntelligenceProcessResponse:
    return _process(assessment_id, services, response, body)


@router.post(
    "/process",
    response_model=IntelligenceProcessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Process completed assessment artifacts into intelligence",
)
def process_intelligence(
    assessment_id: str,
    services: ServicesDep,
    response: Response,
    body: IntelligenceProcessRequest | None = _OPTIONAL_PROCESS_BODY,
) -> IntelligenceProcessResponse:
    return _process(assessment_id, services, response, body)


@router.get(
    "",
    response_model=IntelligenceDetailsResponse,
    summary="Get latest assessment intelligence",
)
def get_intelligence(assessment_id: str, services: ServicesDep) -> IntelligenceDetailsResponse:
    details = services.intelligence.get_latest_assessment_intelligence(
        GetLatestAssessmentIntelligenceQuery(assessment_id=AssessmentId(assessment_id.strip()))
    )
    return _details_response(details)


def _process(
    assessment_id: str,
    services: ServicesDep,
    response: Response,
    body: IntelligenceProcessRequest | None,
) -> IntelligenceProcessResponse:
    result = services.intelligence.process_assessment_intelligence(
        ProcessAssessmentIntelligenceCommand(
            assessment_id=AssessmentId(assessment_id.strip()),
            artifact_ids=tuple(body.artifact_ids) if body and body.artifact_ids else None,
            parser_version=(body.parser_version if body and body.parser_version else "1.0.0"),
        )
    )
    if result.idempotent:
        response.status_code = status.HTTP_200_OK
    details = result.intelligence
    return IntelligenceProcessResponse(
        intelligence_id=details.intelligence_id.value,
        assessment_id=details.assessment_id.value,
        revision=details.revision,
        status=details.status.value,
        created=result.created,
        idempotent=result.idempotent,
        finding_count=details.finding_count,
        metric_count=details.metric_count,
        recommendation_count=details.recommendation_count,
        failure_reason=details.failure_reason,
    )


def _details_response(details: IntelligenceDetails) -> IntelligenceDetailsResponse:
    return IntelligenceDetailsResponse(
        intelligence_id=details.intelligence_id.value,
        organization_id=details.organization_id.value,
        workspace_id=details.workspace_id.value,
        repository_id=details.repository_id.value,
        assessment_id=details.assessment_id.value,
        engine_assessment_id=details.engine_assessment_id,
        schema_version=details.schema_version,
        parser_version=details.parser_version,
        revision=details.revision,
        idempotency_key=details.idempotency_key,
        status=details.status.value,
        source_artifact_ids=list(details.source_artifact_ids),
        finding_count=details.finding_count,
        metric_count=details.metric_count,
        recommendation_count=details.recommendation_count,
        failure_reason=details.failure_reason,
        diagnostics=list(details.diagnostics),
        created_at=details.created_at,
        updated_at=details.updated_at,
        completed_at=details.completed_at,
    )
