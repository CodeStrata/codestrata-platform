"""Thin Portfolio Answering controllers."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.portfolio_answering.dto import (
    AskPortfolioAnswerRequest,
    PortfolioAnswerFeedbackRequest,
    PortfolioAnswerFeedbackResponse,
    PortfolioAnswerResponse,
)
from codestrata_platform.api.portfolio_answering.mappers import answer_response, feedback_response
from codestrata_platform.application.common.errors import ValidationError
from codestrata_platform.application.portfolio_answering.commands import (
    AskPortfolioQuestionCommand,
    GetPortfolioAnswerRunQuery,
    ListPortfolioAnswersQuery,
    SubmitPortfolioAnswerFeedbackCommand,
)
from codestrata_platform.domain.portfolio.identifiers import PortfolioId
from codestrata_platform.domain.portfolio_answering.identifiers import PortfolioAnswerRunId
from codestrata_platform.domain.portfolio_answering.lifecycle import PortfolioQuestionType
from codestrata_platform.domain.portfolio_answering.question import PortfolioQuestionScope
from codestrata_platform.domain.portfolio_retrieval.identifiers import PortfolioRetrievalIndexId
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType

router = APIRouter(tags=["Portfolio Answering"])


def _build_ask_command(
    body: AskPortfolioAnswerRequest,
    *,
    portfolio_id: str,
) -> AskPortfolioQuestionCommand:
    content_types = (
        tuple(PortfolioRetrievalContentType(item) for item in body.content_types)
        if body.content_types
        else ()
    )
    return AskPortfolioQuestionCommand(
        question=body.question,
        scope=PortfolioQuestionScope(
            organization_id=body.organization_id.strip(),
            workspace_id=body.workspace_id.strip(),
            portfolio_id=portfolio_id.strip(),
            portfolio_retrieval_index_id=(
                body.portfolio_retrieval_index_id.strip()
                if body.portfolio_retrieval_index_id is not None
                else None
            ),
            repository_ids=tuple(body.repository_ids or ()),
            content_types=content_types,
        ),
        question_type=(
            PortfolioQuestionType(body.question_type)
            if body.question_type is not None
            else None
        ),
        portfolio_retrieval_index_id=(
            PortfolioRetrievalIndexId(body.portfolio_retrieval_index_id.strip())
            if body.portfolio_retrieval_index_id is not None
            else None
        ),
        include_diagnostics=body.include_diagnostics,
        use_cache=body.use_cache,
    )


@router.post(
    "/portfolio-answers",
    response_model=PortfolioAnswerResponse,
    status_code=status.HTTP_201_CREATED,
)
def ask_portfolio_answer(
    body: AskPortfolioAnswerRequest,
    services: ServicesDep,
) -> PortfolioAnswerResponse:
    if body.portfolio_id is None or not body.portfolio_id.strip():
        raise ValidationError(
            "portfolio_id is required",
            reason_code="missing_portfolio_id",
        )
    result = services.portfolio_answering.ask(
        _build_ask_command(body, portfolio_id=body.portfolio_id)
    )
    return answer_response(result)


@router.post(
    "/portfolios/{portfolio_id}/ask",
    response_model=PortfolioAnswerResponse,
    status_code=status.HTTP_201_CREATED,
)
def ask_portfolio(
    portfolio_id: str,
    body: AskPortfolioAnswerRequest,
    services: ServicesDep,
) -> PortfolioAnswerResponse:
    result = services.portfolio_answering.ask(
        _build_ask_command(body, portfolio_id=portfolio_id)
    )
    return answer_response(result)


@router.get(
    "/portfolio-answers/{answer_id}",
    response_model=PortfolioAnswerResponse,
)
def get_portfolio_answer(answer_id: str, services: ServicesDep) -> PortfolioAnswerResponse:
    result = services.portfolio_answering.get_answer(
        GetPortfolioAnswerRunQuery(answer_run_id=PortfolioAnswerRunId(answer_id.strip()))
    )
    return answer_response(result)


@router.get(
    "/portfolios/{portfolio_id}/answers",
    response_model=list[PortfolioAnswerResponse],
)
def list_portfolio_answers(
    portfolio_id: str,
    services: ServicesDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[PortfolioAnswerResponse]:
    items = services.portfolio_answering.list_portfolio_answers(
        ListPortfolioAnswersQuery(
            portfolio_id=PortfolioId(portfolio_id.strip()),
            limit=limit,
        )
    )
    return [answer_response(item) for item in items]


@router.post(
    "/portfolio-answers/{answer_id}/feedback",
    response_model=PortfolioAnswerFeedbackResponse,
)
def submit_portfolio_answer_feedback(
    answer_id: str,
    body: PortfolioAnswerFeedbackRequest,
    services: ServicesDep,
) -> PortfolioAnswerFeedbackResponse:
    payload = services.portfolio_answering.submit_feedback(
        SubmitPortfolioAnswerFeedbackCommand(
            answer_run_id=PortfolioAnswerRunId(answer_id.strip()),
            rating=body.rating,
            feedback_category=body.feedback_category,
            comment=body.comment or "",
        )
    )
    return feedback_response(payload)
