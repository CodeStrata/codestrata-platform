"""EngineeringGraphProjectionService and query orchestration."""

from __future__ import annotations

import os

from codestrata_platform.application.common.errors import NotFoundError, ValidationError
from codestrata_platform.application.knowledge_graph.commands import (
    BuildKnowledgeGraphCommand,
    FailKnowledgeGraphProjectionCommand,
    RebuildKnowledgeGraphCommand,
    SupersedeKnowledgeGraphCommand,
)
from codestrata_platform.application.knowledge_graph.errors import GraphTraversalLimitError
from codestrata_platform.application.knowledge_graph.models import (
    FindingRelationshipSummary,
    GraphEdgeSummary,
    GraphNeighborResult,
    GraphNodeDetails,
    GraphNodeSummary,
    GraphPathResult,
    GraphProjectionResult,
    KnowledgeGraphDetails,
    KnowledgeGraphSummary,
    RecommendationRelationshipSummary,
    TechnologyRelationshipSummary,
)
from codestrata_platform.application.knowledge_graph.projection import (
    DEFAULT_PROJECTION_SCHEMA_VERSION,
    DEFAULT_PROJECTOR_VERSION,
    build_projection_key,
    create_pending_graph,
    project_snapshot_into_graph,
)
from codestrata_platform.application.knowledge_graph.queries import (
    FindGraphPathQuery,
    GetFindingRelationshipsQuery,
    GetGraphNodeQuery,
    GetKnowledgeGraphQuery,
    GetLatestRepositoryGraphQuery,
    GetNodeNeighborsQuery,
    GetRecommendationRelationshipsQuery,
    GetTechnologyRelationshipsQuery,
    ListGraphEdgesQuery,
    ListGraphNodesQuery,
    ListRepositoryGraphsQuery,
)
from codestrata_platform.domain.engineering import (
    EngineeringSnapshotRepository,
    EngineeringSnapshotStatus,
)
from codestrata_platform.domain.knowledge_graph import (
    GraphNodeType,
    GraphProjectionKey,
    GraphQueryRepository,
    GraphStatus,
    KnowledgeGraphId,
    KnowledgeGraphRepository,
)

AUTO_PROJECT_ENV = "CODESTRATA_KNOWLEDGE_GRAPH_AUTO_PROJECT"
DEFAULT_MAX_DEPTH = 5
HARD_MAX_DEPTH = 10
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 500


