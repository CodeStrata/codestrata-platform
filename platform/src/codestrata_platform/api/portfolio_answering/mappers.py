"""Map application portfolio answering models to API DTOs."""

from __future__ import annotations

from codestrata_platform.api.portfolio_answering.dto import (
    PortfolioAnswerCitationResponse,
    PortfolioAnswerFeedbackResponse,
    PortfolioAnswerResponse,
)
from codestrata_platform.application.portfolio_answering.models import (
    PortfolioAnswerCitationModel,
    PortfolioAnswerModel,
)


def citation_response(item: PortfolioAnswerCitationModel) -> PortfolioAnswerCitationResponse:
    return PortfolioAnswerCitationResponse(
        citation_id=item.citation_id,
        label=item.label,
        document_id=item.document_id,
        chunk_id=item.chunk_id,
        content_type=item.content_type,
        canonical_type=item.canonical_type,
        canonical_id=item.canonical_id,
        source_references=list(item.source_references),
        repository_ids=list(item.repository_ids),
        portfolio_id=item.portfolio_id,
        portfolio_snapshot_id=item.portfolio_snapshot_id,
        retrieval_score=item.retrieval_score,
        excerpt=item.excerpt,
    )


def answer_response(item: PortfolioAnswerModel) -> PortfolioAnswerResponse:
    return PortfolioAnswerResponse(
        answer_run_id=item.answer_run_id,
        question=item.question,
        question_type=item.question_type.value,
        status=item.status.value,
        answer=item.answer,
        citations=[citation_response(citation) for citation in item.citations],
        confidence_level=(
            item.confidence_level.value if item.confidence_level is not None else None
        ),
        confidence_score=item.confidence_score,
        grounding_status=(
            item.grounding_status.value if item.grounding_status is not None else None
        ),
        limitations=list(item.limitations),
        follow_up_questions=list(item.follow_up_questions),
        portfolio_id=item.portfolio_id,
        portfolio_snapshot_id=item.portfolio_snapshot_id,
        portfolio_retrieval_index_id=item.portfolio_retrieval_index_id,
        provider_id=item.provider_id,
        model_id=item.model_id,
        prompt_template_version=item.prompt_template_version,
        answer_policy_version=item.answer_policy_version,
        generated_at=item.generated_at,
        cache_hit=item.cache_hit,
        diagnostics=dict(item.diagnostics) if item.diagnostics is not None else None,
    )


def feedback_response(payload: dict[str, object]) -> PortfolioAnswerFeedbackResponse:
    return PortfolioAnswerFeedbackResponse(
        answer_run_id=str(payload["answer_run_id"]),
        rating=int(payload["rating"]),  # type: ignore[arg-type]
        feedback_category=str(payload["feedback_category"]),
        comment=str(payload.get("comment", "")),
    )
