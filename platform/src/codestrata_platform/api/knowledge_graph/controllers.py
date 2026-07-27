"""Thin Engineering Knowledge Graph controllers."""

from __future__ import annotations

from fastapi import APIRouter, Query, Response, status

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.knowledge_graph.dto import (
    BuildKnowledgeGraphRequest,
    GraphEdgeResponse,
    GraphNeighborResponse,
    GraphNodeResponse,
    GraphPathRequest,
    GraphPathResponse,
    KnowledgeGraphDetailsResponse,
    KnowledgeGraphSummaryResponse,
    RebuildKnowledgeGraphRequest,
)
from codestrata_platform.api.knowledge_graph.mappers import (
    details_response,
    edge_response,
    neighbor_response,
    node_response,
    path_response,
    projection_response,
    summary_response,
)
from codestrata_platform.application.knowledge_graph.commands import (
    BuildKnowledgeGraphCommand,
    RebuildKnowledgeGraphCommand,
)
from codestrata_platform.application.knowledge_graph.queries import (
    FindGraphPathQuery,
    GetGraphNodeQuery,
    GetKnowledgeGraphQuery,
    GetLatestRepositoryGraphQuery,
    GetNodeNeighborsQuery,
    ListGraphEdgesQuery,
    ListGraphNodesQuery,
    ListRepositoryGraphsQuery,
)
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.knowledge_graph.identifiers import GraphNodeId, KnowledgeGraphId
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType
from codestrata_platform.domain.repository.ids import RepositoryId

router = APIRouter(tags=["Knowledge Graphs"])


@router.post(
    "/knowledge-graphs",
    response_model=KnowledgeGraphDetailsResponse,
    status_code=status.HTTP_201_CREATED,
)
def build_knowledge_graph(
    body: BuildKnowledgeGraphRequest,
    services: ServicesDep,
    response: Response,
) -> KnowledgeGraphDetailsResponse:
    result = services.knowledge_graphs.build_knowledge_graph(
        BuildKnowledgeGraphCommand(
            snapshot_id=EngineeringSnapshotId(body.snapshot_id.strip()),
            projector_version=body.projector_version,
            projection_schema_version=body.projection_schema_version,
        )
    )
    if result.idempotent:
        response.status_code = status.HTTP_200_OK
    return projection_response(result)


@router.post(
    "/knowledge-graphs/{graph_id}/rebuild",
    response_model=KnowledgeGraphDetailsResponse,
)
def rebuild_knowledge_graph(
    graph_id: str,
    services: ServicesDep,
    body: RebuildKnowledgeGraphRequest | None = None,
) -> KnowledgeGraphDetailsResponse:
    request = body or RebuildKnowledgeGraphRequest()
    result = services.knowledge_graphs.rebuild_knowledge_graph(
        RebuildKnowledgeGraphCommand(
            graph_id=KnowledgeGraphId(graph_id.strip()),
            projector_version=request.projector_version,
            projection_schema_version=request.projection_schema_version,
        )
    )
    return projection_response(result)


@router.get("/knowledge-graphs/{graph_id}", response_model=KnowledgeGraphDetailsResponse)
def get_knowledge_graph(graph_id: str, services: ServicesDep) -> KnowledgeGraphDetailsResponse:
    details = services.knowledge_graphs.get_knowledge_graph(
        GetKnowledgeGraphQuery(graph_id=KnowledgeGraphId(graph_id.strip()))
    )
    return details_response(details)


@router.get(
    "/repositories/{repository_id}/knowledge-graphs",
    response_model=list[KnowledgeGraphSummaryResponse],
)
def list_repository_graphs(
    repository_id: str,
    services: ServicesDep,
) -> list[KnowledgeGraphSummaryResponse]:
    items = services.knowledge_graphs.list_repository_graphs(
        ListRepositoryGraphsQuery(repository_id=RepositoryId(repository_id.strip()))
    )
    return [summary_response(item) for item in items]


