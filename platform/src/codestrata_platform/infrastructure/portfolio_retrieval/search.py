"""Shared hybrid / lexical / vector ranking helpers for portfolio retrieval repositories.

Reuses the generic ``lexical_score``/``cosine_similarity`` primitives from the
canonical Engineering Retrieval search module and layers portfolio-specific
relevance signals (portfolio-aggregate relevance, repository relevance,
systemic/cross-repository relevance, source quality) on top, scored via
``DefaultPortfolioHybridRetrievalPolicy``. Repository-balance adjustment is
applied last so both the in-memory and durable repositories share one
deterministic search pipeline.
"""

from __future__ import annotations

from codestrata_platform.application.portfolio_retrieval.policies import (
    DefaultPortfolioHybridRetrievalPolicy,
)
from codestrata_platform.application.portfolio_retrieval.ranking import apply_repository_balance
from codestrata_platform.domain.portfolio.lifecycle import RepositoryCriticality
from codestrata_platform.domain.portfolio_retrieval.chunk import PortfolioRetrievalChunk
from codestrata_platform.domain.portfolio_retrieval.document import PortfolioRetrievalDocument
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    EmbeddingVector,
    PortfolioContextId,
)
from codestrata_platform.domain.portfolio_retrieval.index import PortfolioRetrievalIndex
from codestrata_platform.domain.portfolio_retrieval.query import (
    PortfolioRetrievalQuery,
    PortfolioRetrievalScore,
)
from codestrata_platform.domain.portfolio_retrieval.ranking import (
    HARD_MAX_CONTRIBUTING_REPOSITORIES,
    RepositoryContribution,
)
from codestrata_platform.domain.portfolio_retrieval.result import (
    PortfolioRetrievalHit,
    PortfolioRetrievalSearchResult,
)
from codestrata_platform.domain.portfolio_retrieval.scope import PortfolioRetrievalScope
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType
from codestrata_platform.domain.retrieval.taxonomy import RetrievalMode
from codestrata_platform.infrastructure.retrieval.search import cosine_similarity, lexical_score

_PORTFOLIO_AGGREGATE_TYPES = frozenset(
    {
        PortfolioRetrievalContentType.PORTFOLIO_SUMMARY,
        PortfolioRetrievalContentType.PORTFOLIO_TECHNOLOGY,
        PortfolioRetrievalContentType.TECHNOLOGY_STANDARDIZATION,
        PortfolioRetrievalContentType.TECHNOLOGY_FRAGMENTATION,
        PortfolioRetrievalContentType.PORTFOLIO_FINDING,
        PortfolioRetrievalContentType.RECURRING_FINDING,
        PortfolioRetrievalContentType.PORTFOLIO_RECOMMENDATION,
        PortfolioRetrievalContentType.RECURRING_RECOMMENDATION,
        PortfolioRetrievalContentType.PORTFOLIO_RISK,
        PortfolioRetrievalContentType.SYSTEMIC_RISK,
        PortfolioRetrievalContentType.MODERNIZATION_THEME,
        PortfolioRetrievalContentType.MODERNIZATION_CANDIDATE,
        PortfolioRetrievalContentType.MODERNIZATION_WAVE,
        PortfolioRetrievalContentType.PORTFOLIO_COVERAGE,
    }
)

_SYSTEMIC_TYPES = frozenset(
    {
        PortfolioRetrievalContentType.SYSTEMIC_RISK,
        PortfolioRetrievalContentType.CROSS_REPOSITORY_SIGNAL,
        PortfolioRetrievalContentType.SHARED_EXPOSURE,
        PortfolioRetrievalContentType.TECHNOLOGY_FRAGMENTATION,
    }
)

