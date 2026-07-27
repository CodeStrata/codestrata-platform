"""Application models for portfolio answering."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.answering.lifecycle import (
    AnswerConfidenceLevel,
    AnswerStatus,
    GroundingStatus,
)
from codestrata_platform.domain.portfolio_answering.answer import PortfolioAnswerRun
from codestrata_platform.domain.portfolio_answering.lifecycle import PortfolioQuestionType


@dataclass(frozen=True, slots=True)
class PortfolioAnswerCitationModel:
    citation_id: str
    label: str
    document_id: str
    chunk_id: str
    content_type: str
    canonical_type: str
    canonical_id: str
    source_references: tuple[str, ...]
    repository_ids: tuple[str, ...]
    portfolio_id: str
    portfolio_snapshot_id: str
    retrieval_score: float
    excerpt: str


@dataclass(frozen=True, slots=True)
class PortfolioAnswerModel:
    answer_run_id: str
    question: str
    question_type: PortfolioQuestionType
    status: AnswerStatus
    answer: str | None
    citations: tuple[PortfolioAnswerCitationModel, ...]
    confidence_level: AnswerConfidenceLevel | None
    confidence_score: int | None
    grounding_status: GroundingStatus | None
    limitations: tuple[str, ...]
    follow_up_questions: tuple[str, ...]
    portfolio_id: str
    portfolio_snapshot_id: str
    portfolio_retrieval_index_id: str
    provider_id: str
    model_id: str
    prompt_template_version: str
    answer_policy_version: str
    generated_at: datetime | None
    cache_hit: bool = False
    diagnostics: dict[str, str] | None = None

    @classmethod
    def from_aggregate(
        cls,
        run: PortfolioAnswerRun,
        *,
        cache_hit: bool = False,
        include_diagnostics: bool = False,
    ) -> PortfolioAnswerModel:
        citations = tuple(
            PortfolioAnswerCitationModel(
                citation_id=item.citation_id.value,
                label=item.label,
                document_id=item.document_id,
                chunk_id=item.chunk_id,
                content_type=item.content_type,
                canonical_type=item.canonical_type,
                canonical_id=item.canonical_id,
                source_references=item.source_references,
                repository_ids=item.repository_ids,
                portfolio_id=item.portfolio_id,
                portfolio_snapshot_id=item.portfolio_snapshot_id,
                retrieval_score=item.retrieval_score,
                excerpt=item.excerpt,
            )
            for item in run.citations
        )
        return cls(
            answer_run_id=run.answer_run_id.value,
            question=run.question.text,
            question_type=run.question_type,
            status=run.status,
            answer=run.answer_text.value if run.answer_text is not None else None,
            citations=citations,
            confidence_level=run.confidence.level if run.confidence else None,
            confidence_score=run.confidence.score if run.confidence else None,
            grounding_status=run.grounding.status if run.grounding else None,
            limitations=run.limitations,
            follow_up_questions=run.follow_up_questions,
            portfolio_id=run.portfolio_id.value,
            portfolio_snapshot_id=run.portfolio_snapshot_id.value,
            portfolio_retrieval_index_id=run.portfolio_retrieval_index_id.value,
            provider_id=run.provider_id,
            model_id=run.model_id,
            prompt_template_version=run.prompt_template_version.value,
            answer_policy_version=run.answer_policy_version.value,
            generated_at=run.completed_at,
            cache_hit=cache_hit,
            diagnostics=dict(run.diagnostics) if include_diagnostics else None,
        )
