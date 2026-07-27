"""Bounded in-process graph neighbor and path helpers."""

from __future__ import annotations

from collections import defaultdict, deque

from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.identifiers import GraphNodeId
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType

_HARD_MAX_PATH_DEPTH = 10


def bounded_path_depth(max_depth: int) -> int:
    return max(1, min(int(max_depth), _HARD_MAX_PATH_DEPTH))


def graph_neighbors(
    nodes: tuple[GraphNode, ...],
    edges: tuple[GraphEdge, ...],
    node_id: GraphNodeId,
    *,
    direction: str = "both",
    edge_types: tuple[GraphEdgeType, ...] | None = None,
    node_types: tuple[GraphNodeType, ...] | None = None,
    limit: int = 100,
) -> tuple[tuple[GraphEdge, GraphNode], ...]:
    node_by_id = {item.node_id.value: item for item in nodes}
    if node_id.value not in node_by_id:
        return ()
    allowed_edges = {item.value for item in edge_types} if edge_types else None
    allowed_nodes = {item.value for item in node_types} if node_types else None
    direction_key = direction.strip().lower() or "both"
    results: list[tuple[GraphEdge, GraphNode]] = []
    for edge in edges:
        if allowed_edges is not None and edge.edge_type.value not in allowed_edges:
            continue
        neighbor: GraphNode | None = None
        outgoing = direction_key in {"both", "out", "outgoing"}
        incoming = direction_key in {"both", "in", "incoming"}
        if outgoing and edge.source_node_id.value == node_id.value:
            neighbor = node_by_id.get(edge.target_node_id.value)
        elif incoming and edge.target_node_id.value == node_id.value:
            neighbor = node_by_id.get(edge.source_node_id.value)
        if neighbor is None:
            continue
        if allowed_nodes is not None and neighbor.node_type.value not in allowed_nodes:
            continue
        results.append((edge, neighbor))
        if len(results) >= max(1, limit):
            break
    return tuple(results)


def graph_paths(
    edges: tuple[GraphEdge, ...],
    *,
    source_node_id: GraphNodeId,
    target_node_id: GraphNodeId,
    max_depth: int = 5,
    edge_types: tuple[GraphEdgeType, ...] | None = None,
    max_paths: int = 20,
) -> tuple[tuple[GraphNodeId, ...], ...]:
    depth_limit = bounded_path_depth(max_depth)
    path_limit = max(1, int(max_paths))
    if source_node_id.value == target_node_id.value:
        return ((source_node_id,),)
    allowed_edges = {item.value for item in edge_types} if edge_types else None
    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        if allowed_edges is not None and edge.edge_type.value not in allowed_edges:
            continue
        adjacency[edge.source_node_id.value].append(edge.target_node_id.value)

    found: list[tuple[GraphNodeId, ...]] = []
    queue: deque[tuple[str, ...]] = deque(((source_node_id.value,),))
    while queue and len(found) < path_limit:
        path = queue.popleft()
        if len(path) - 1 >= depth_limit:
            continue
        for nxt in adjacency.get(path[-1], ()):
            if nxt in path:
                continue
            next_path = (*path, nxt)
            if nxt == target_node_id.value:
                found.append(tuple(GraphNodeId(item) for item in next_path))
                if len(found) >= path_limit:
                    break
                continue
            queue.append(next_path)
    return tuple(found)
