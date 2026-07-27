"""In-memory Engineering Knowledge Graph repository."""

from __future__ import annotations

from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.graph import EngineeringKnowledgeGraph
from codestrata_platform.domain.knowledge_graph.identifiers import GraphNodeId, KnowledgeGraphId
from codestrata_platform.domain.knowledge_graph.lifecycle import GraphStatus
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.infrastructure.graph_traversal import graph_neighbors, graph_paths


class InMemoryKnowledgeGraphRepository:
    """In-memory KnowledgeGraphRepository + GraphQueryRepository adapter."""

    def __init__(self) -> None:
        self._items: dict[str, EngineeringKnowledgeGraph] = {}

    def get(self, graph_id: KnowledgeGraphId) -> EngineeringKnowledgeGraph | None:
        item = self._items.get(graph_id.value)
        return item.snapshot() if item is not None else None

    def save(self, graph: EngineeringKnowledgeGraph) -> None:
        self._items[graph.graph_id.value] = graph.snapshot()

    def find_by_projection_key(
        self,
        projection_key: str,
    ) -> EngineeringKnowledgeGraph | None:
        key = projection_key.strip()
        for item in self._items.values():
            if item.projection_key.value == key:
                return item.snapshot()
        return None

    def list_by_repository(
        self,
        repository_id: RepositoryId,
    ) -> tuple[EngineeringKnowledgeGraph, ...]:
        return tuple(
            item.snapshot()
            for item in sorted(
                (
                    item
                    for item in self._items.values()
                    if item.repository_id == repository_id
                ),
                key=lambda item: item.graph_version.value,
            )
        )

    def get_latest_completed(
        self,
        repository_id: RepositoryId,
    ) -> EngineeringKnowledgeGraph | None:
        completed = [
            item
            for item in self._items.values()
            if item.repository_id == repository_id and item.status is GraphStatus.COMPLETED
        ]
        if not completed:
            return None
        latest = max(completed, key=lambda item: item.graph_version.value)
        return latest.snapshot()

    def find_by_snapshot(
        self,
        snapshot_id: EngineeringSnapshotId,
        *,
        projector_version: str | None = None,
    ) -> EngineeringKnowledgeGraph | None:
        matches = [
            item
            for item in self._items.values()
            if item.engineering_snapshot_id == snapshot_id
            and (
                projector_version is None
                or item.projector_version == projector_version.strip()
            )
        ]
        if not matches:
            return None
        latest = max(matches, key=lambda item: item.graph_version.value)
        return latest.snapshot()

    def latest_graph_version_for_repository(self, repository_id: RepositoryId) -> int:
        versions = [
            item.graph_version.value
            for item in self._items.values()
            if item.repository_id == repository_id
        ]
        return max(versions) if versions else 0

    def neighbors(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        *,
        direction: str = "both",
        edge_types: tuple[GraphEdgeType, ...] | None = None,
        node_types: tuple[GraphNodeType, ...] | None = None,
        limit: int = 100,
    ) -> tuple[tuple[GraphEdge, GraphNode], ...]:
        graph = self.get(graph_id)
        if graph is None:
            return ()
        return graph_neighbors(
            graph.nodes,
            graph.edges,
            node_id,
            direction=direction,
            edge_types=edge_types,
            node_types=node_types,
            limit=limit,
        )

    def paths(
        self,
        graph_id: KnowledgeGraphId,
        *,
        source_node_id: GraphNodeId,
        target_node_id: GraphNodeId,
        max_depth: int = 5,
        edge_types: tuple[GraphEdgeType, ...] | None = None,
        max_paths: int = 20,
    ) -> tuple[tuple[GraphNodeId, ...], ...]:
        graph = self.get(graph_id)
        if graph is None:
            return ()
        return graph_paths(
            graph.edges,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            max_depth=max_depth,
            edge_types=edge_types,
            max_paths=max_paths,
        )
