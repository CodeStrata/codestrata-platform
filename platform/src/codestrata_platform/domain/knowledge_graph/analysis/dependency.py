"""Bounded dependency analysis over persisted graph edges."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType

COMPONENT_DEPENDENCY_EDGES = frozenset({GraphEdgeType.COMPONENT_DEPENDS_ON_COMPONENT})


@dataclass(frozen=True, slots=True)
class DependencyChain:
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    depth: int


@dataclass(frozen=True, slots=True)
class DependencyCycle:
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DependencyHotspot:
    node_id: str
    display_name: str
    fan_in: int
    fan_out: int
    kind: str


@dataclass(frozen=True, slots=True)
class DependencyDepthSummary:
    maximum_depth: int
    average_depth: float
    chains_examined: int


@dataclass(frozen=True, slots=True)
class OrphanComponent:
    node_id: str
    display_name: str
    canonical_id: str


@dataclass(frozen=True, slots=True)
class DependencyAnalysis:
    direct_dependencies: tuple[str, ...]
    transitive_dependencies: tuple[str, ...]
    upstream_dependencies: tuple[str, ...]
    downstream_dependencies: tuple[str, ...]
    cycles: tuple[DependencyCycle, ...]
    hotspots: tuple[DependencyHotspot, ...]
    orphans: tuple[OrphanComponent, ...]
    depth_summary: DependencyDepthSummary
    chains: tuple[DependencyChain, ...]


def _component_adjacency(
    nodes: tuple[GraphNode, ...],
    edges: tuple[GraphEdge, ...],
) -> tuple[dict[str, list[tuple[str, str]]], dict[str, list[tuple[str, str]]]]:
    """Return (out, in) adjacency for component dependency edges: neighbor_id, edge_id."""

    component_ids = {
        item.node_id.value for item in nodes if item.node_type is GraphNodeType.COMPONENT
    }
    outgoing: dict[str, list[tuple[str, str]]] = defaultdict(list)
    incoming: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for edge in edges:
        if edge.edge_type not in COMPONENT_DEPENDENCY_EDGES:
            continue
        src = edge.source_node_id.value
        tgt = edge.target_node_id.value
        if src not in component_ids or tgt not in component_ids:
            continue
        outgoing[src].append((tgt, edge.edge_id.value))
        incoming[tgt].append((src, edge.edge_id.value))
    return outgoing, incoming


def walk_dependencies(
    start_id: str,
    adjacency: dict[str, list[tuple[str, str]]],
    *,
    max_depth: int,
    max_nodes: int,
) -> tuple[tuple[str, ...], tuple[DependencyChain, ...], int]:
    visited: set[str] = set()
    chains: list[DependencyChain] = []
    queue: deque[tuple[str, int, tuple[str, ...], tuple[str, ...]]] = deque(
        [(start_id, 0, (start_id,), ())]
    )
    max_seen_depth = 0
    while queue and len(visited) < max_nodes:
        current, depth, path, edge_path = queue.popleft()
        if depth >= max_depth:
            continue
        for neighbor, edge_id in adjacency.get(current, []):
            if neighbor in path:
                continue
            next_path = (*path, neighbor)
            next_edges = (*edge_path, edge_id)
            next_depth = depth + 1
            max_seen_depth = max(max_seen_depth, next_depth)
            if neighbor not in visited and neighbor != start_id:
                visited.add(neighbor)
                chains.append(
                    DependencyChain(
                        node_ids=next_path,
                        edge_ids=next_edges,
                        depth=next_depth,
                    )
                )
            queue.append((neighbor, next_depth, next_path, next_edges))
            if len(visited) >= max_nodes:
                break
    return tuple(sorted(visited)), tuple(chains), max_seen_depth


def detect_cycles(
    nodes: tuple[GraphNode, ...],
    edges: tuple[GraphEdge, ...],
    *,
    max_depth: int,
    max_cycles: int,
) -> tuple[DependencyCycle, ...]:
    outgoing, _incoming = _component_adjacency(nodes, edges)
    cycles: list[DependencyCycle] = []
    seen_signatures: set[tuple[str, ...]] = set()

    for start in sorted(outgoing.keys()):
        stack: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = [(start, (start,), ())]
        while stack and len(cycles) < max_cycles:
            current, path, edge_path = stack.pop()
            if len(path) - 1 >= max_depth:
                continue
            for neighbor, edge_id in outgoing.get(current, []):
                if neighbor == start and len(path) > 1:
                    cycle_nodes = (*path, neighbor)
                    rotated = _normalize_cycle(cycle_nodes[:-1])
                    if rotated in seen_signatures:
                        continue
                    seen_signatures.add(rotated)
                    cycles.append(
                        DependencyCycle(
                            node_ids=(*rotated, rotated[0]),
                            edge_ids=(*edge_path, edge_id),
                        )
                    )
                    if len(cycles) >= max_cycles:
                        break
                    continue
                if neighbor in path:
                    continue
                stack.append((neighbor, (*path, neighbor), (*edge_path, edge_id)))
    return tuple(cycles)


def _normalize_cycle(nodes: tuple[str, ...]) -> tuple[str, ...]:
    if not nodes:
        return ()
    start = min(range(len(nodes)), key=lambda index: nodes[index])
    return tuple(nodes[start:] + nodes[:start])


def analyze_dependencies(
    nodes: tuple[GraphNode, ...],
    edges: tuple[GraphEdge, ...],
    *,
    subject_node_id: str | None = None,
    max_depth: int,
    max_nodes: int,
    max_paths: int,
) -> DependencyAnalysis:
    outgoing, incoming = _component_adjacency(nodes, edges)
    components = {
        item.node_id.value: item
        for item in nodes
        if item.node_type is GraphNodeType.COMPONENT
    }

    start = subject_node_id if subject_node_id in components else None
    if start is None and components:
        start = sorted(components.keys())[0]

    direct: tuple[str, ...] = ()
    transitive: tuple[str, ...] = ()
    upstream: tuple[str, ...] = ()
    downstream: tuple[str, ...] = ()
    chains: tuple[DependencyChain, ...] = ()
    max_depth_seen = 0
    if start is not None:
        direct = tuple(sorted({item[0] for item in outgoing.get(start, [])}))
        downstream, down_chains, down_depth = walk_dependencies(
            start,
            outgoing,
            max_depth=max_depth,
            max_nodes=max_nodes,
        )
        upstream, up_chains, up_depth = walk_dependencies(
            start,
            incoming,
            max_depth=max_depth,
            max_nodes=max_nodes,
        )
        transitive = tuple(sorted(set(downstream) | set(upstream)))
        chains = tuple(list(down_chains)[:max_paths] + list(up_chains)[:max_paths])
        max_depth_seen = max(down_depth, up_depth)

    fan_in = {node_id: len(incoming.get(node_id, [])) for node_id in components}
    fan_out = {node_id: len(outgoing.get(node_id, [])) for node_id in components}
    hotspots: list[DependencyHotspot] = []
    for node_id, component in components.items():
        fi = fan_in.get(node_id, 0)
        fo = fan_out.get(node_id, 0)
        if fi >= 2 or fo >= 2:
            kind = "fan_in" if fi >= fo else "fan_out"
            hotspots.append(
                DependencyHotspot(
                    node_id=node_id,
                    display_name=component.display_name,
                    fan_in=fi,
                    fan_out=fo,
                    kind=kind,
                )
            )
    hotspots.sort(key=lambda item: (-(item.fan_in + item.fan_out), item.node_id))

    orphans = tuple(
        OrphanComponent(
            node_id=node_id,
            display_name=component.display_name,
            canonical_id=component.canonical_id,
        )
        for node_id, component in sorted(components.items())
        if fan_in.get(node_id, 0) == 0 and fan_out.get(node_id, 0) == 0
    )

    cycles = detect_cycles(nodes, edges, max_depth=max_depth, max_cycles=max_paths)
    average = (
        sum(chain.depth for chain in chains) / len(chains) if chains else 0.0
    )
    return DependencyAnalysis(
        direct_dependencies=direct,
        transitive_dependencies=transitive,
        upstream_dependencies=upstream,
        downstream_dependencies=downstream,
        cycles=cycles,
        hotspots=tuple(hotspots[:50]),
        orphans=orphans,
        depth_summary=DependencyDepthSummary(
            maximum_depth=max_depth_seen,
            average_depth=round(average, 2),
            chains_examined=len(chains),
        ),
        chains=chains[:max_paths],
    )
