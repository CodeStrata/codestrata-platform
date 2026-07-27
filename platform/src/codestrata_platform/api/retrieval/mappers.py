"""Map application retrieval models to API DTOs."""

from __future__ import annotations

from codestrata_platform.api.retrieval.dto import (
    RetrievalChunkSummaryResponse,
    RetrievalCitationResponse,
    RetrievalContextItemResponse,
    RetrievalContextResponse,
    RetrievalDocumentSummaryResponse,
    RetrievalIndexDetailsResponse,
    RetrievalIndexStatisticsResponse,
    RetrievalIndexSummaryResponse,
    RetrievalScoreBreakdownResponse,
    RetrievalSearchHitResponse,
    RetrievalSearchResultResponse,
)
from codestrata_platform.application.retrieval.context import (
    RetrievalCitation,
    RetrievalContext,
    RetrievalContextItem,
)
from codestrata_platform.application.retrieval.models import (
    RetrievalBuildResult,
    RetrievalChunkSummary,
    RetrievalDocumentSummary,
    RetrievalIndexDetails,
    RetrievalIndexStatistics,
    RetrievalIndexSummary,
    RetrievalScoreBreakdown,
    RetrievalSearchHitModel,
    RetrievalSearchResultModel,
)


def summary_response(item: RetrievalIndexSummary) -> RetrievalIndexSummaryResponse:
    return RetrievalIndexSummaryResponse(
        index_id=item.index_id,
        repository_id=item.repository_id,
        assessment_id=item.assessment_id,
        engineering_snapshot_id=item.engineering_snapshot_id,
        knowledge_graph_id=item.knowledge_graph_id,
        index_version=item.index_version,
        status=item.status.value,
        projection_key=item.projection_key,
        embedding_provider_id=item.embedding_provider_id,
        embedding_model_id=item.embedding_model_id,
        embedding_dimension=item.embedding_dimension,
        document_count=item.document_count,
        chunk_count=item.chunk_count,
        created_at=item.created_at,
        completed_at=item.completed_at,
    )


def details_response(
    item: RetrievalIndexDetails,
    *,
    created: bool | None = None,
    idempotent: bool | None = None,
) -> RetrievalIndexDetailsResponse:
    return RetrievalIndexDetailsResponse(
        index_id=item.index_id,
        repository_id=item.repository_id,
        assessment_id=item.assessment_id,
        engineering_snapshot_id=item.engineering_snapshot_id,
        knowledge_graph_id=item.knowledge_graph_id,
        index_version=item.index_version,
        status=item.status.value,
        projection_key=item.projection_key,
        embedding_provider_id=item.embedding_provider_id,
        embedding_model_id=item.embedding_model_id,
        embedding_dimension=item.embedding_dimension,
        document_count=item.document_count,
        chunk_count=item.chunk_count,
        created_at=item.created_at,
        completed_at=item.completed_at,
        organization_id=item.organization_id,
        workspace_id=item.workspace_id,
        engineering_snapshot_version=item.engineering_snapshot_version,
        knowledge_graph_version=item.knowledge_graph_version,
        retrieval_schema_version=item.retrieval_schema_version,
        chunking_policy_version=item.chunking_policy_version,
        failure_reason=item.failure_reason,
        created=created if created is not None else item.created,
        idempotent=idempotent if idempotent is not None else item.idempotent,
    )


def build_result_response(result: RetrievalBuildResult) -> RetrievalIndexDetailsResponse:
    return details_response(
        result.index,
        created=result.created,
        idempotent=result.idempotent,
    )


def document_response(item: RetrievalDocumentSummary) -> RetrievalDocumentSummaryResponse:
    return RetrievalDocumentSummaryResponse(
        document_id=item.document_id,
        content_type=item.content_type,
        canonical_type=item.canonical_type,
        canonical_id=item.canonical_id,
        title=item.title,
        summary=item.summary,
    )


def chunk_response(item: RetrievalChunkSummary) -> RetrievalChunkSummaryResponse:
    return RetrievalChunkSummaryResponse(
        chunk_id=item.chunk_id,
        document_id=item.document_id,
        ordinal=item.ordinal,
        token_estimate=item.token_estimate,
        text=item.text,
        has_embedding=item.has_embedding,
    )


def score_breakdown_response(item: RetrievalScoreBreakdown) -> RetrievalScoreBreakdownResponse:
    return RetrievalScoreBreakdownResponse(
        lexical_score=item.lexical_score,
        vector_score=item.vector_score,
        graph_score=item.graph_score,
        source_quality_score=item.source_quality_score,
        final_score=item.final_score,
        policy_version=item.policy_version,
    )


def search_hit_response(item: RetrievalSearchHitModel) -> RetrievalSearchHitResponse:
    return RetrievalSearchHitResponse(
        result_id=item.result_id,
        chunk_id=item.chunk_id,
        document_id=item.document_id,
        content_type=item.content_type,
        canonical_type=item.canonical_type,
        canonical_id=item.canonical_id,
        title=item.title,
        text=item.text,
        score=score_breakdown_response(item.score),
        source_references=list(item.source_references),
        graph_node_ids=list(item.graph_node_ids),
    )


def search_result_response(item: RetrievalSearchResultModel) -> RetrievalSearchResultResponse:
    return RetrievalSearchResultResponse(
        hits=[search_hit_response(hit) for hit in item.hits],
        mode=item.mode,
        top_k=item.top_k,
    )


def citation_response(item: RetrievalCitation) -> RetrievalCitationResponse:
    return RetrievalCitationResponse(
        chunk_id=item.chunk_id,
        document_id=item.document_id,
        canonical_type=item.canonical_type,
        canonical_id=item.canonical_id,
        source_references=list(item.source_references),
        graph_node_ids=list(item.graph_node_ids),
    )


def context_item_response(item: RetrievalContextItem) -> RetrievalContextItemResponse:
    return RetrievalContextItemResponse(
        chunk_id=item.chunk_id,
        document_id=item.document_id,
        content_type=item.content_type,
        canonical_type=item.canonical_type,
        canonical_id=item.canonical_id,
        text=item.text,
        score=item.score,
        citation=citation_response(item.citation),
    )


def context_response(item: RetrievalContext) -> RetrievalContextResponse:
    return RetrievalContextResponse(
        items=[context_item_response(entry) for entry in item.items],
        token_estimate=item.token_estimate,
        policy_version=item.policy_version,
        truncated=item.truncated,
    )


def statistics_response(item: RetrievalIndexStatistics) -> RetrievalIndexStatisticsResponse:
    return RetrievalIndexStatisticsResponse(
        index_id=item.index_id,
        document_count=item.document_count,
        chunk_count=item.chunk_count,
        embedded_chunk_count=item.embedded_chunk_count,
        content_type_counts=dict(item.content_type_counts),
    )
