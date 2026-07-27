"""Thin Engineering Answering controllers."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from codestrata_platform.api.answering.dto import (
    AnswerFeedbackRequest,
    AnswerFeedbackResponse,
    AskAnswerRequest,
    EngineeringAnswerResponse,
)
from codestrata_platform.api.answering.mappers import answer_response, feedback_response
from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.application.answering.commands import (
    AskEngineeringQuestionCommand,
    GetAnswerRunQuery,
    ListRepositoryAnswersQuery,
    SubmitAnswerFeedbackCommand,
)
from codestrata_platform.application.common.errors import ValidationError
from codestrata_platform.domain.answering.identifiers import AnswerRunId
from codestrata_platform.domain.answering.lifecycle import QuestionType
from codestrata_platform.domain.answering.question import QuestionScope
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.identifiers import RetrievalIndexId
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType

router = APIRouter(tags=["Answering"])


def _build_ask_command(
    body: AskAnswerRequest,
    *,
    repository_id: str,
) -> AskEngineeringQuestionCommand:
    content_types = (
        tuple(RetrievalContentType(item) for item in body.content_types)
        if body.content_types
        else ()
    )
    return AskEngineeringQuestionCommand(
        question=body.question,
        scope=QuestionScope(
            organization_id=body.organization_id.strip(),
            workspace_id=body.workspace_id.strip(),
            repository_id=repository_id.strip(),
            retrieval_index_id=(
                body.retrieval_index_id.strip() if body.retrieval_index_id is not None else None
            ),
            canonical_ids=tuple(body.canonical_ids or ()),
            graph_node_ids=tuple(body.graph_node_ids or ()),
            content_types=content_types,
        ),
        question_type=(
            QuestionType(body.question_type) if body.question_type is not None else None
        ),
        retrieval_index_id=(
            RetrievalIndexId(body.retrieval_index_id.strip())
            if body.retrieval_index_id is not None
            else None
        ),
        include_diagnostics=body.include_diagnostics,
        use_cache=body.use_cache,
    )


@router.post(
    "/answers",
    response_model=EngineeringAnswerResponse,
    status_code=status.HTTP_201_CREATED,
)
def ask_answer(
    body: AskAnswerRequest,
    services: ServicesDep,
) -> EngineeringAnswerResponse:
    if body.repository_id is None or not body.repository_id.strip():
        raise ValidationError(
            "repository_id is required",
            reason_code="missing_repository_id",
        )
    result = services.answering.ask(
        _build_ask_command(body, repository_id=body.repository_id)
    )
    return answer_response(result)


@router.post(
    "/repositories/{repository_id}/ask",
    response_model=EngineeringAnswerResponse,
    status_code=status.HTTP_201_CREATED,
)
def ask_repository_answer(
    repository_id: str,
    body: AskAnswerRequest,
    services: ServicesDep,
) -> EngineeringAnswerResponse:
    result = services.answering.ask(
        _build_ask_command(body, repository_id=repository_id)
    )
    return answer_response(result)


@router.get(
    "/answers/{answer_run_id}",
    response_model=EngineeringAnswerResponse,
)
def get_answer(answer_run_id: str, services: ServicesDep) -> EngineeringAnswerResponse:
    result = services.answering.get_answer(
        GetAnswerRunQuery(answer_run_id=AnswerRunId(answer_run_id.strip()))
    )
    return answer_response(result)


@router.get(
    "/repositories/{repository_id}/answers",
    response_model=list[EngineeringAnswerResponse],
)
def list_repository_answers(
    repository_id: str,
    services: ServicesDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[EngineeringAnswerResponse]:
    items = services.answering.list_repository_answers(
        ListRepositoryAnswersQuery(
            repository_id=RepositoryId(repository_id.strip()),
            limit=limit,
        )
    )
    return [answer_response(item) for item in items]


@router.post(
    "/answers/{answer_run_id}/feedback",
    response_model=AnswerFeedbackResponse,
)
def submit_answer_feedback(
    answer_run_id: str,
    body: AnswerFeedbackRequest,
    services: ServicesDep,
) -> AnswerFeedbackResponse:
    payload = services.answering.submit_feedback(
        SubmitAnswerFeedbackCommand(
            answer_run_id=AnswerRunId(answer_run_id.strip()),
            rating=body.rating,
            feedback_category=body.feedback_category,
            comment=body.comment or "",
        )
    )
    return feedback_response(payload)