_SOURCE_QUALITY: dict[PortfolioRetrievalContentType, float] = {
    PortfolioRetrievalContentType.PORTFOLIO_SUMMARY: 0.9,
    PortfolioRetrievalContentType.PORTFOLIO_RISK: 0.95,
    PortfolioRetrievalContentType.SYSTEMIC_RISK: 0.95,
    PortfolioRetrievalContentType.PORTFOLIO_FINDING: 0.9,
    PortfolioRetrievalContentType.RECURRING_FINDING: 0.9,
    PortfolioRetrievalContentType.PORTFOLIO_RECOMMENDATION: 0.85,
    PortfolioRetrievalContentType.RECURRING_RECOMMENDATION: 0.85,
    PortfolioRetrievalContentType.PORTFOLIO_TECHNOLOGY: 0.8,
    PortfolioRetrievalContentType.TECHNOLOGY_STANDARDIZATION: 0.8,
    PortfolioRetrievalContentType.TECHNOLOGY_FRAGMENTATION: 0.8,
    PortfolioRetrievalContentType.MODERNIZATION_THEME: 0.8,
    PortfolioRetrievalContentType.MODERNIZATION_CANDIDATE: 0.8,
    PortfolioRetrievalContentType.MODERNIZATION_WAVE: 0.75,
    PortfolioRetrievalContentType.PORTFOLIO_COVERAGE: 0.75,
    PortfolioRetrievalContentType.REPOSITORY_PROFILE: 0.75,
    PortfolioRetrievalContentType.REPOSITORY_RISK_PROFILE: 0.8,
    PortfolioRetrievalContentType.REPOSITORY_TECHNOLOGY_PROFILE: 0.75,
    PortfolioRetrievalContentType.CROSS_REPOSITORY_SIGNAL: 0.85,
    PortfolioRetrievalContentType.SHARED_EXPOSURE: 0.85,
    PortfolioRetrievalContentType.REPOSITORY_SUPPORTING_CONTEXT: 0.6,
}
_DEFAULT_SOURCE_QUALITY = 0.6


def portfolio_relevance_score(content_type: PortfolioRetrievalContentType) -> float:
    return 1.0 if content_type in _PORTFOLIO_AGGREGATE_TYPES else 0.0


def systemic_relevance_score(content_type: PortfolioRetrievalContentType) -> float:
    return 1.0 if content_type in _SYSTEMIC_TYPES else 0.0


def source_quality_score(content_type: PortfolioRetrievalContentType) -> float:
    return _SOURCE_QUALITY.get(content_type, _DEFAULT_SOURCE_QUALITY)


def repository_relevance_score(
    document: PortfolioRetrievalDocument,
    chunk: PortfolioRetrievalChunk,
    *,
    scope: PortfolioRetrievalScope,
) -> float:
    repository_ids = {item.value for item in chunk.repository_ids} or {
        item.value for item in document.repository_ids
    }
    if not repository_ids:
        return 0.0
    if not scope.repository_ids:
        return 1.0
    included = {item.value for item in scope.repository_ids}
    matched = repository_ids & included
    if not matched:
        return 0.0
    return min(1.0, len(matched) / len(repository_ids))


def matches_content_type(
    document: PortfolioRetrievalDocument,
    query: PortfolioRetrievalQuery,
) -> bool:
    if query.content_types and document.content_type not in query.content_types:
        return False
    return True


def matches_query_filters(
    document: PortfolioRetrievalDocument,
    query: PortfolioRetrievalQuery,
) -> bool:
    for key, value in query.filters.items():
        candidate = document.metadata.get(key) or document.structured_content.get(key)
        if candidate is None or candidate.strip().lower() != value.strip().lower():
            return False
    return True


def matches_repository_scope(
    document: PortfolioRetrievalDocument,
    chunk: PortfolioRetrievalChunk,
    *,
    scope: PortfolioRetrievalScope,
) -> bool:
    repository_ids = {item.value for item in chunk.repository_ids} or {
        item.value for item in document.repository_ids
    }
    if scope.exclude_repository_ids and repository_ids:
        excluded = {item.value for item in scope.exclude_repository_ids}
        if repository_ids & excluded:
            return False
    if scope.repository_ids and repository_ids:
        included = {item.value for item in scope.repository_ids}
        if not repository_ids & included:
            return False
    return True


