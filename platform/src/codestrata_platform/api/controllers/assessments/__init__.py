"""Assessment REST controllers."""

from __future__ import annotations

from fastapi import APIRouter, status

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.dto.request.assessment import (
    CompleteAssessmentRequest,
    FailAssessmentRequest,
    RegisterAssessmentRequest,
)
from codestrata_platform.api.dto.response.assessment import AssessmentResponse
from codestrata_platform.api.mapper import (
    to_assessment_response,
    to_complete_assessment_command,
    to_register_assessment_command,
)
from codestrata_platform.application.commands.assessment import (
    FailAssessmentCommand,
    StartAssessmentCommand,
)
from codestrata_platform.domain.assessment import AssessmentId

router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.post(
    "",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register assessment",
)
def register_assessment(
    body: RegisterAssessmentRequest,
    services: ServicesDep,
) -> AssessmentResponse:
    created = services.assessments.create_assessment(to_register_assessment_command(body))
    return to_assessment_response(created)


@router.get(
    "/{assessment_id}",
    response_model=AssessmentResponse,
    summary="Get assessment",
)
def get_assessment(assessment_id: str, services: ServicesDep) -> AssessmentResponse:
    model = services.assessments.get_assessment(AssessmentId(assessment_id))
    return to_assessment_response(model)


@router.post(
    "/{assessment_id}/start",
    response_model=AssessmentResponse,
    summary="Start assessment",
)
def start_assessment(assessment_id: str, services: ServicesDep) -> AssessmentResponse:
    model = services.assessments.start_assessment(
        StartAssessmentCommand(assessment_id=AssessmentId(assessment_id))
    )
    return to_assessment_response(model)


@router.post(
    "/{assessment_id}/complete",
    response_model=AssessmentResponse,
    summary="Complete assessment",
)
def complete_assessment(
    assessment_id: str,
    body: CompleteAssessmentRequest,
    services: ServicesDep,
) -> AssessmentResponse:
    model = services.assessments.complete_assessment(
        to_complete_assessment_command(assessment_id, body)
    )
    return to_assessment_response(model)


@router.post(
    "/{assessment_id}/fail",
    response_model=AssessmentResponse,
    summary="Fail assessment",
)
def fail_assessment(
    assessment_id: str,
    body: FailAssessmentRequest,
    services: ServicesDep,
) -> AssessmentResponse:
    model = services.assessments.fail_assessment(
        FailAssessmentCommand(assessment_id=AssessmentId(assessment_id), reason=body.reason)
    )
    return to_assessment_response(model)
