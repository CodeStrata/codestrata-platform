"""Application models for engineering answering."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.answering.answer import EngineeringAnswerRun
from codestrata_platform.domain.answering.lifecycle import (
    AnswerConfidenceLevel,
    AnswerStatus,
    GroundingStatus,
    QuestionType,
)


@dataclass(frozen=True, slots=True)
class AnswerCitationModel:
    citation_id: str
    label: str
    document_id: str
    chunk_id: str
    content_type: str
    canonical_type: str
    canonical_id: str
    source_references: tuple[str, ...]
    graph_node_ids: tuple[str, ...]
    graph_edge_ids: tuple[str, ...]
    retrieval_score: float
    excerpt: str


@dataclass(frozen=True, slots=True)
class EngineeringAnswerModel:
    answer_run_id: str
    question: str
    question_type: QuestionType
    status: AnswerStatus
    answer: str | None
    citations: tuple[AnswerCitationModel, ...]
    confidence_level: AnswerConfidenceLevel | None
    confidence_score: int | None
    grounding_status: GroundingStatus | None
    limitations: tuple[str, ...]
    follow_up_questions: tuple[str, ...]
    retrieval_index_id: str
    graph_id: str
    snapshot_id: str
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
        run: EngineeringAnswerRun,
        *,
        cache_hit: bool = False,
        include_diagnostics: bool = False,
    ) -> EngineeringAnswerModel:
        citations = tuple(
            AnswerCitationModel(
                citation_id=item.citation_id.value,
                label=item.label,
                document_id=item.document_id,
                chunk_id=item.chunk_id,
                content_type=item.content_type,
                canonical_type=item.canonical_type,
                canonical_id=item.canonical_id,
                source_references=item.source_references,
                graph_node_ids=item.graph_node_ids,
                graph_edge_ids=item.graph_edge_ids,
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
            retrieval_index_id=run.retrieval_index_id.value,
            graph_id=run.knowledge_graph_id.value,
            snapshot_id=run.engineering_snapshot_id.value,
            provider_id=run.provider_id,
            model_id=run.model_id,
            prompt_template_version=run.prompt_template_version.value,
            answer_policy_version=run.answer_policy_version.value,
            generated_at=run.completed_at,
            cache_hit=cache_hit,
            diagnostics=dict(run.diagnostics) if include_diagnostics else None,
        )


# Structured aliases required by the phase brief.
RepositoryOverviewAnswer = EngineeringAnswerModel
FindingExplanationAnswer = EngineeringAnswerModel
RecommendationExplanationAnswer = EngineeringAnswerModel
ImpactExplanationAnswer = EngineeringAnswerModel
RiskExplanationAnswer = EngineeringAnswerModel
DependencyExplanationAnswer = EngineeringAnswerModel
ModernizationGuidanceAnswer = EngineeringAnswerModel
GeneralEngineeringAnswer = EngineeringAnswerModel
