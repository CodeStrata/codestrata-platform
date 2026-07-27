"""Context sufficiency and citation helpers for answering."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.application.retrieval.context import RetrievalContext, RetrievalContextItem
from codestrata_platform.domain.answering.citation import AnswerCitation
from codestrata_platform.domain.answering.identifiers import AnswerCitationId
from codestrata_platform.domain.answering.lifecycle import ContextSufficiencyStatus, QuestionType
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType


@dataclass(frozen=True, slots=True)
class ContextSufficiencyResult:
    status: ContextSufficiencyStatus
    reasons: tuple[str, ...]
    missing: tuple[str, ...]


class ContextSufficiencyPolicy:
    def evaluate(
        self,
        *,
        question_type: QuestionType,
        context: RetrievalContext,
    ) -> ContextSufficiencyResult:
        if not context.items:
            return ContextSufficiencyResult(
                status=ContextSufficiencyStatus.INSUFFICIENT,
                reasons=("no_retrieved_chunks",),
                missing=("any_context",),
            )
        types = {item.content_type for item in context.items}
        missing: list[str] = []
        reasons: list[str] = ["chunks_present"]
        if question_type is QuestionType.FINDING_EXPLANATION:
            if RetrievalContentType.FINDING.value not in types:
                missing.append("finding")
            if RetrievalContentType.EVIDENCE.value not in types:
                missing.append("evidence")
                reasons.append("evidence_gap")
            if RetrievalContentType.RECOMMENDATION.value not in types:
                missing.append("recommendation")
                reasons.append("recommendation_gap")
        elif question_type in {
            QuestionType.COMPONENT_IMPACT,
            QuestionType.TECHNOLOGY_IMPACT,
        }:
            if RetrievalContentType.IMPACT_ANALYSIS.value not in types and not any(
                item.content_type
                in {
                    RetrievalContentType.COMPONENT.value,
                    RetrievalContentType.TECHNOLOGY.value,
                }
                for item in context.items
            ):
                missing.append("impact_or_component_context")
        elif question_type is QuestionType.RECOMMENDATION_EXPLANATION:
            if RetrievalContentType.RECOMMENDATION.value not in types:
                missing.append("recommendation")
        high_score = any(item.score >= 0.2 for item in context.items)
        if not high_score:
            reasons.append("low_retrieval_scores")
        if missing and len(context.items) < 2:
            status = ContextSufficiencyStatus.INSUFFICIENT
        elif missing:
            status = ContextSufficiencyStatus.PARTIAL
        elif high_score:
            status = ContextSufficiencyStatus.SUFFICIENT
        else:
            status = ContextSufficiencyStatus.PARTIAL
        return ContextSufficiencyResult(
            status=status,
            reasons=tuple(reasons),
            missing=tuple(missing),
        )


def build_labeled_citations(
    context: RetrievalContext,
) -> tuple[tuple[str, RetrievalContextItem], ...]:
    return tuple((f"[C{index}]", item) for index, item in enumerate(context.items, start=1))


def citations_from_context(context: RetrievalContext) -> tuple[AnswerCitation, ...]:
    citations: list[AnswerCitation] = []
    for index, item in enumerate(context.items, start=1):
        label = f"[C{index}]"
        token = item.chunk_id.replace(":", "")[-24:] or f"chunk{index}"
        citations.append(
            AnswerCitation(
                citation_id=AnswerCitationId(f"answer-cite:{token}:{index}"),
                label=label,
                document_id=item.document_id,
                chunk_id=item.chunk_id,
                content_type=item.content_type,
                canonical_type=item.canonical_type,
                canonical_id=item.canonical_id,
                source_references=item.citation.source_references,
                graph_node_ids=item.citation.graph_node_ids,
                graph_edge_ids=(),
                retrieval_score=item.score,
                excerpt=item.text[:800],
            )
        )
    return tuple(citations)
