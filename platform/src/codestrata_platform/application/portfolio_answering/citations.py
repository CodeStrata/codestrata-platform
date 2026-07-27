"""Context sufficiency and citation helpers for portfolio answering."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.application.portfolio_retrieval.models import (
    PortfolioRetrievalContext,
    PortfolioRetrievalContextItem,
)
from codestrata_platform.domain.answering.lifecycle import ContextSufficiencyStatus
from codestrata_platform.domain.portfolio_answering.citation import PortfolioAnswerCitation
from codestrata_platform.domain.portfolio_answering.identifiers import PortfolioAnswerCitationId
from codestrata_platform.domain.portfolio_answering.lifecycle import PortfolioQuestionType
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType


@dataclass(frozen=True, slots=True)
class PortfolioContextSufficiencyResult:
    status: ContextSufficiencyStatus
    reasons: tuple[str, ...]
    missing: tuple[str, ...]


class PortfolioContextSufficiencyPolicy:
    def evaluate(
        self,
        *,
        question_type: PortfolioQuestionType,
        context: PortfolioRetrievalContext,
    ) -> PortfolioContextSufficiencyResult:
        if not context.items:
            return PortfolioContextSufficiencyResult(
                status=ContextSufficiencyStatus.INSUFFICIENT,
                reasons=("no_retrieved_chunks",),
                missing=("any_context",),
            )
        types = {item.content_type for item in context.items}
        missing: list[str] = []
        reasons: list[str] = ["chunks_present"]
        if question_type is PortfolioQuestionType.RECURRING_FINDING_EXPLANATION:
            if (
                PortfolioRetrievalContentType.RECURRING_FINDING.value not in types
                and PortfolioRetrievalContentType.PORTFOLIO_FINDING.value not in types
            ):
                missing.append("recurring_finding")
        elif question_type is PortfolioQuestionType.SYSTEMIC_RISK_EXPLANATION:
            if (
                PortfolioRetrievalContentType.SYSTEMIC_RISK.value not in types
                and PortfolioRetrievalContentType.PORTFOLIO_RISK.value not in types
            ):
                missing.append("systemic_risk")
        elif question_type is PortfolioQuestionType.MODERNIZATION_GUIDANCE:
            if not any(
                value in types
                for value in (
                    PortfolioRetrievalContentType.MODERNIZATION_CANDIDATE.value,
                    PortfolioRetrievalContentType.MODERNIZATION_WAVE.value,
                    PortfolioRetrievalContentType.MODERNIZATION_THEME.value,
                )
            ):
                missing.append("modernization_context")
        elif question_type is PortfolioQuestionType.CROSS_REPOSITORY_SIGNAL:
            if (
                PortfolioRetrievalContentType.CROSS_REPOSITORY_SIGNAL.value not in types
                and PortfolioRetrievalContentType.SHARED_EXPOSURE.value not in types
            ):
                missing.append("cross_repository_signal")
        high_score = any(item.score >= 0.2 for item in context.items)
        if not high_score:
            reasons.append("low_retrieval_scores")
        if context.truncated:
            reasons.append("context_truncated")
        if missing and len(context.items) < 2:
            status = ContextSufficiencyStatus.INSUFFICIENT
        elif missing or context.truncated:
            status = ContextSufficiencyStatus.PARTIAL
        elif high_score:
            status = ContextSufficiencyStatus.SUFFICIENT
        else:
            status = ContextSufficiencyStatus.PARTIAL
        return PortfolioContextSufficiencyResult(
            status=status,
            reasons=tuple(reasons),
            missing=tuple(missing),
        )


def bracket_label(raw_label: str, index: int) -> str:
    compact = raw_label.strip()
    if compact.startswith("[") and compact.endswith("]"):
        return compact
    if compact.startswith("P") and compact[1:].isdigit():
        return f"[{compact}]"
    return f"[P{index}]"


def build_labeled_context_items(
    context: PortfolioRetrievalContext,
) -> tuple[tuple[str, PortfolioRetrievalContextItem], ...]:
    return tuple(
        (bracket_label(item.label, index), item)
        for index, item in enumerate(context.items, start=1)
    )


def citations_from_context(
    context: PortfolioRetrievalContext,
    *,
    portfolio_id: str,
    portfolio_snapshot_id: str,
) -> tuple[PortfolioAnswerCitation, ...]:
    citations: list[PortfolioAnswerCitation] = []
    for index, item in enumerate(context.items, start=1):
        label = bracket_label(item.label, index)
        token = item.citation.chunk_id.replace(":", "")[-24:] or f"chunk{index}"
        citations.append(
            PortfolioAnswerCitation(
                citation_id=PortfolioAnswerCitationId(f"portfolio-answer-cite:{token}:{index}"),
                label=label,
                document_id=item.citation.document_id,
                chunk_id=item.citation.chunk_id,
                content_type=item.content_type,
                canonical_type=item.canonical_type,
                canonical_id=item.canonical_id,
                source_references=item.citation.references,
                repository_ids=item.repository_ids,
                portfolio_id=portfolio_id,
                portfolio_snapshot_id=portfolio_snapshot_id,
                retrieval_score=item.score,
                excerpt=item.text[:800],
            )
        )
    return tuple(citations)
