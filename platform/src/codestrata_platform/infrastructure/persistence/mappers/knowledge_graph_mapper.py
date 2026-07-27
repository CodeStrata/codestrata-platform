"""EngineeringKnowledgeGraph ↔ persistence record mapper."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.graph import EngineeringKnowledgeGraph
from codestrata_platform.domain.knowledge_graph.identifiers import (
    GraphEdgeId,
    GraphNodeId,
    GraphProjectionId,
    GraphProjectionKey,
    KnowledgeGraphId,
)
from codestrata_platform.domain.knowledge_graph.lifecycle import GraphStatus, GraphVersion
from codestrata_platform.domain.knowledge_graph.node import (
    GraphNode,
    GraphProperty,
    GraphSourceReference,
)
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers._helpers import (
    audit_from_record,
    ensure_utc,
)
from codestrata_platform.infrastructure.persistence.models.knowledge_graph_records import (
    EngineeringGraphEdgeRecord,
    EngineeringGraphNodeRecord,
    EngineeringGraphProjectionRecord,
    EngineeringKnowledgeGraphRecord,
)


class KnowledgeGraphMapper:
    @staticmethod
    def to_record(graph: EngineeringKnowledgeGraph) -> EngineeringKnowledgeGraphRecord:
        return EngineeringKnowledgeGraphRecord(
            id=graph.graph_id.value,
            projection_id=graph.projection_id.value,
            organization_id=graph.organization_id.value,
            workspace_id=graph.workspace_id.value,
            repository_id=graph.repository_id.value,
            assessment_id=graph.assessment_id.value,
            engineering_snapshot_id=graph.engineering_snapshot_id.value,
            engineering_snapshot_version=graph.engineering_snapshot_version,
            intelligence_revision=graph.intelligence_revision,
            graph_version=graph.graph_version.value,
            status=graph.status.value,
            projection_key=graph.projection_key.value,
            projection_schema_version=graph.projection_schema_version,
            projector_version=graph.projector_version,
            created_at=graph.audit.created_at.value,
            updated_at=graph.audit.updated_at.value,
            completed_at=graph.completed_at,
            superseded_at=graph.superseded_at,
            failure_reason=graph.failure_reason,
            optimistic_version=graph._version,
        )

    @staticmethod
    def apply_to_record(
        graph: EngineeringKnowledgeGraph,
        record: EngineeringKnowledgeGraphRecord,
    ) -> None:
        record.projection_id = graph.projection_id.value
        record.organization_id = graph.organization_id.value
        record.workspace_id = graph.workspace_id.value
        record.repository_id = graph.repository_id.value
        record.assessment_id = graph.assessment_id.value
        record.engineering_snapshot_id = graph.engineering_snapshot_id.value
        record.engineering_snapshot_version = graph.engineering_snapshot_version
        record.intelligence_revision = graph.intelligence_revision
        record.graph_version = graph.graph_version.value
        record.status = graph.status.value
        record.projection_key = graph.projection_key.value
        record.projection_schema_version = graph.projection_schema_version
        record.projector_version = graph.projector_version
        record.created_at = graph.audit.created_at.value
        record.updated_at = graph.audit.updated_at.value
        record.completed_at = graph.completed_at
        record.superseded_at = graph.superseded_at
        record.failure_reason = graph.failure_reason
        record.optimistic_version = graph._version

    @staticmethod
    def to_projection_record(
        graph: EngineeringKnowledgeGraph,
    ) -> EngineeringGraphProjectionRecord:
        return EngineeringGraphProjectionRecord(
            id=graph.projection_id.value,
            graph_id=graph.graph_id.value,
            projection_key=graph.projection_key.value,
            projection_schema_version=graph.projection_schema_version,
            projector_version=graph.projector_version,
            status=graph.status.value,
            created_at=graph.audit.created_at.value,
            updated_at=graph.audit.updated_at.value,
        )

    @staticmethod
    def apply_to_projection_record(
        graph: EngineeringKnowledgeGraph,
        record: EngineeringGraphProjectionRecord,
    ) -> None:
        record.graph_id = graph.graph_id.value
        record.projection_key = graph.projection_key.value
        record.projection_schema_version = graph.projection_schema_version
        record.projector_version = graph.projector_version
        record.status = graph.status.value
        record.created_at = graph.audit.created_at.value
        record.updated_at = graph.audit.updated_at.value

    @staticmethod
    def to_domain(
        record: EngineeringKnowledgeGraphRecord,
        *,
        nodes: tuple[GraphNode, ...] = (),
        edges: tuple[GraphEdge, ...] = (),
    ) -> EngineeringKnowledgeGraph:
        return EngineeringKnowledgeGraph(
            graph_id=KnowledgeGraphId(record.id),
            projection_id=GraphProjectionId(record.projection_id),
            organization_id=OrganizationId(record.organization_id),
            workspace_id=WorkspaceId(record.workspace_id),
            repository_id=RepositoryId(record.repository_id),
            assessment_id=AssessmentId(record.assessment_id),
            engineering_snapshot_id=EngineeringSnapshotId(record.engineering_snapshot_id),
            engineering_snapshot_version=record.engineering_snapshot_version,
            intelligence_revision=record.intelligence_revision,
            graph_version=GraphVersion(record.graph_version),
            status=GraphStatus(record.status),
            projection_key=GraphProjectionKey(record.projection_key),
            projection_schema_version=record.projection_schema_version,
            projector_version=record.projector_version,
            nodes=nodes,
            edges=edges,
            audit=audit_from_record(
                created_at=record.created_at,
                updated_at=record.updated_at,
            ),
            completed_at=(
                ensure_utc(record.completed_at) if record.completed_at is not None else None
            ),
            superseded_at=(
                ensure_utc(record.superseded_at) if record.superseded_at is not None else None
            ),
            failure_reason=record.failure_reason,
            _version=record.optimistic_version,
        )

    @staticmethod
    def properties_to_json(properties: GraphProperty) -> dict[str, Any]:
        return dict(properties.values)

    @staticmethod
    def properties_from_json(data: dict[str, Any] | None) -> GraphProperty:
        return GraphProperty(values=dict(data or {}))

    @staticmethod
    def source_reference_to_json(
        reference: GraphSourceReference | None,
    ) -> dict[str, Any] | None:
        if reference is None:
            return None
        return {
            "snapshot_id": reference.snapshot_id,
            "canonical_type": reference.canonical_type,
            "canonical_id": reference.canonical_id,
        }

    @staticmethod
    def source_reference_from_json(
        data: dict[str, Any] | None,
    ) -> GraphSourceReference | None:
        if not data:
            return None
        return GraphSourceReference(
            snapshot_id=str(data["snapshot_id"]),
            canonical_type=str(data["canonical_type"]),
            canonical_id=str(data["canonical_id"]),
        )

    @staticmethod
    def node_to_record(
        node: GraphNode,
        *,
        graph_id: str,
        created_at: datetime,
    ) -> EngineeringGraphNodeRecord:
        return EngineeringGraphNodeRecord(
            node_id=node.node_id.value,
            graph_id=graph_id,
            node_type=node.node_type.value,
            canonical_type=node.canonical_type,
            canonical_id=node.canonical_id,
            display_name=node.display_name,
            properties_json=KnowledgeGraphMapper.properties_to_json(node.properties),
            source_reference_json=KnowledgeGraphMapper.source_reference_to_json(
                node.source_reference
            ),
            created_at=created_at,
        )

    @staticmethod
    def node_from_record(record: EngineeringGraphNodeRecord) -> GraphNode:
        return GraphNode(
            node_id=GraphNodeId(record.node_id),
            node_type=GraphNodeType(record.node_type),
            canonical_type=record.canonical_type,
            canonical_id=record.canonical_id,
            display_name=record.display_name,
            properties=KnowledgeGraphMapper.properties_from_json(record.properties_json),
            source_reference=KnowledgeGraphMapper.source_reference_from_json(
                record.source_reference_json
            ),
        )

    @staticmethod
    def edge_to_record(
        edge: GraphEdge,
        *,
        graph_id: str,
        created_at: datetime,
    ) -> EngineeringGraphEdgeRecord:
        return EngineeringGraphEdgeRecord(
            edge_id=edge.edge_id.value,
            graph_id=graph_id,
            source_node_id=edge.source_node_id.value,
            target_node_id=edge.target_node_id.value,
            edge_type=edge.edge_type.value,
            properties_json=KnowledgeGraphMapper.properties_to_json(edge.properties),
            source_reference_json=KnowledgeGraphMapper.source_reference_to_json(
                edge.source_reference
            ),
            created_at=created_at,
        )

    @staticmethod
    def edge_from_record(record: EngineeringGraphEdgeRecord) -> GraphEdge:
        return GraphEdge(
            edge_id=GraphEdgeId(record.edge_id),
            source_node_id=GraphNodeId(record.source_node_id),
            target_node_id=GraphNodeId(record.target_node_id),
            edge_type=GraphEdgeType(record.edge_type),
            properties=KnowledgeGraphMapper.properties_from_json(record.properties_json),
            source_reference=KnowledgeGraphMapper.source_reference_from_json(
                record.source_reference_json
            ),
        )

    @staticmethod
    def child_records(
        graph: EngineeringKnowledgeGraph,
    ) -> tuple[tuple[EngineeringGraphNodeRecord, ...], tuple[EngineeringGraphEdgeRecord, ...]]:
        created_at = graph.audit.created_at.value
        graph_id = graph.graph_id.value
        nodes = tuple(
            KnowledgeGraphMapper.node_to_record(node, graph_id=graph_id, created_at=created_at)
            for node in graph.nodes
        )
        edges = tuple(
            KnowledgeGraphMapper.edge_to_record(edge, graph_id=graph_id, created_at=created_at)
            for edge in graph.edges
        )
        return nodes, edges