def search_portfolio_index(
    index: PortfolioRetrievalIndex,
    query: PortfolioRetrievalQuery,
    *,
    scope: PortfolioRetrievalScope,
    query_embedding: EmbeddingVector | None,
    policy: DefaultPortfolioHybridRetrievalPolicy | None = None,
    criticality_lookup: dict[str, RepositoryCriticality] | None = None,
) -> PortfolioRetrievalSearchResult:
    if (
        index.organization_id != scope.organization_id
        or index.workspace_id != scope.workspace_id
        or index.portfolio_id != scope.portfolio_id
    ):
        return PortfolioRetrievalSearchResult(hits=(), mode=query.mode.value, top_k=query.top_k)
    if (
        scope.portfolio_snapshot_id is not None
        and index.portfolio_snapshot_id != scope.portfolio_snapshot_id
    ):
        return PortfolioRetrievalSearchResult(hits=(), mode=query.mode.value, top_k=query.top_k)

    hybrid = policy or DefaultPortfolioHybridRetrievalPolicy()
    documents = {item.document_id.value: item for item in index.documents}
    hits: list[PortfolioRetrievalHit] = []

    for chunk in index.chunks:
        document = documents.get(chunk.document_id.value)
        if document is None:
            continue
        if not matches_content_type(document, query):
            continue
        if not matches_query_filters(document, query):
            continue
        if not matches_repository_scope(document, chunk, scope=scope):
            continue

        lex = lexical_score(query.query_text, chunk.text)
        vec = 0.0
        if query_embedding is not None and chunk.embedding is not None:
            vec = cosine_similarity(query_embedding, chunk.embedding)
        portfolio = (
            portfolio_relevance_score(document.content_type)
            if query.include_portfolio_aggregates
            else 0.0
        )
        repository = (
            repository_relevance_score(document, chunk, scope=scope)
            if query.include_repository_context
            else 0.0
        )
        systemic = systemic_relevance_score(document.content_type)
        quality = source_quality_score(document.content_type)

        if query.mode is RetrievalMode.LEXICAL:
            if lex <= 0:
                continue
            score = PortfolioRetrievalScore(
                lexical_score=lex,
                source_quality_score=quality,
                final_score=round(0.85 * lex + 0.15 * quality, 6),
                ranking_policy_version=hybrid.version,
            )
        elif query.mode is RetrievalMode.VECTOR:
            if vec <= 0:
                continue
            score = PortfolioRetrievalScore(
                vector_score=vec,
                source_quality_score=quality,
                final_score=round(0.85 * vec + 0.15 * quality, 6),
                ranking_policy_version=hybrid.version,
            )
        else:
            score = hybrid.combine(
                lexical_score=lex,
                vector_score=vec,
                portfolio_score=portfolio,
                repository_score=repository,
                systemic_score=systemic,
                source_quality_score=quality,
                freshness_score=1.0,
            )
            if score.final_score <= 0:
                continue

        digest = chunk.chunk_id.value.replace("portfolio-retrieval-chunk:", "")[:32]
        repository_ids = chunk.repository_ids or document.repository_ids
        primary = chunk.primary_repository_id or document.primary_repository_id
        finding_count = 0
        raw_findings = document.structured_content.get("finding_count")
        if raw_findings is not None:
            try:
                finding_count = max(0, int(raw_findings))
            except ValueError:
                finding_count = 0
        contributions = tuple(
            RepositoryContribution(
                repository_id=repository_id,
                contribution_score=round(1.0 / max(1, len(repository_ids)), 6),
                finding_count=finding_count if primary == repository_id else 0,
                is_primary=primary == repository_id if primary is not None else False,
            )
            for repository_id in repository_ids[:HARD_MAX_CONTRIBUTING_REPOSITORIES]
        )
        hits.append(
            PortfolioRetrievalHit(
                result_id=PortfolioContextId(f"portfolio-retrieval-hit:{digest}"),
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                content_type=document.content_type,
                canonical_type=document.canonical_type,
                canonical_id=document.canonical_id,
                title=document.title,
                text=chunk.text,
                score=score,
                repository_ids=repository_ids,
                primary_repository_id=primary,
                repository_contributions=contributions,
                citations=chunk.citations,
            )
        )

    hits.sort(
        key=lambda item: (
            -item.score.final_score,
            item.chunk_id.value,
            item.document_id.value,
        )
    )
    balanced = apply_repository_balance(
        tuple(hits),
        query.repository_balance_mode,
        criticality_lookup,
    )
    return PortfolioRetrievalSearchResult(
        hits=balanced[: query.top_k],
        mode=query.mode.value,
        top_k=query.top_k,
    )


__all__ = [
    "matches_content_type",
    "matches_query_filters",
    "matches_repository_scope",
    "portfolio_relevance_score",
    "repository_relevance_score",
    "search_portfolio_index",
    "source_quality_score",
    "systemic_relevance_score",
]
