"""Engineering Knowledge Graph domain — projection of CEIM snapshots."""

from __future__ import annotations

from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.errors import (
    GraphInvariantError,
    GraphProjectionError,
)
from codestrata_platform.domain.knowledge_graph.graph import EngineeringKnowledgeGraph
from codestrata_platform.domain.knowledge_graph.identifiers import (
    GraphEdgeId,
    GraphNodeId,
    GraphProjectionId,
    GraphProjectionKey,
    KnowledgeGraphId,
    deterministic_edge_id,
    deterministic_graph_id,
    deterministic_node_id,
)
from codestrata_platform.domain.knowledge_graph.lifecycle import GraphStatus, GraphVersion
from codestrata_platform.domain.knowledge_graph.node import (
    GraphNode,
    GraphProperty,
    GraphSourceReference,
)
from codestrata_platform.domain.knowledge_graph.ports import (
    GraphEdgeRepository,
    GraphNodeRepository,
    GraphQueryRepository,
    KnowledgeGraphRepository,
)
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType

__all__ = [
    "EngineeringKnowledgeGraph",
    "GraphEdge",
    "GraphEdgeId",
    "GraphEdgeRepository",
    "GraphEdgeType",
    "GraphInvariantError",
    "GraphNode",
    "GraphNodeId",
    "GraphNodeRepository",
    "GraphNodeType",
    "GraphProjectionError",
    "GraphProjectionId",
    "GraphProjectionKey",
    "GraphProperty",
    "GraphQueryRepository",
    "GraphSourceReference",
    "GraphStatus",
    "GraphVersion",
    "KnowledgeGraphId",
    "KnowledgeGraphRepository",
    "deterministic_edge_id",
    "deterministic_graph_id",
    "deterministic_node_id",
]
