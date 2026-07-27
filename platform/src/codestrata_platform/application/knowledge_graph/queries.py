"""Knowledge graph application queries."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.knowledge_graph.identifiers import GraphNodeId, KnowledgeGraphId
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType
from codestrata_platform.domain.repository.ids import RepositoryId


@dataclass(frozen=True, slots=True)
class GetKnowledgeGraphQuery:
    graph_id: KnowledgeGraphId


@dataclass(frozen=True, slots=True)
class GetLatestRepositoryGraphQuery:
    repository_id: RepositoryId


@dataclass(frozen=True, slots=True)
class ListRepositoryGraphsQuery:
    repository_id: RepositoryId


@dataclass(frozen=True, slots=True)
class ListGraphNodesQuery:
    graph_id: KnowledgeGraphId
    node_type: GraphNodeType | None = None
    canonical_type: str | None = None
    canonical_id: str | None = None
    offset: int = 0
    limit: int = 100


@dataclass(frozen=True, slots=True)
class GetGraphNodeQuery:
    graph_id: KnowledgeGraphId
    node_id: GraphNodeId


@dataclass(frozen=True, slots=True)
class ListGraphEdgesQuery:
    graph_id: KnowledgeGraphId
    edge_type: GraphEdgeType | None = None
    offset: int = 0
    limit: int = 100


@dataclass(frozen=True, slots=True)
class GetNodeNeighborsQuery:
    graph_id: KnowledgeGraphId
    node_id: GraphNodeId
    direction: str = "both"
    edge_types: tuple[GraphEdgeType, ...] | None = None
    node_types: tuple[GraphNodeType, ...] | None = None
    limit: int = 100


@dataclass(frozen=True, slots=True)
class FindGraphPathQuery:
    graph_id: KnowledgeGraphId
    source_node_id: GraphNodeId
    target_node_id: GraphNodeId
    max_depth: int = 5
    edge_types: tuple[GraphEdgeType, ...] | None = None
    max_paths: int = 20


@dataclass(frozen=True, slots=True)
class GetTechnologyRelationshipsQuery:
    graph_id: KnowledgeGraphId


@dataclass(frozen=True, slots=True)
class GetFindingRelationshipsQuery:
    graph_id: KnowledgeGraphId


@dataclass(frozen=True, slots=True)
class GetRecommendationRelationshipsQuery:
    graph_id: KnowledgeGraphId
