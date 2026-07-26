"""Confidence calculation for grounded answers (deterministic factors only)."""

from __future__ import annotations

from collections.abc import Sequence

from codestrata_platform.rag.domain.answering import AnswerConfidence, AnswerStatement
from codestrata_platform.rag.domain.retrieval import RetrievalHit


def calculate_answer_confidence(
    *,
    statements: Sequence[AnswerStatement],
    citations_used: int,
    hits: Sequence[RetrievalHit],
    grounding_exclusions: int,
    minimum_supporting_sources: int,
) -> AnswerConfidence:
    """Derive HIGH/MEDIUM/LOW/NONE from measurable retrieval/answer factors.

    Factors (documented, non-probabilistic):
    - mean retrieval score of cited hits
    - number of accepted statements
    - unique supporting documents/files
    - citation coverage of factual statements
    - grounding exclusions
    """

    if not statements:
        return AnswerConfidence.NONE

    factual = [
        item
        for item in statements
        if item.statement_type.value
        not in {"insufficient_evidence", "limitation"}
    ]
    if not factual:
        return AnswerConfidence.NONE

    cited_hits = [
        hit
        for hit in hits
        if hit.citation_label
        in {label for stmt in factual for label in stmt.citation_labels}
    ]
    if not cited_hits:
        return AnswerConfidence.NONE

    mean_score = sum(hit.score for hit in cited_hits) / len(cited_hits)
    unique_docs = {hit.document_id for hit in cited_hits if hit.document_id}
    unique_files = {hit.file_path for hit in cited_hits if hit.file_path}
    supporting_sources = max(len(unique_docs), len(unique_files), citations_used)
    citation_coverage = sum(1 for item in factual if item.citation_labels) / len(factual)

    if (
        mean_score >= 0.55
        and supporting_sources >= max(2, minimum_supporting_sources)
        and citation_coverage >= 1.0
        and grounding_exclusions == 0
        and len(factual) >= 2
    ):
        return AnswerConfidence.HIGH
    if (
        mean_score >= 0.25
        and supporting_sources >= minimum_supporting_sources
        and citation_coverage >= 0.8
    ):
        return AnswerConfidence.MEDIUM
    if supporting_sources >= 1 and citation_coverage > 0:
        return AnswerConfidence.LOW
    return AnswerConfidence.NONE
