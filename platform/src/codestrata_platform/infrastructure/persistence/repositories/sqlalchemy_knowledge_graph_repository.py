"""SqlAlchemyKnowledgeGraphRepository."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.graph import EngineeringKnowledgeGraph
from codestrata_platform.domain.knowledge_graph.identifiers import GraphNodeId, KnowledgeGraphId
from codestrata_platform.domain.knowledge_graph.lifecycle import GraphStatus
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.infrastructure.graph_traversal import graph_neighbors, graph_paths
from codestrata_platform.infrastructure.persistence.mappers.knowledge_graph_mapper import (
    KnowledgeGraphMapper,
)
from codestrata_platform.infrastructure.persistence.models.knowledge_graph_records import (
    EngineeringGraphEdgeRecord,
    EngineeringGraphNodeRecord,
    EngineeringGraphProjectionRecord,
    EngineeringKnowledgeGraphRecord,
)


class SqlAlchemyKnowledgeGraphRepository:
    """Durable KnowledgeGraphRepository + GraphQueryRepository adapter."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, graph_id: KnowledgeGraphId) -> EngineeringKnowledgeGraph | None:
        record = self._session.get(EngineeringKnowledgeGraphRecord, graph_id.value)
        if record is None:
            return None
        return self._to_domain(record)

    def save(self, graph: EngineeringKnowledgeGraph) -> None:
        record = self._session.get(EngineeringKnowledgeGraphRecord, graph.graph_id.value)
        if record is None:
            self._session.add(KnowledgeGraphMapper.to_record(graph))
        else:
            KnowledgeGraphMapper.apply_to_record(graph, record)

        graph_id = graph.graph_id.value
        self._session.execute(
            delete(EngineeringGraphEdgeRecord).where(
                EngineeringGraphEdgeRecord.graph_id == graph_id
            )
        )
        self._session.execute(
            delete(EngineeringGraphNodeRecord).where(
                EngineeringGraphNodeRecord.graph_id == graph_id
            )
        )

        node_records, edge_records = KnowledgeGraphMapper.child_records(graph)
        for child in node_records:
            self._session.add(child)
        self._session.flush()
        for child in edge_records:
            self._session.add(child)

        projection = self._session.get(
            EngineeringGraphProjectionRecord,
            graph.projection_id.value,
        )
        if projection is None:
            self._session.add(KnowledgeGraphMapper.to_projection_record(graph))
        else:
            KnowledgeGraphMapper.apply_to_projection_record(graph, projection)
        self._session.flush()

    def find_by_projection_key(
        self,
        projection_key: str,
    ) -> EngineeringKnowledgeGraph | None:
        record = self._session.scalars(
            select(EngineeringKnowledgeGraphRecord).where(
                EngineeringKnowledgeGraphRecord.projection_key == projection_key.strip()
            )
        ).first()
        if record is None:
            return None
        return self._to_domain(record)

    def list_by_repository(
        self,
        repository_id: RepositoryId,
    ) -> tuple[EngineeringKnowledgeGraph, ...]:
        records = self._session.scalars(
            select(EngineeringKnowledgeGraphRecord)
            .where(EngineeringKnowledgeGraphRecord.repository_id == repository_id.value)
            .order_by(EngineeringKnowledgeGraphRecord.graph_version.asc())
        ).all()
        return tuple(self._to_domain(record) for record in records)

    def get_latest_completed(
        self,
        repository_id: RepositoryId,
    ) -> EngineeringKnowledgeGraph | None:
        record = self._session.scalars(
            select(EngineeringKnowledgeGraphRecord)
            .where(
                EngineeringKnowledgeGraphRecord.repository_id == repository_id.value,
                EngineeringKnowledgeGraphRecord.status == GraphStatus.COMPLETED.value,
            )
            .order_by(EngineeringKnowledgeGraphRecord.graph_version.desc())
            .limit(1)
        ).first()
        if record is None:
            return None
        return self._to_domain(record)

    def find_by_snapshot(
        self,
        snapshot_id: EngineeringSnapshotId,
        *,
        projector_version: str | None = None,
    ) -> EngineeringKnowledgeGraph | None:
        statement = select(EngineeringKnowledgeGraphRecord).where(
            EngineeringKnowledgeGraphRecord.engineering_snapshot_id == snapshot_id.value
        )
        if projector_version is not None:
            statement = statement.where(
                EngineeringKnowledgeGraphRecord.projector_version == projector_version.strip()
            )
        statement = statement.order_by(EngineeringKnowledgeGraphRecord.graph_version.desc())
        record = self._session.scalars(statement).first()
        if record is None:
            return None
        return self._to_domain(record)

    def latest_graph_version_for_repository(self, repository_id: RepositoryId) -> int:
        value = self._session.scalar(
            select(func.max(EngineeringKnowledgeGraphRecord.graph_version)).where(
                EngineeringKnowledgeGraphRecord.repository_id == repository_id.value
            )
        )
        return int(value or 0)

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

    def _to_domain(self, record: EngineeringKnowledgeGraphRecord) -> EngineeringKnowledgeGraph:
        node_records = self._session.scalars(
            select(EngineeringGraphNodeRecord).where(
                EngineeringGraphNodeRecord.graph_id == record.id
            )
        ).all()
        edge_records = self._session.scalars(
            select(EngineeringGraphEdgeRecord).where(
                EngineeringGraphEdgeRecord.graph_id == record.id
            )
        ).all()
        nodes = tuple(KnowledgeGraphMapper.node_from_record(item) for item in node_records)
        edges = tuple(KnowledgeGraphMapper.edge_from_record(item) for item in edge_records)
        return KnowledgeGraphMapper.to_domain(record, nodes=nodes, edges=edges)
