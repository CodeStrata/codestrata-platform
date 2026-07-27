"""Map application knowledge-graph models to API DTOs."""

from __future__ import annotations

from codestrata_platform.api.knowledge_graph.dto import (
    GraphEdgeResponse,
    GraphNeighborResponse,
    GraphNodeResponse,
    GraphPathResponse,
    KnowledgeGraphDetailsResponse,
    KnowledgeGraphSummaryResponse,
)
from codestrata_platform.application.knowledge_graph.models import (
    GraphEdgeSummary,
    GraphNeighborResult,
    GraphNodeDetails,
    GraphNodeSummary,
    GraphPathResult,
    GraphProjectionResult,
    KnowledgeGraphDetails,
    KnowledgeGraphSummary,
)


def summary_response(item: KnowledgeGraphSummary) -> KnowledgeGraphSummaryResponse:
    return KnowledgeGraphSummaryResponse(
        graph_id=item.graph_id,
        repository_id=item.repository_id,
        assessment_id=item.assessment_id,
        engineering_snapshot_id=item.engineering_snapshot_id,
        engineering_snapshot_version=item.engineering_snapshot_version,
        graph_version=item.graph_version,
        status=item.status.value,
        projection_key=item.projection_key,
        projector_version=item.projector_version,
        node_count=item.node_count,
        edge_count=item.edge_count,
        created_at=item.created_at,
        completed_at=item.completed_at,
    )


def details_response(
    item: KnowledgeGraphDetails,
    *,
    created: bool | None = None,
    idempotent: bool | None = None,
) -> KnowledgeGraphDetailsResponse:
    return KnowledgeGraphDetailsResponse(
        graph_id=item.graph_id,
        repository_id=item.repository_id,
        assessment_id=item.assessment_id,
        engineering_snapshot_id=item.engineering_snapshot_id,
        engineering_snapshot_version=item.engineering_snapshot_version,
        graph_version=item.graph_version,
        status=item.status.value,
        projection_key=item.projection_key,
        projector_version=item.projector_version,
        node_count=item.node_count,
        edge_count=item.edge_count,
        created_at=item.created_at,
        completed_at=item.completed_at,
        organization_id=item.organization_id,
        workspace_id=item.workspace_id,
        intelligence_revision=item.intelligence_revision,
        projection_schema_version=item.projection_schema_version,
        failure_reason=item.failure_reason,
        created=created,
        idempotent=idempotent,
    )


def projection_response(result: GraphProjectionResult) -> KnowledgeGraphDetailsResponse:
    return details_response(
        result.graph,
        created=result.created,
        idempotent=result.idempotent,
    )


def node_response(
    item: GraphNodeSummary | GraphNodeDetails,
) -> GraphNodeResponse:
    properties = dict(item.properties) if isinstance(item, GraphNodeDetails) else None
    return GraphNodeResponse(
        node_id=item.node_id,
        node_type=item.node_type.value,
        canonical_type=item.canonical_type,
        canonical_id=item.canonical_id,
        display_name=item.display_name,
        properties=properties,
    )


def edge_response(item: GraphEdgeSummary) -> GraphEdgeResponse:
    return GraphEdgeResponse(
        edge_id=item.edge_id,
        source_node_id=item.source_node_id,
        target_node_id=item.target_node_id,
        edge_type=item.edge_type.value,
    )


def neighbor_response(item: GraphNeighborResult) -> GraphNeighborResponse:
    return GraphNeighborResponse(
        edge=edge_response(item.edge),
        node=node_response(item.node),
    )


def path_response(item: GraphPathResult) -> GraphPathResponse:
    return GraphPathResponse(node_ids=list(item.node_ids))
