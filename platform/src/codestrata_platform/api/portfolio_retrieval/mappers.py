"""Map application portfolio retrieval models to API DTOs."""

from __future__ import annotations

from codestrata_platform.api.portfolio_retrieval.dto import (
    PortfolioRetrievalChunkSummaryResponse,
    PortfolioRetrievalCitationResponse,
    PortfolioRetrievalContextDiagnosticResponse,
    PortfolioRetrievalContextItemResponse,
    PortfolioRetrievalContextResponse,
    PortfolioRetrievalDocumentSummaryResponse,
    PortfolioRetrievalIndexDetailsResponse,
    PortfolioRetrievalIndexStatisticsResponse,
    PortfolioRetrievalIndexSummaryResponse,
    PortfolioRetrievalScoreBreakdownResponse,
    PortfolioRetrievalSearchHitResponse,
    PortfolioRetrievalSearchResultResponse,
    RepositoryContributionResponse,
)
from codestrata_platform.application.portfolio_retrieval.models import (
    PortfolioRetrievalBuildResult,
    PortfolioRetrievalChunkSummary,
    PortfolioRetrievalCitationLabel,
    PortfolioRetrievalContext,
    PortfolioRetrievalContextDiagnostic,
    PortfolioRetrievalContextItem,
    PortfolioRetrievalDocumentSummary,
    PortfolioRetrievalIndexDetails,
    PortfolioRetrievalIndexStatistics,
    PortfolioRetrievalIndexSummary,
    PortfolioRetrievalScoreBreakdown,
    PortfolioRetrievalSearchHitModel,
    PortfolioRetrievalSearchResultModel,
    RepositoryContributionModel,
)


def summary_response(
    item: PortfolioRetrievalIndexSummary,
) -> PortfolioRetrievalIndexSummaryResponse:
    return PortfolioRetrievalIndexSummaryResponse(
        index_id=item.index_id,
        portfolio_id=item.portfolio_id,
        portfolio_snapshot_id=item.portfolio_snapshot_id,
        portfolio_snapshot_version=item.portfolio_snapshot_version,
        index_version=item.index_version,
        status=item.status.value,
        projection_key=item.projection_key,
        embedding_provider_id=item.embedding_provider_id,
        embedding_model_id=item.embedding_model_id,
        embedding_dimension=item.embedding_dimension,
        repository_count=item.repository_count,
        document_count=item.document_count,
        chunk_count=item.chunk_count,
        created_at=item.created_at,
        completed_at=item.completed_at,
    )


def details_response(
    item: PortfolioRetrievalIndexDetails,
    *,
    created: bool | None = None,
    idempotent: bool | None = None,
) -> PortfolioRetrievalIndexDetailsResponse:
    return PortfolioRetrievalIndexDetailsResponse(
        index_id=item.index_id,
        portfolio_id=item.portfolio_id,
        portfolio_snapshot_id=item.portfolio_snapshot_id,
        portfolio_snapshot_version=item.portfolio_snapshot_version,
        index_version=item.index_version,
        status=item.status.value,
        projection_key=item.projection_key,
        embedding_provider_id=item.embedding_provider_id,
        embedding_model_id=item.embedding_model_id,
        embedding_dimension=item.embedding_dimension,
        repository_count=item.repository_count,
        document_count=item.document_count,
        chunk_count=item.chunk_count,
        created_at=item.created_at,
        completed_at=item.completed_at,
        organization_id=item.organization_id,
        workspace_id=item.workspace_id,
        retrieval_schema_version=item.retrieval_schema_version,
        chunking_policy_version=item.chunking_policy_version,
        ranking_policy_version=item.ranking_policy_version,
        repository_ids=list(item.repository_ids),
        failure_reason=item.failure_reason,
        superseded_at=item.superseded_at,
        created=created if created is not None else item.created,
        idempotent=idempotent if idempotent is not None else item.idempotent,
    )


def build_result_response(
    result: PortfolioRetrievalBuildResult,
) -> PortfolioRetrievalIndexDetailsResponse:
    return details_response(
        result.index,
        created=result.created,
        idempotent=result.idempotent,
    )


def document_response(
    item: PortfolioRetrievalDocumentSummary,
) -> PortfolioRetrievalDocumentSummaryResponse:
    return PortfolioRetrievalDocumentSummaryResponse(
        document_id=item.document_id,
        content_type=item.content_type,
        canonical_type=item.canonical_type,
        canonical_id=item.canonical_id,
        title=item.title,
        summary=item.summary,
        repository_ids=list(item.repository_ids),
        primary_repository_id=item.primary_repository_id,
    )


