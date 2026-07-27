"""Ports for Engineering Knowledge Graph persistence and queries."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.graph import EngineeringKnowledgeGraph
from codestrata_platform.domain.knowledge_graph.identifiers import (
    GraphEdgeId,
    GraphNodeId,
    KnowledgeGraphId,
)
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType
from codestrata_platform.domain.repository.ids import RepositoryId


class KnowledgeGraphRepository(Protocol):
    def get(self, graph_id: KnowledgeGraphId) -> EngineeringKnowledgeGraph | None: ...

    def save(self, graph: EngineeringKnowledgeGraph) -> None: ...

    def find_by_projection_key(
        self,
        projection_key: str,
    ) -> EngineeringKnowledgeGraph | None: ...

    def list_by_repository(
        self,
        repository_id: RepositoryId,
    ) -> tuple[EngineeringKnowledgeGraph, ...]: ...

    def get_latest_completed(
        self,
        repository_id: RepositoryId,
    ) -> EngineeringKnowledgeGraph | None: ...

    def find_by_snapshot(
        self,
        snapshot_id: EngineeringSnapshotId,
        *,
        projector_version: str | None = None,
    ) -> EngineeringKnowledgeGraph | None: ...

    def latest_graph_version_for_repository(self, repository_id: RepositoryId) -> int: ...


class GraphNodeRepository(Protocol):
    def list_by_graph(
        self,
        graph_id: KnowledgeGraphId,
        *,
        node_type: GraphNodeType | None = None,
        canonical_type: str | None = None,
        canonical_id: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[GraphNode, ...]: ...

    def get(self, graph_id: KnowledgeGraphId, node_id: GraphNodeId) -> GraphNode | None: ...


class GraphEdgeRepository(Protocol):
    def list_by_graph(
        self,
        graph_id: KnowledgeGraphId,
        *,
        edge_type: GraphEdgeType | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[GraphEdge, ...]: ...

    def get(self, graph_id: KnowledgeGraphId, edge_id: GraphEdgeId) -> GraphEdge | None: ...


class GraphQueryRepository(Protocol):
    def neighbors(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        direction: str = "both",
        edge_types: tuple[GraphEdgeType, ...] | None = None,
        node_types: tuple[GraphNodeType, ...] | None = None,
        limit: int = 100,
    ) -> tuple[tuple[GraphEdge, GraphNode], ...]: ...

    def paths(
        self,
        graph_id: KnowledgeGraphId,
        *,
        source_node_id: GraphNodeId,
        target_node_id: GraphNodeId,
        max_depth: int = 5,
        edge_types: tuple[GraphEdgeType, ...] | None = None,
        max_paths: int = 20,
    ) -> tuple[tuple[GraphNodeId, ...], ...]: ...
