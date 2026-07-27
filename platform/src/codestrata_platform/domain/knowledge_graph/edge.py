"""Graph edge value objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.knowledge_graph.identifiers import GraphEdgeId, GraphNodeId
from codestrata_platform.domain.knowledge_graph.node import GraphProperty, GraphSourceReference
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType


@dataclass(frozen=True, slots=True)
class GraphEdge:
    edge_id: GraphEdgeId
    source_node_id: GraphNodeId
    target_node_id: GraphNodeId
    edge_type: GraphEdgeType
    properties: GraphProperty = field(default_factory=GraphProperty)
    source_reference: GraphSourceReference | None = None

    def __post_init__(self) -> None:
        if self.source_node_id.value == self.target_node_id.value:
            # Self-reference policy is enforced by the aggregate using taxonomy allow-list.
            pass
        if not self.edge_type:
            raise InvalidValueError(
                "Graph edge type is required",
                reason_code="empty_graph_edge_type",
            )
