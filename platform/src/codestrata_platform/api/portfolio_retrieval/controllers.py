"""Thin Portfolio Retrieval controllers."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.portfolio_retrieval.dto import (
    BuildPortfolioRetrievalIndexRequest,
    PortfolioRetrievalChunkSummaryResponse,
    PortfolioRetrievalContextRequest,
    PortfolioRetrievalContextResponse,
    PortfolioRetrievalDocumentSummaryResponse,
    PortfolioRetrievalIndexDetailsResponse,
    PortfolioRetrievalIndexStatisticsResponse,
    PortfolioRetrievalIndexSummaryResponse,
    PortfolioRetrievalSearchRequest,
    PortfolioRetrievalSearchResultResponse,
    RebuildPortfolioRetrievalIndexRequest,
)
from codestrata_platform.api.portfolio_retrieval.mappers import (
    build_result_response,
    chunk_response,
    context_response,
    details_response,
    document_response,
    search_result_response,
    statistics_response,
    summary_response,
)
from codestrata_platform.application.portfolio_retrieval.commands import (
    BuildPortfolioRetrievalIndexCommand,
    RebuildPortfolioRetrievalIndexCommand,
)
from codestrata_platform.application.portfolio_retrieval.queries import (
    BuildPortfolioRetrievalContextQuery,
    GetLatestPortfolioRetrievalIndexQuery,
    GetPortfolioRetrievalChunkQuery,
    GetPortfolioRetrievalDocumentQuery,
    GetPortfolioRetrievalIndexQuery,
    GetPortfolioRetrievalIndexStatisticsQuery,
    ListPortfolioRetrievalDocumentsQuery,
    ListPortfolioRetrievalIndexesQuery,
    SearchPortfolioRetrievalIndexQuery,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    PortfolioRetrievalChunkId,
    PortfolioRetrievalDocumentId,
    PortfolioRetrievalIndexId,
)
from codestrata_platform.domain.portfolio_retrieval.lifecycle import RepositoryBalanceMode
from codestrata_platform.domain.portfolio_retrieval.query import PortfolioRetrievalQuery
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.taxonomy import RetrievalMode
from codestrata_platform.domain.workspace.ids import WorkspaceId

router = APIRouter(tags=["Portfolio Retrieval"])


@router.post(
    "/portfolio-retrieval/indexes",
    response_model=PortfolioRetrievalIndexDetailsResponse,
    status_code=status.HTTP_201_CREATED,
)
def build_portfolio_retrieval_index(
    body: BuildPortfolioRetrievalIndexRequest,
    services: ServicesDep,
    response: Response,
) -> PortfolioRetrievalIndexDetailsResponse:
    result = services.portfolio_retrieval.build_index(
        BuildPortfolioRetrievalIndexCommand(
            portfolio_id=PortfolioId(body.portfolio_id.strip()),
            organization_id=OrganizationId(body.organization_id.strip()),
            workspace_id=WorkspaceId(body.workspace_id.strip()),
            portfolio_snapshot_id=(
                PortfolioSnapshotId(body.portfolio_snapshot_id.strip())
                if body.portfolio_snapshot_id is not None
                else None
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
    "/portfolio-retrieval/indexes/{index_id}/rebuild",
    response_model=PortfolioRetrievalIndexDetailsResponse,
)
def rebuild_portfolio_retrieval_index(
    index_id: str,
    services: ServicesDep,
    body: RebuildPortfolioRetrievalIndexRequest | None = None,
) -> PortfolioRetrievalIndexDetailsResponse:
    request = body or RebuildPortfolioRetrievalIndexRequest()
    result = services.portfolio_retrieval.rebuild_index(
        RebuildPortfolioRetrievalIndexCommand(
            index_id=PortfolioRetrievalIndexId(index_id.strip()),
            embedding_provider=request.embedding_provider,
            embedding_model=request.embedding_model,
            embedding_dimension=request.embedding_dimension,
            force=request.force,
        )
    )
    return build_result_response(result)


@router.get(
    "/portfolio-retrieval/indexes/{index_id}",
    response_model=PortfolioRetrievalIndexDetailsResponse,
)
def get_portfolio_retrieval_index(
    index_id: str,
    services: ServicesDep,
) -> PortfolioRetrievalIndexDetailsResponse:
    details = services.portfolio_retrieval.get(
        GetPortfolioRetrievalIndexQuery(index_id=PortfolioRetrievalIndexId(index_id.strip()))
    )
    return details_response(details)


@router.get(
    "/portfolios/{portfolio_id}/retrieval-indexes",
    response_model=list[PortfolioRetrievalIndexSummaryResponse],
)
def list_portfolio_retrieval_indexes(
    portfolio_id: str,
    services: ServicesDep,
) -> list[PortfolioRetrievalIndexSummaryResponse]:
    items = services.portfolio_retrieval.list(
        ListPortfolioRetrievalIndexesQuery(portfolio_id=PortfolioId(portfolio_id.strip()))
    )
    return [summary_response(item) for item in items]


@router.get(
    "/portfolios/{portfolio_id}/retrieval-indexes/latest",
    response_model=PortfolioRetrievalIndexDetailsResponse,
)
def get_latest_portfolio_retrieval_index(
    portfolio_id: str,
    services: ServicesDep,
) -> PortfolioRetrievalIndexDetailsResponse:
    details = services.portfolio_retrieval.get_latest(
        GetLatestPortfolioRetrievalIndexQuery(portfolio_id=PortfolioId(portfolio_id.strip()))
    )
    return details_response(details)


@router.get(
    "/portfolio-retrieval/indexes/{index_id}/documents",
    response_model=list[PortfolioRetrievalDocumentSummaryResponse],
)
def list_portfolio_retrieval_documents(
    index_id: str,
    services: ServicesDep,
    content_type: Annotated[list[str] | None, Query()] = None,
    page: Annotated[int, Query(ge=0)] = 0,
    size: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[PortfolioRetrievalDocumentSummaryResponse]:
    content_types = (
        tuple(PortfolioRetrievalContentType(item) for item in content_type) if content_type else ()
    )
    items = services.portfolio_retrieval.list_documents(
        ListPortfolioRetrievalDocumentsQuery(
            index_id=PortfolioRetrievalIndexId(index_id.strip()),
            offset=page * size,
            limit=size,
            content_types=content_types,
        )
    )
    return [document_response(item) for item in items]


@router.get(
    "/portfolio-retrieval/indexes/{index_id}/documents/{document_id}",
    response_model=PortfolioRetrievalDocumentSummaryResponse,
)
def get_portfolio_retrieval_document(
    index_id: str,
    document_id: str,
    services: ServicesDep,
) -> PortfolioRetrievalDocumentSummaryResponse:
    item = services.portfolio_retrieval.get_document(
        GetPortfolioRetrievalDocumentQuery(
            index_id=PortfolioRetrievalIndexId(index_id.strip()),
            document_id=PortfolioRetrievalDocumentId(document_id.strip()),
        )
    )
    return document_response(item)


@router.get(
    "/portfolio-retrieval/indexes/{index_id}/chunks/{chunk_id}",
    response_model=PortfolioRetrievalChunkSummaryResponse,
)
def get_portfolio_retrieval_chunk(
    index_id: str,
    chunk_id: str,
    services: ServicesDep,
) -> PortfolioRetrievalChunkSummaryResponse:
    item = services.portfolio_retrieval.get_chunk(
        GetPortfolioRetrievalChunkQuery(
            index_id=PortfolioRetrievalIndexId(index_id.strip()),
            chunk_id=PortfolioRetrievalChunkId(chunk_id.strip()),
        )
    )
    return chunk_response(item)


@router.post(
    "/portfolio-retrieval/indexes/{index_id}/search",
    response_model=PortfolioRetrievalSearchResultResponse,
)
def search_portfolio_retrieval_index(
    index_id: str,
    body: PortfolioRetrievalSearchRequest,
    services: ServicesDep,
) -> PortfolioRetrievalSearchResultResponse:
    content_types = (
        tuple(PortfolioRetrievalContentType(item) for item in body.content_types)
        if body.content_types
        else ()
    )
    repository_ids = tuple(
        RepositoryId(item.strip()) for item in (body.repository_ids or ()) if item.strip()
    )
    exclude_repository_ids = tuple(
        RepositoryId(item.strip())
        for item in (body.exclude_repository_ids or ())
        if item.strip()
    )
    result = services.portfolio_retrieval.search(
        SearchPortfolioRetrievalIndexQuery(
            index_id=PortfolioRetrievalIndexId(index_id.strip()),
            query=PortfolioRetrievalQuery(
                query_text=body.query_text,
                mode=RetrievalMode(body.mode),
                top_k=body.top_k,
                content_types=content_types,
                repository_ids=repository_ids,
                exclude_repository_ids=exclude_repository_ids,
                repository_balance_mode=RepositoryBalanceMode(body.repository_balance_mode),
                include_portfolio_aggregates=body.include_portfolio_aggregates,
                include_repository_context=body.include_repository_context,
                include_score_breakdown=body.include_score_breakdown,
            ),
        )
    )
    return search_result_response(result)


@router.post(
    "/portfolio-retrieval/indexes/{index_id}/context",
    response_model=PortfolioRetrievalContextResponse,
)
def assemble_portfolio_retrieval_context(
    index_id: str,
    body: PortfolioRetrievalContextRequest,
    services: ServicesDep,
) -> PortfolioRetrievalContextResponse:
    content_types = (
        tuple(PortfolioRetrievalContentType(item) for item in body.content_types)
        if body.content_types
        else ()
    )
    result = services.portfolio_retrieval.assemble_context(
        BuildPortfolioRetrievalContextQuery(
            index_id=PortfolioRetrievalIndexId(index_id.strip()),
            query_text=body.query_text,
            mode=RetrievalMode(body.mode),
            top_k=body.top_k,
            max_tokens=body.max_tokens,
            max_repositories=body.max_repositories,
            content_types=content_types,
            repository_balance_mode=RepositoryBalanceMode(body.repository_balance_mode),
        )
    )
    return context_response(result)


@router.get(
    "/portfolio-retrieval/indexes/{index_id}/statistics",
    response_model=PortfolioRetrievalIndexStatisticsResponse,
)
def get_portfolio_retrieval_index_statistics(
    index_id: str,
    services: ServicesDep,
) -> PortfolioRetrievalIndexStatisticsResponse:
    result = services.portfolio_retrieval.statistics(
        GetPortfolioRetrievalIndexStatisticsQuery(
            index_id=PortfolioRetrievalIndexId(index_id.strip())
        )
    )
    return statistics_response(result)