def knowledge_graph_auto_project_enabled() -> bool:
    raw = os.environ.get(AUTO_PROJECT_ENV, "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


class EngineeringGraphProjectionService:
    """Build and query Engineering Knowledge Graphs from published CEIM snapshots."""

    def __init__(
        self,
        *,
        graphs: KnowledgeGraphRepository,
        snapshots: EngineeringSnapshotRepository,
        queries: GraphQueryRepository | None = None,
        projector_version: str = DEFAULT_PROJECTOR_VERSION,
        projection_schema_version: str = DEFAULT_PROJECTION_SCHEMA_VERSION,
    ) -> None:
        self._graphs = graphs
        self._snapshots = snapshots
        self._queries = queries
        self._projector_version = projector_version
        self._projection_schema_version = projection_schema_version

    def build_knowledge_graph(
        self,
        command: BuildKnowledgeGraphCommand,
    ) -> GraphProjectionResult:
        snapshot = self._require_published_snapshot(command.snapshot_id)
        projector_version = command.projector_version or self._projector_version
        schema_version = command.projection_schema_version or self._projection_schema_version
        projection_key = build_projection_key(
            snapshot,
            projector_version=projector_version,
            projection_schema_version=schema_version,
        )
        existing = self._graphs.find_by_projection_key(projection_key.value)
        if existing is not None and existing.status is GraphStatus.COMPLETED:
            return GraphProjectionResult(
                graph=KnowledgeGraphDetails.from_aggregate(existing),
                created=False,
                idempotent=True,
            )
        if existing is not None and existing.status is GraphStatus.FAILED:
            # Legacy/in-flight FAILED rows may still occupy the unique key.
            existing.projection_key = GraphProjectionKey(
                f"{projection_key.value}:f{existing.graph_version.value}"[:128]
            )
            self._graphs.save(existing)

        graph_version = (
            self._graphs.latest_graph_version_for_repository(snapshot.repository_id) + 1
        )
        if graph_version > 1:
            self._supersede_active_for_repository(snapshot.repository_id)

        graph = create_pending_graph(
            snapshot,
            graph_version=graph_version,
            projector_version=projector_version,
            projection_schema_version=schema_version,
        )
        graph.begin_projection()
        try:
            project_snapshot_into_graph(graph, snapshot)
            graph.complete()
        except Exception as error:  # noqa: BLE001 - projection boundary
            graph.fail(reason=str(error)[:1000])
            # Free the unique projection_key so deterministic retries can rebuild.
            graph.projection_key = GraphProjectionKey(
                f"{projection_key.value}:f{graph.graph_version.value}"[:128]
            )
            self._graphs.save(graph)
            raise ValidationError(
                f"Knowledge graph projection failed: {error}",
                reason_code="graph_projection_failed",
            ) from error

        self._graphs.save(graph)
        return GraphProjectionResult(
            graph=KnowledgeGraphDetails.from_aggregate(graph),
            created=True,
            idempotent=False,
        )

    def rebuild_knowledge_graph(
        self,
        command: RebuildKnowledgeGraphCommand,
    ) -> GraphProjectionResult:
        current = self._require_graph(command.graph_id)
        return self.build_knowledge_graph(
            BuildKnowledgeGraphCommand(
                snapshot_id=current.engineering_snapshot_id,
                projector_version=command.projector_version,
                projection_schema_version=command.projection_schema_version,
            )
        )

    def supersede_knowledge_graph(
        self,
        command: SupersedeKnowledgeGraphCommand,
    ) -> KnowledgeGraphDetails:
        graph = self._require_graph(command.graph_id)
        graph.supersede()
        self._graphs.save(graph)
        return KnowledgeGraphDetails.from_aggregate(graph)

    def fail_knowledge_graph_projection(
        self,
        command: FailKnowledgeGraphProjectionCommand,
    ) -> KnowledgeGraphDetails:
        graph = self._require_graph(command.graph_id)
        graph.fail(command.reason)
        self._graphs.save(graph)
        return KnowledgeGraphDetails.from_aggregate(graph)

    def get_knowledge_graph(self, query: GetKnowledgeGraphQuery) -> KnowledgeGraphDetails:
        return KnowledgeGraphDetails.from_aggregate(self._require_graph(query.graph_id))

    def get_latest_repository_graph(
        self,
        query: GetLatestRepositoryGraphQuery,
    ) -> KnowledgeGraphDetails:
        graph = self._graphs.get_latest_completed(query.repository_id)
        if graph is None:
            raise NotFoundError(
                f"Knowledge graph not found for repository {query.repository_id.value}",
                reason_code="knowledge_graph_not_found",
            )
        return KnowledgeGraphDetails.from_aggregate(graph)

    def list_repository_graphs(
        self,
        query: ListRepositoryGraphsQuery,
    ) -> tuple[KnowledgeGraphSummary, ...]:
        items = self._graphs.list_by_repository(query.repository_id)
        return tuple(KnowledgeGraphSummary.from_aggregate(item) for item in items)

    def list_graph_nodes(self, query: ListGraphNodesQuery) -> tuple[GraphNodeSummary, ...]:
        graph = self._require_graph(query.graph_id)
        nodes = graph.nodes
        if query.node_type is not None:
            nodes = tuple(item for item in nodes if item.node_type is query.node_type)
        if query.canonical_type is not None:
            nodes = tuple(
                item for item in nodes if item.canonical_type == query.canonical_type
            )
        if query.canonical_id is not None:
            nodes = tuple(item for item in nodes if item.canonical_id == query.canonical_id)
        offset = max(0, query.offset)
        limit = min(max(1, query.limit), MAX_PAGE_SIZE)
        page = nodes[offset : offset + limit]
        return tuple(GraphNodeSummary.from_domain(item) for item in page)

    def get_graph_node(self, query: GetGraphNodeQuery) -> GraphNodeDetails:
        graph = self._require_graph(query.graph_id)
        for node in graph.nodes:
            if node.node_id == query.node_id:
                return GraphNodeDetails.from_domain(node)
        raise NotFoundError(
            f"Graph node not found: {query.node_id.value}",
            reason_code="graph_node_not_found",
        )

    def list_graph_edges(self, query: ListGraphEdgesQuery) -> tuple[GraphEdgeSummary, ...]:
        graph = self._require_graph(query.graph_id)
        edges = graph.edges
        if query.edge_type is not None:
            edges = tuple(item for item in edges if item.edge_type is query.edge_type)
        offset = max(0, query.offset)
        limit = min(max(1, query.limit), MAX_PAGE_SIZE)
        page = edges[offset : offset + limit]
        return tuple(GraphEdgeSummary.from_domain(item) for item in page)

    def get_node_neighbors(
        self,
        query: GetNodeNeighborsQuery,
    ) -> tuple[GraphNeighborResult, ...]:
        graph = self._require_graph(query.graph_id)
        limit = min(max(1, query.limit), MAX_PAGE_SIZE)
        nodes = {item.node_id.value: item for item in graph.nodes}
        if query.node_id.value not in nodes:
            raise NotFoundError(
                f"Graph node not found: {query.node_id.value}",
                reason_code="graph_node_not_found",
            )
        if self._queries is not None:
            pairs = self._queries.neighbors(
                query.graph_id,
                query.node_id,
                direction=query.direction,
                edge_types=query.edge_types,
                node_types=query.node_types,
                limit=limit,
            )
            return tuple(
                GraphNeighborResult(
                    edge=GraphEdgeSummary.from_domain(edge),
                    node=GraphNodeSummary.from_domain(node),
                )
                for edge, node in pairs
            )

        results: list[GraphNeighborResult] = []
        for edge in graph.edges:
            if query.edge_types and edge.edge_type not in query.edge_types:
                continue
            neighbor_id = None
            if query.direction in {"out", "both"} and edge.source_node_id == query.node_id:
                neighbor_id = edge.target_node_id.value
            if query.direction in {"in", "both"} and edge.target_node_id == query.node_id:
                neighbor_id = edge.source_node_id.value
            if neighbor_id is None:
                continue
            neighbor = nodes.get(neighbor_id)
            if neighbor is None:
                continue
            if query.node_types and neighbor.node_type not in query.node_types:
                continue
            results.append(
                GraphNeighborResult(
                    edge=GraphEdgeSummary.from_domain(edge),
                    node=GraphNodeSummary.from_domain(neighbor),
                )
            )
            if len(results) >= limit:
                break
        return tuple(results)

    def find_graph_paths(self, query: FindGraphPathQuery) -> tuple[GraphPathResult, ...]:
        max_depth = query.max_depth
        if max_depth < 1:
            raise GraphTraversalLimitError(
                "max_depth must be >= 1",
                reason_code="invalid_max_depth",
            )
        if max_depth > HARD_MAX_DEPTH:
            raise GraphTraversalLimitError(
                f"max_depth may not exceed {HARD_MAX_DEPTH}",
                reason_code="max_depth_exceeded",
            )
        max_depth = min(max_depth, HARD_MAX_DEPTH)
        max_paths = min(max(1, query.max_paths), 50)
        graph = self._require_graph(query.graph_id)

        if self._queries is not None:
            paths = self._queries.paths(
                query.graph_id,
                source_node_id=query.source_node_id,
                target_node_id=query.target_node_id,
                max_depth=max_depth,
                edge_types=query.edge_types,
                max_paths=max_paths,
            )
            return tuple(
                GraphPathResult(node_ids=tuple(item.value for item in path))
                for path in paths
            )

        adjacency: dict[str, list[str]] = {}
        for edge in graph.edges:
            if query.edge_types and edge.edge_type not in query.edge_types:
                continue
            adjacency.setdefault(edge.source_node_id.value, []).append(edge.target_node_id.value)
            adjacency.setdefault(edge.target_node_id.value, []).append(edge.source_node_id.value)

        source = query.source_node_id.value
        target = query.target_node_id.value
        found: list[tuple[str, ...]] = []

        def _walk(path: list[str]) -> None:
            if len(found) >= max_paths:
                return
            if len(path) - 1 > max_depth:
                return
            current = path[-1]
            if current == target and len(path) > 1:
                found.append(tuple(path))
                return
            if len(path) - 1 == max_depth:
                return
            for nxt in adjacency.get(current, []):
                if nxt in path:
                    continue
                path.append(nxt)
                _walk(path)
                path.pop()
                if len(found) >= max_paths:
                    return

        _walk([source])
        return tuple(GraphPathResult(node_ids=item) for item in found)

    def get_technology_relationships(
        self,
        query: GetTechnologyRelationshipsQuery,
    ) -> tuple[TechnologyRelationshipSummary, ...]:
        graph = self._require_graph(query.graph_id)
        nodes = {item.node_id.value: item for item in graph.nodes}
        results: list[TechnologyRelationshipSummary] = []
        for edge in graph.edges:
            source = nodes.get(edge.source_node_id.value)
            target = nodes.get(edge.target_node_id.value)
            if source is None or target is None:
                continue
            if source.node_type is GraphNodeType.TECHNOLOGY:
                results.append(
                    TechnologyRelationshipSummary(
                        technology_node_id=source.node_id.value,
                        technology_key=source.canonical_id,
                        edge_type=edge.edge_type.value,
                        related_node_id=target.node_id.value,
                        related_node_type=target.node_type.value,
                    )
                )
            elif target.node_type is GraphNodeType.TECHNOLOGY:
                results.append(
                    TechnologyRelationshipSummary(
                        technology_node_id=target.node_id.value,
                        technology_key=target.canonical_id,
                        edge_type=edge.edge_type.value,
                        related_node_id=source.node_id.value,
                        related_node_type=source.node_type.value,
                    )
                )
        return tuple(results)

    def get_finding_relationships(
        self,
        query: GetFindingRelationshipsQuery,
    ) -> tuple[FindingRelationshipSummary, ...]:
        graph = self._require_graph(query.graph_id)
        nodes = {item.node_id.value: item for item in graph.nodes}
        results: list[FindingRelationshipSummary] = []
        for edge in graph.edges:
            source = nodes.get(edge.source_node_id.value)
            target = nodes.get(edge.target_node_id.value)
            if source is None or target is None:
                continue
            if source.node_type is GraphNodeType.FINDING:
                results.append(
                    FindingRelationshipSummary(
                        finding_node_id=source.node_id.value,
                        finding_id=source.canonical_id,
                        edge_type=edge.edge_type.value,
                        related_node_id=target.node_id.value,
                        related_node_type=target.node_type.value,
                    )
                )
            elif target.node_type is GraphNodeType.FINDING:
                results.append(
                    FindingRelationshipSummary(
                        finding_node_id=target.node_id.value,
                        finding_id=target.canonical_id,
                        edge_type=edge.edge_type.value,
                        related_node_id=source.node_id.value,
                        related_node_type=source.node_type.value,
                    )
                )
        return tuple(results)

    def get_recommendation_relationships(
        self,
        query: GetRecommendationRelationshipsQuery,
    ) -> tuple[RecommendationRelationshipSummary, ...]:
        graph = self._require_graph(query.graph_id)
        nodes = {item.node_id.value: item for item in graph.nodes}
        results: list[RecommendationRelationshipSummary] = []
        for edge in graph.edges:
            source = nodes.get(edge.source_node_id.value)
            target = nodes.get(edge.target_node_id.value)
            if source is None or target is None:
                continue
            if source.node_type is GraphNodeType.RECOMMENDATION:
                results.append(
                    RecommendationRelationshipSummary(
                        recommendation_node_id=source.node_id.value,
                        recommendation_id=source.canonical_id,
                        edge_type=edge.edge_type.value,
                        related_node_id=target.node_id.value,
                        related_node_type=target.node_type.value,
                    )
                )
        return tuple(results)

    def maybe_auto_project_for_snapshot(self, snapshot_id) -> GraphProjectionResult | None:
        if not knowledge_graph_auto_project_enabled():
            return None
        return self.build_knowledge_graph(BuildKnowledgeGraphCommand(snapshot_id=snapshot_id))

    def _require_published_snapshot(self, snapshot_id):
        snapshot = self._snapshots.get(snapshot_id)
        if snapshot is None:
            raise NotFoundError(
                f"Engineering snapshot not found: {snapshot_id.value}",
                reason_code="engineering_snapshot_not_found",
            )
        if snapshot.status is not EngineeringSnapshotStatus.PUBLISHED:
            raise ValidationError(
                "Knowledge graph requires a published EngineeringSnapshot",
                reason_code="snapshot_not_published",
            )
        return snapshot

    def _require_graph(self, graph_id: KnowledgeGraphId):
        graph = self._graphs.get(graph_id)
        if graph is None:
            raise NotFoundError(
                f"Knowledge graph not found: {graph_id.value}",
                reason_code="knowledge_graph_not_found",
            )
        return graph

    def _supersede_active_for_repository(self, repository_id) -> None:
        for item in self._graphs.list_by_repository(repository_id):
            if item.status is GraphStatus.COMPLETED:
                item.supersede()
                self._graphs.save(item)