@router.get(
    "/repositories/{repository_id}/knowledge-graphs/latest",
    response_model=KnowledgeGraphDetailsResponse,
)
def get_latest_repository_graph(
    repository_id: str,
    services: ServicesDep,
) -> KnowledgeGraphDetailsResponse:
    details = services.knowledge_graphs.get_latest_repository_graph(
        GetLatestRepositoryGraphQuery(repository_id=RepositoryId(repository_id.strip()))
    )
    return details_response(details)


@router.get("/knowledge-graphs/{graph_id}/nodes", response_model=list[GraphNodeResponse])
def list_nodes(
    graph_id: str,
    services: ServicesDep,
    node_type: str | None = Query(default=None),
    canonical_type: str | None = Query(default=None),
    canonical_id: str | None = Query(default=None),
    page: int = Query(default=0, ge=0),
    size: int = Query(default=100, ge=1, le=500),
) -> list[GraphNodeResponse]:
    items = services.knowledge_graphs.list_graph_nodes(
        ListGraphNodesQuery(
            graph_id=KnowledgeGraphId(graph_id.strip()),
            node_type=GraphNodeType(node_type) if node_type else None,
            canonical_type=canonical_type,
            canonical_id=canonical_id,
            offset=page * size,
            limit=size,
        )
    )
    return [node_response(item) for item in items]


@router.get(
    "/knowledge-graphs/{graph_id}/nodes/{node_id}",
    response_model=GraphNodeResponse,
)
def get_node(
    graph_id: str,
    node_id: str,
    services: ServicesDep,
) -> GraphNodeResponse:
    details = services.knowledge_graphs.get_graph_node(
        GetGraphNodeQuery(
            graph_id=KnowledgeGraphId(graph_id.strip()),
            node_id=GraphNodeId(node_id.strip()),
        )
    )
    return node_response(details)


@router.get(
    "/knowledge-graphs/{graph_id}/nodes/{node_id}/neighbors",
    response_model=list[GraphNeighborResponse],
)
def get_neighbors(
    graph_id: str,
    node_id: str,
    services: ServicesDep,
    direction: str = Query(default="both"),
    size: int = Query(default=100, ge=1, le=500),
) -> list[GraphNeighborResponse]:
    items = services.knowledge_graphs.get_node_neighbors(
        GetNodeNeighborsQuery(
            graph_id=KnowledgeGraphId(graph_id.strip()),
            node_id=GraphNodeId(node_id.strip()),
            direction=direction,
            limit=size,
        )
    )
    return [neighbor_response(item) for item in items]


@router.get("/knowledge-graphs/{graph_id}/edges", response_model=list[GraphEdgeResponse])
def list_edges(
    graph_id: str,
    services: ServicesDep,
    edge_type: str | None = Query(default=None),
    page: int = Query(default=0, ge=0),
    size: int = Query(default=100, ge=1, le=500),
) -> list[GraphEdgeResponse]:
    items = services.knowledge_graphs.list_graph_edges(
        ListGraphEdgesQuery(
            graph_id=KnowledgeGraphId(graph_id.strip()),
            edge_type=GraphEdgeType(edge_type) if edge_type else None,
            offset=page * size,
            limit=size,
        )
    )
    return [edge_response(item) for item in items]


@router.post(
    "/knowledge-graphs/{graph_id}/paths",
    response_model=list[GraphPathResponse],
)
def find_paths(
    graph_id: str,
    body: GraphPathRequest,
    services: ServicesDep,
) -> list[GraphPathResponse]:
    edge_types = (
        tuple(GraphEdgeType(item) for item in body.edge_types) if body.edge_types else None
    )
    items = services.knowledge_graphs.find_graph_paths(
        FindGraphPathQuery(
            graph_id=KnowledgeGraphId(graph_id.strip()),
            source_node_id=GraphNodeId(body.source_node_id.strip()),
            target_node_id=GraphNodeId(body.target_node_id.strip()),
            max_depth=body.max_depth,
            edge_types=edge_types,
            max_paths=body.max_paths,
        )
    )
    return [path_response(item) for item in items]
