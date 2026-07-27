"""Application models for Engineering Knowledge Graph."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.graph import EngineeringKnowledgeGraph
from codestrata_platform.domain.knowledge_graph.lifecycle import GraphStatus
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType


@dataclass(frozen=True, slots=True)
class KnowledgeGraphSummary:
    graph_id: str
    repository_id: str
    assessment_id: str
    engineering_snapshot_id: str
    engineering_snapshot_version: int
    graph_version: int
    status: GraphStatus
    projection_key: str
    projector_version: str
    node_count: int
    edge_count: int
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_aggregate(cls, graph: EngineeringKnowledgeGraph) -> KnowledgeGraphSummary:
        return cls(
            graph_id=graph.graph_id.value,
            repository_id=graph.repository_id.value,
            assessment_id=graph.assessment_id.value,
            engineering_snapshot_id=graph.engineering_snapshot_id.value,
            engineering_snapshot_version=graph.engineering_snapshot_version,
            graph_version=graph.graph_version.value,
            status=graph.status,
            projection_key=graph.projection_key.value,
            projector_version=graph.projector_version,
            node_count=len(graph.nodes),
            edge_count=len(graph.edges),
            created_at=graph.audit.created_at.value,
            completed_at=graph.completed_at,
        )


@dataclass(frozen=True, slots=True)
class KnowledgeGraphDetails(KnowledgeGraphSummary):
    organization_id: str
    workspace_id: str
    intelligence_revision: int
    projection_schema_version: str
    failure_reason: str | None

    @classmethod
    def from_aggregate(cls, graph: EngineeringKnowledgeGraph) -> KnowledgeGraphDetails:
        summary = KnowledgeGraphSummary.from_aggregate(graph)
        return cls(
            graph_id=summary.graph_id,
            repository_id=summary.repository_id,
            assessment_id=summary.assessment_id,
            engineering_snapshot_id=summary.engineering_snapshot_id,
            engineering_snapshot_version=summary.engineering_snapshot_version,
            graph_version=summary.graph_version,
            status=summary.status,
            projection_key=summary.projection_key,
            projector_version=summary.projector_version,
            node_count=summary.node_count,
            edge_count=summary.edge_count,
            created_at=summary.created_at,
            completed_at=summary.completed_at,
            organization_id=graph.organization_id.value,
            workspace_id=graph.workspace_id.value,
            intelligence_revision=graph.intelligence_revision,
            projection_schema_version=graph.projection_schema_version,
            failure_reason=graph.failure_reason,
        )


@dataclass(frozen=True, slots=True)
class GraphNodeSummary:
    node_id: str
    node_type: GraphNodeType
    canonical_type: str
    canonical_id: str
    display_name: str

    @classmethod
    def from_domain(cls, node: GraphNode) -> GraphNodeSummary:
        return cls(
            node_id=node.node_id.value,
            node_type=node.node_type,
            canonical_type=node.canonical_type,
            canonical_id=node.canonical_id,
            display_name=node.display_name,
        )


@dataclass(frozen=True, slots=True)
class GraphNodeDetails(GraphNodeSummary):
    properties: dict[str, object]

    @classmethod
    def from_domain(cls, node: GraphNode) -> GraphNodeDetails:
        summary = GraphNodeSummary.from_domain(node)
        return cls(
            node_id=summary.node_id,
            node_type=summary.node_type,
            canonical_type=summary.canonical_type,
            canonical_id=summary.canonical_id,
            display_name=summary.display_name,
            properties=dict(node.properties.values),
        )


@dataclass(frozen=True, slots=True)
class GraphEdgeSummary:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: GraphEdgeType

    @classmethod
    def from_domain(cls, edge: GraphEdge) -> GraphEdgeSummary:
        return cls(
            edge_id=edge.edge_id.value,
            source_node_id=edge.source_node_id.value,
            target_node_id=edge.target_node_id.value,
            edge_type=edge.edge_type,
        )


@dataclass(frozen=True, slots=True)
class GraphNeighborResult:
    edge: GraphEdgeSummary
    node: GraphNodeSummary


@dataclass(frozen=True, slots=True)
class GraphPathResult:
    node_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GraphProjectionResult:
    graph: KnowledgeGraphDetails
    created: bool
    idempotent: bool


@dataclass(frozen=True, slots=True)
class TechnologyRelationshipSummary:
    technology_node_id: str
    technology_key: str
    edge_type: str
    related_node_id: str
    related_node_type: str


@dataclass(frozen=True, slots=True)
class FindingRelationshipSummary:
    finding_node_id: str
    finding_id: str
    edge_type: str
    related_node_id: str
    related_node_type: str


@dataclass(frozen=True, slots=True)
class RecommendationRelationshipSummary:
    recommendation_node_id: str
    recommendation_id: str
    edge_type: str
    related_node_id: str
    related_node_type: str
