"""Shared graph intelligence repository implementation over loaded graphs."""

from __future__ import annotations

from codestrata_platform.application.knowledge_graph.intelligence.errors import (
    GraphNotFoundError,
    GraphNotReadyError,
)
from codestrata_platform.domain.knowledge_graph.analysis.context import (
    GraphQueryContext,
    GraphQueryLimits,
    GraphQueryScope,
)
from codestrata_platform.domain.knowledge_graph.analysis.dependency import (
    analyze_dependencies,
    detect_cycles,
)
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.graph import EngineeringKnowledgeGraph
from codestrata_platform.domain.knowledge_graph.identifiers import GraphNodeId, KnowledgeGraphId
from codestrata_platform.domain.knowledge_graph.lifecycle import GraphStatus
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.ports import KnowledgeGraphRepository
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType
from codestrata_platform.infrastructure.graph_traversal import graph_neighbors, graph_paths


class GraphIntelligenceRepositoryBase:
    """Storage-neutral GraphIntelligenceRepository backed by KnowledgeGraphRepository."""

    def __init__(self, graphs: KnowledgeGraphRepository) -> None:
        self._graphs = graphs

    def _require_graph(
        self,
        graph_id: KnowledgeGraphId,
        scope: GraphQueryScope,
    ) -> EngineeringKnowledgeGraph:
        graph = self._graphs.get(graph_id)
        if graph is None:
            raise GraphNotFoundError(graph_id.value)
        if graph.status is not GraphStatus.COMPLETED:
            raise GraphNotReadyError(
                f"Knowledge graph {graph_id.value} is not completed",
                reason_code="graph_not_completed",
            )
        if (
            graph.organization_id != scope.organization_id
            or graph.workspace_id != scope.workspace_id
            or graph.repository_id != scope.repository_id
        ):
            raise GraphNotFoundError(graph_id.value)
        return graph

    def get_graph_context(
        self,
        graph_id: KnowledgeGraphId,
        scope: GraphQueryScope,
    ) -> GraphQueryContext:
        graph = self._require_graph(graph_id, scope)
        return GraphQueryContext(
            organization_id=graph.organization_id,
            workspace_id=graph.workspace_id,
            repository_id=graph.repository_id,
            graph_id=graph.graph_id,
            graph_version=graph.graph_version,
            engineering_snapshot_id=graph.engineering_snapshot_id,
        )

    def get_node(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
    ) -> GraphNode | None:
        graph = self._require_graph(graph_id, scope)
        return next((item for item in graph.nodes if item.node_id == node_id), None)

    def get_nodes(
        self,
        graph_id: KnowledgeGraphId,
        *,
        scope: GraphQueryScope,
        node_types: tuple[GraphNodeType, ...] | None = None,
        limit: int = 500,
    ) -> tuple[GraphNode, ...]:
        graph = self._require_graph(graph_id, scope)
        nodes = graph.nodes
        if node_types:
            allowed = set(node_types)
            nodes = tuple(item for item in nodes if item.node_type in allowed)
        return nodes[: max(1, limit)]

    def get_edges(
        self,
        graph_id: KnowledgeGraphId,
        *,
        scope: GraphQueryScope,
        edge_types: tuple[GraphEdgeType, ...] | None = None,
        limit: int = 1000,
    ) -> tuple[GraphEdge, ...]:
        graph = self._require_graph(graph_id, scope)
        edges = graph.edges
        if edge_types:
            allowed = set(edge_types)
            edges = tuple(item for item in edges if item.edge_type in allowed)
        return edges[: max(1, limit)]

    def get_neighbors(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
        direction: str = "both",
        edge_types: tuple[GraphEdgeType, ...] | None = None,
        node_types: tuple[GraphNodeType, ...] | None = None,
    ) -> tuple[tuple[GraphEdge, GraphNode], ...]:
        graph = self._require_graph(graph_id, scope)
        return graph_neighbors(
            graph.nodes,
            graph.edges,
            node_id,
            direction=direction,
            edge_types=edge_types,
            node_types=node_types,
            limit=min(limits.maximum_nodes, limits.maximum_edges),
        )

    def get_bounded_paths(
        self,
        graph_id: KnowledgeGraphId,
        *,
        scope: GraphQueryScope,
        source_node_id: GraphNodeId,
        target_node_id: GraphNodeId,
        limits: GraphQueryLimits,
        edge_types: tuple[GraphEdgeType, ...] | None = None,
    ) -> tuple[tuple[GraphNodeId, ...], ...]:
        graph = self._require_graph(graph_id, scope)
        return graph_paths(
            graph.edges,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            max_depth=limits.maximum_depth,
            edge_types=edge_types,
            max_paths=limits.maximum_paths,
        )

    def get_upstream_dependencies(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[GraphNode, ...]:
        graph = self._require_graph(graph_id, scope)
        analysis = analyze_dependencies(
            graph.nodes,
            graph.edges,
            subject_node_id=node_id.value,
            max_depth=limits.maximum_depth,
            max_nodes=limits.maximum_nodes,
            max_paths=limits.maximum_paths,
        )
        node_map = {item.node_id.value: item for item in graph.nodes}
        return tuple(
            node_map[item]
            for item in analysis.upstream_dependencies
            if item in node_map
        )[: limits.maximum_nodes]

    def get_downstream_dependencies(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[GraphNode, ...]:
        graph = self._require_graph(graph_id, scope)
        analysis = analyze_dependencies(
            graph.nodes,
            graph.edges,
            subject_node_id=node_id.value,
            max_depth=limits.maximum_depth,
            max_nodes=limits.maximum_nodes,
            max_paths=limits.maximum_paths,
        )
        node_map = {item.node_id.value: item for item in graph.nodes}
        return tuple(
            node_map[item]
            for item in analysis.downstream_dependencies
            if item in node_map
        )[: limits.maximum_nodes]

    def detect_cycles(
        self,
        graph_id: KnowledgeGraphId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[tuple[GraphNodeId, ...], ...]:
        graph = self._require_graph(graph_id, scope)
        cycles = detect_cycles(
            graph.nodes,
            graph.edges,
            max_depth=limits.maximum_depth,
            max_cycles=limits.maximum_paths,
        )
        return tuple(tuple(GraphNodeId(item) for item in cycle.node_ids) for cycle in cycles)

    def get_connected_findings(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[GraphNode, ...]:
        return self._connected_of_type(
            graph_id, node_id, scope=scope, limits=limits, node_type=GraphNodeType.FINDING
        )

    def get_connected_recommendations(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[GraphNode, ...]:
        return self._connected_of_type(
            graph_id,
            node_id,
            scope=scope,
            limits=limits,
            node_type=GraphNodeType.RECOMMENDATION,
        )

    def get_connected_evidence(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[GraphNode, ...]:
        return self._connected_of_type(
            graph_id, node_id, scope=scope, limits=limits, node_type=GraphNodeType.EVIDENCE
        )

    def get_connected_components(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[GraphNode, ...]:
        return self._connected_of_type(
            graph_id, node_id, scope=scope, limits=limits, node_type=GraphNodeType.COMPONENT
        )

    def get_connected_technologies(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[GraphNode, ...]:
        return self._connected_of_type(
            graph_id, node_id, scope=scope, limits=limits, node_type=GraphNodeType.TECHNOLOGY
        )

    def get_graph_statistics(
        self,
        graph_id: KnowledgeGraphId,
        *,
        scope: GraphQueryScope,
    ) -> dict[str, int]:
        graph = self._require_graph(graph_id, scope)
        counts: dict[str, int] = {"nodes": len(graph.nodes), "edges": len(graph.edges)}
        for node in graph.nodes:
            key = f"node:{node.node_type.value}"
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _connected_of_type(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
        node_type: GraphNodeType,
    ) -> tuple[GraphNode, ...]:
        pairs = self.get_neighbors(
            graph_id,
            node_id,
            scope=scope,
            limits=limits,
            direction="both",
            node_types=(node_type,),
        )
        return tuple(node for _edge, node in pairs)[: limits.maximum_nodes]
