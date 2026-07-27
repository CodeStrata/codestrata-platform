"""Thin Engineering Retrieval controllers."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.retrieval.dto import (
    BuildRetrievalIndexRequest,
    RebuildRetrievalIndexRequest,
    RetrievalChunkSummaryResponse,
    RetrievalContextRequest,
    RetrievalContextResponse,
    RetrievalDocumentSummaryResponse,
    RetrievalIndexDetailsResponse,
    RetrievalIndexStatisticsResponse,
    RetrievalIndexSummaryResponse,
    RetrievalSearchRequest,
    RetrievalSearchResultResponse,
)
from codestrata_platform.api.retrieval.mappers import (
    build_result_response,
    chunk_response,
    context_response,
    details_response,
    document_response,
    search_result_response,
    statistics_response,
    summary_response,
)
from codestrata_platform.application.retrieval.commands import (
    BuildRetrievalIndexCommand,
    RebuildRetrievalIndexCommand,
)
from codestrata_platform.application.retrieval.queries import (
    AssembleRetrievalContextQuery,
    GetLatestRepositoryRetrievalIndexQuery,
    GetRetrievalChunkQuery,
    GetRetrievalDocumentQuery,
    GetRetrievalIndexQuery,
    GetRetrievalIndexStatisticsQuery,
    ListRepositoryRetrievalIndexesQuery,
    ListRetrievalDocumentsQuery,
    SearchRetrievalIndexQuery,
)
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.knowledge_graph.identifiers import KnowledgeGraphId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.identifiers import (
    RetrievalChunkId,
    RetrievalDocumentId,
    RetrievalIndexId,
)
from codestrata_platform.domain.retrieval.query import RetrievalQuery
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType, RetrievalMode

router = APIRouter(tags=["Retrieval"])


@router.post(
    "/retrieval/indexes",
    response_model=RetrievalIndexDetailsResponse,
    status_code=status.HTTP_201_CREATED,
)
def build_retrieval_index(
    body: BuildRetrievalIndexRequest,
    services: ServicesDep,
    response: Response,
) -> RetrievalIndexDetailsResponse:
    result = services.retrieval.build_retrieval_index(
        BuildRetrievalIndexCommand(
            snapshot_id=EngineeringSnapshotId(body.snapshot_id.strip()),
            graph_id=(
                KnowledgeGraphId(body.graph_id.strip()) if body.graph_id is not None else None
            ),
            embedding_provider=body.embedding_provider,
            embedding_model=body.embedding_model,
            embedding_dimension=body.embedding_dimension,
        )
    )
    if result.idempotent:
        response.status_code = status.HTTP_200_OK
    return build_result_response(result)


@router.post(
    "/retrieval/indexes/{index_id}/rebuild",
    response_model=RetrievalIndexDetailsResponse,
)
def rebuild_retrieval_index(
    index_id: str,
    services: ServicesDep,
    body: RebuildRetrievalIndexRequest | None = None,
) -> RetrievalIndexDetailsResponse:
    request = body or RebuildRetrievalIndexRequest()
    result = services.retrieval.rebuild_retrieval_index(
        RebuildRetrievalIndexCommand(
            index_id=RetrievalIndexId(index_id.strip()),
            embedding_provider=request.embedding_provider,
            embedding_model=request.embedding_model,
            embedding_dimension=request.embedding_dimension,
        )
    )
    return build_result_response(result)


@router.get(
    "/retrieval/indexes/{index_id}",
    response_model=RetrievalIndexDetailsResponse,
)
def get_retrieval_index(index_id: str, services: ServicesDep) -> RetrievalIndexDetailsResponse:
    details = services.retrieval.get_retrieval_index(
        GetRetrievalIndexQuery(index_id=RetrievalIndexId(index_id.strip()))
    )
    return details_response(details)


@router.get(
    "/repositories/{repository_id}/retrieval-indexes",
    response_model=list[RetrievalIndexSummaryResponse],
)
def list_repository_retrieval_indexes(
    repository_id: str,
    services: ServicesDep,
) -> list[RetrievalIndexSummaryResponse]:
    items = services.retrieval.list_repository_indexes(
        ListRepositoryRetrievalIndexesQuery(
            repository_id=RepositoryId(repository_id.strip()),
        )
    )
    return [summary_response(item) for item in items]


@router.get(
    "/repositories/{repository_id}/retrieval-indexes/latest",
    response_model=RetrievalIndexDetailsResponse,
)
def get_latest_repository_retrieval_index(
    repository_id: str,
    services: ServicesDep,
) -> RetrievalIndexDetailsResponse:
    details = services.retrieval.get_latest_repository_index(
        GetLatestRepositoryRetrievalIndexQuery(
            repository_id=RepositoryId(repository_id.strip()),
        )
    )
    return details_response(details)


@router.get(
    "/retrieval/indexes/{index_id}/documents",
    response_model=list[RetrievalDocumentSummaryResponse],
)
def list_retrieval_documents(
    index_id: str,
    services: ServicesDep,
    content_type: Annotated[list[str] | None, Query()] = None,
    page: Annotated[int, Query(ge=0)] = 0,
    size: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[RetrievalDocumentSummaryResponse]:
    content_types = (
        tuple(RetrievalContentType(item) for item in content_type) if content_type else ()
    )
    items = services.retrieval.list_documents(
        ListRetrievalDocumentsQuery(
            index_id=RetrievalIndexId(index_id.strip()),
            offset=page * size,
            limit=size,
            content_types=content_types,
        )
    )
    return [document_response(item) for item in items]


@router.get(
    "/retrieval/indexes/{index_id}/documents/{document_id}",
    response_model=RetrievalDocumentSummaryResponse,
)
def get_retrieval_document(
    index_id: str,
    document_id: str,
    services: ServicesDep,
) -> RetrievalDocumentSummaryResponse:
    item = services.retrieval.get_document(
        GetRetrievalDocumentQuery(
            index_id=RetrievalIndexId(index_id.strip()),
            document_id=RetrievalDocumentId(document_id.strip()),
        )
    )
    return document_response(item)


@router.get(
    "/retrieval/indexes/{index_id}/chunks/{chunk_id}",
    response_model=RetrievalChunkSummaryResponse,
)
def get_retrieval_chunk(
    index_id: str,
    chunk_id: str,
    services: ServicesDep,
) -> RetrievalChunkSummaryResponse:
    item = services.retrieval.get_chunk(
        GetRetrievalChunkQuery(
            index_id=RetrievalIndexId(index_id.strip()),
            chunk_id=RetrievalChunkId(chunk_id.strip()),
        )
    )
    return chunk_response(item)


@router.post(
    "/retrieval/indexes/{index_id}/search",
    response_model=RetrievalSearchResultResponse,
)
def search_retrieval_index(
    index_id: str,
    body: RetrievalSearchRequest,
    services: ServicesDep,
) -> RetrievalSearchResultResponse:
    content_types = (
        tuple(RetrievalContentType(item) for item in body.content_types)
        if body.content_types
        else ()
    )
    result = services.retrieval.search(
        SearchRetrievalIndexQuery(
            index_id=RetrievalIndexId(index_id.strip()),
            query=RetrievalQuery(
                query_text=body.query_text,
                mode=RetrievalMode(body.mode),
                top_k=body.top_k,
                minimum_score=body.minimum_score if body.minimum_score is not None else 0.0,
                content_types=content_types,
                canonical_types=tuple(body.canonical_types or ()),
                canonical_ids=tuple(body.canonical_ids or ()),
                graph_node_ids=tuple(body.graph_node_ids or ()),
                include_source_references=body.include_source_references,
                include_score_breakdown=body.include_score_breakdown,
            ),
        )
    )
    return search_result_response(result)


@router.post(
    "/retrieval/indexes/{index_id}/context",
    response_model=RetrievalContextResponse,
)
def assemble_retrieval_context(
    index_id: str,
    body: RetrievalContextRequest,
    services: ServicesDep,
) -> RetrievalContextResponse:
    content_types = (
        tuple(RetrievalContentType(item) for item in body.content_types)
        if body.content_types
        else ()
    )
    result = services.retrieval.assemble_context(
        AssembleRetrievalContextQuery(
            index_id=RetrievalIndexId(index_id.strip()),
            query_text=body.query_text,
            mode=RetrievalMode(body.mode),
            top_k=body.top_k,
            max_tokens=body.max_tokens,
            content_types=content_types,
        )
    )
    return context_response(result)


@router.get(
    "/retrieval/indexes/{index_id}/statistics",
    response_model=RetrievalIndexStatisticsResponse,
)
def get_retrieval_index_statistics(
    index_id: str,
    services: ServicesDep,
) -> RetrievalIndexStatisticsResponse:
    result = services.retrieval.statistics(
        GetRetrievalIndexStatisticsQuery(index_id=RetrievalIndexId(index_id.strip()))
    )
    return statistics_response(result)
