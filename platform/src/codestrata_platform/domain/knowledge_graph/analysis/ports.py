"""Ports for graph intelligence repository adapters."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.knowledge_graph.analysis.context import (
    GraphQueryContext,
    GraphQueryLimits,
    GraphQueryScope,
)
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.identifiers import GraphNodeId, KnowledgeGraphId
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType


class GraphIntelligenceRepository(Protocol):
    def get_graph_context(
        self,
        graph_id: KnowledgeGraphId,
        scope: GraphQueryScope,
    ) -> GraphQueryContext: ...

    def get_node(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
    ) -> GraphNode | None: ...

    def get_nodes(
        self,
        graph_id: KnowledgeGraphId,
        *,
        scope: GraphQueryScope,
        node_types: tuple[GraphNodeType, ...] | None = None,
        limit: int = 500,
    ) -> tuple[GraphNode, ...]: ...

    def get_edges(
        self,
        graph_id: KnowledgeGraphId,
        *,
        scope: GraphQueryScope,
        edge_types: tuple[GraphEdgeType, ...] | None = None,
        limit: int = 1000,
    ) -> tuple[GraphEdge, ...]: ...

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
    ) -> tuple[tuple[GraphEdge, GraphNode], ...]: ...

    def get_bounded_paths(
        self,
        graph_id: KnowledgeGraphId,
        *,
        scope: GraphQueryScope,
        source_node_id: GraphNodeId,
        target_node_id: GraphNodeId,
        limits: GraphQueryLimits,
        edge_types: tuple[GraphEdgeType, ...] | None = None,
    ) -> tuple[tuple[GraphNodeId, ...], ...]: ...

    def get_upstream_dependencies(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[GraphNode, ...]: ...

    def get_downstream_dependencies(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[GraphNode, ...]: ...

    def detect_cycles(
        self,
        graph_id: KnowledgeGraphId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[tuple[GraphNodeId, ...], ...]: ...

    def get_connected_findings(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[GraphNode, ...]: ...

    def get_connected_recommendations(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[GraphNode, ...]: ...

    def get_connected_evidence(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[GraphNode, ...]: ...

    def get_connected_components(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[GraphNode, ...]: ...

    def get_connected_technologies(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        scope: GraphQueryScope,
        limits: GraphQueryLimits,
    ) -> tuple[GraphNode, ...]: ...

    def get_graph_statistics(
        self,
        graph_id: KnowledgeGraphId,
        *,
        scope: GraphQueryScope,
    ) -> dict[str, int]: ...