def chunk_response(item: PortfolioRetrievalChunkSummary) -> PortfolioRetrievalChunkSummaryResponse:
    return PortfolioRetrievalChunkSummaryResponse(
        chunk_id=item.chunk_id,
        document_id=item.document_id,
        ordinal=item.ordinal,
        token_estimate=item.token_estimate,
        text=item.text,
        repository_ids=list(item.repository_ids),
        primary_repository_id=item.primary_repository_id,
        has_embedding=item.has_embedding,
    )


def score_breakdown_response(
    item: PortfolioRetrievalScoreBreakdown,
) -> PortfolioRetrievalScoreBreakdownResponse:
    return PortfolioRetrievalScoreBreakdownResponse(
        lexical_score=item.lexical_score,
        vector_score=item.vector_score,
        portfolio_score=item.portfolio_score,
        repository_score=item.repository_score,
        systemic_score=item.systemic_score,
        source_quality_score=item.source_quality_score,
        freshness_score=item.freshness_score,
        balance_adjustment=item.balance_adjustment,
        final_score=item.final_score,
        ranking_policy_version=item.ranking_policy_version,
    )


def contribution_response(item: RepositoryContributionModel) -> RepositoryContributionResponse:
    return RepositoryContributionResponse(
        repository_id=item.repository_id,
        contribution_score=item.contribution_score,
        finding_count=item.finding_count,
        is_primary=item.is_primary,
    )


def search_hit_response(
    item: PortfolioRetrievalSearchHitModel,
) -> PortfolioRetrievalSearchHitResponse:
    return PortfolioRetrievalSearchHitResponse(
        result_id=item.result_id,
        chunk_id=item.chunk_id,
        document_id=item.document_id,
        content_type=item.content_type,
        canonical_type=item.canonical_type,
        canonical_id=item.canonical_id,
        title=item.title,
        text=item.text,
        score=score_breakdown_response(item.score),
        repository_ids=list(item.repository_ids),
        primary_repository_id=item.primary_repository_id,
        repository_contributions=[
            contribution_response(entry) for entry in item.repository_contributions
        ],
        citations=list(item.citations),
    )


def search_result_response(
    item: PortfolioRetrievalSearchResultModel,
) -> PortfolioRetrievalSearchResultResponse:
    return PortfolioRetrievalSearchResultResponse(
        hits=[search_hit_response(hit) for hit in item.hits],
        mode=item.mode,
        top_k=item.top_k,
    )


def citation_response(item: PortfolioRetrievalCitationLabel) -> PortfolioRetrievalCitationResponse:
    return PortfolioRetrievalCitationResponse(
        label=item.label,
        chunk_id=item.chunk_id,
        document_id=item.document_id,
        canonical_type=item.canonical_type,
        canonical_id=item.canonical_id,
        repository_ids=list(item.repository_ids),
        references=list(item.references),
    )


def context_item_response(
    item: PortfolioRetrievalContextItem,
) -> PortfolioRetrievalContextItemResponse:
    return PortfolioRetrievalContextItemResponse(
        label=item.label,
        section=item.section,
        content_type=item.content_type,
        canonical_type=item.canonical_type,
        canonical_id=item.canonical_id,
        title=item.title,
        text=item.text,
        score=item.score,
        repository_ids=list(item.repository_ids),
        citation=citation_response(item.citation),
    )


def diagnostic_response(
    item: PortfolioRetrievalContextDiagnostic,
) -> PortfolioRetrievalContextDiagnosticResponse:
    return PortfolioRetrievalContextDiagnosticResponse(
        kind=item.kind,
        detail=item.detail,
        repository_id=item.repository_id,
    )


def context_response(item: PortfolioRetrievalContext) -> PortfolioRetrievalContextResponse:
    return PortfolioRetrievalContextResponse(
        items=[context_item_response(entry) for entry in item.items],
        sections=list(item.sections),
        token_estimate=item.token_estimate,
        repository_count=item.repository_count,
        policy_version=item.policy_version,
        truncated=item.truncated,
        diagnostics=[diagnostic_response(entry) for entry in item.diagnostics],
    )


def statistics_response(
    item: PortfolioRetrievalIndexStatistics,
) -> PortfolioRetrievalIndexStatisticsResponse:
    return PortfolioRetrievalIndexStatisticsResponse(
        index_id=item.index_id,
        document_count=item.document_count,
        chunk_count=item.chunk_count,
        embedded_chunk_count=item.embedded_chunk_count,
        repository_count=item.repository_count,
        content_type_counts=dict(item.content_type_counts),
    )
