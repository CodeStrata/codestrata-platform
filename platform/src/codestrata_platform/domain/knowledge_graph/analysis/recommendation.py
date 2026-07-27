"""Recommendation dependency ordering over persisted graph edges."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from codestrata_platform.domain.knowledge_graph.analysis.impact import finding_severity
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType


@dataclass(frozen=True, slots=True)
class RecommendationConflict:
    left_node_id: str
    right_node_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class RecommendationExecutionStep:
    node_id: str
    display_name: str
    priority: str
    order: int


@dataclass(frozen=True, slots=True)
class RecommendationPriorityView:
    node_id: str
    display_name: str
    priority: str
    related_finding_severity: str
    impact_score: int
    findings_resolved: int


@dataclass(frozen=True, slots=True)
class RecommendationDependencyView:
    node_id: str
    depends_on: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RecommendationCoverage:
    total: int
    linked_to_findings: int
    with_dependencies: int


@dataclass(frozen=True, slots=True)
class RecommendationAnalysis:
    coverage: RecommendationCoverage
    priorities: tuple[RecommendationPriorityView, ...]
    dependencies: tuple[RecommendationDependencyView, ...]
    execution_order: tuple[RecommendationExecutionStep, ...]
    cycles: tuple[tuple[str, ...], ...]
    conflicts: tuple[RecommendationConflict, ...]


def analyze_recommendations(
    nodes: tuple[GraphNode, ...],
    edges: tuple[GraphEdge, ...],
) -> RecommendationAnalysis:
    recommendations = [
        item for item in nodes if item.node_type is GraphNodeType.RECOMMENDATION
    ]
    findings = {
        item.node_id.value: item
        for item in nodes
        if item.node_type is GraphNodeType.FINDING
    }

    resolves: dict[str, list[str]] = defaultdict(list)
    depends: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        if edge.edge_type is GraphEdgeType.RECOMMENDATION_RESOLVES_FINDING:
            resolves[edge.source_node_id.value].append(edge.target_node_id.value)
        if edge.edge_type is GraphEdgeType.RECOMMENDATION_DEPENDS_ON_RECOMMENDATION:
            depends[edge.source_node_id.value].append(edge.target_node_id.value)

    linked = sum(1 for item in recommendations if resolves.get(item.node_id.value))
    with_deps = sum(1 for item in recommendations if depends.get(item.node_id.value))

    priorities: list[RecommendationPriorityView] = []
    for item in recommendations:
        related = [findings[fid] for fid in resolves.get(item.node_id.value, []) if fid in findings]
        severities = [finding_severity(finding) for finding in related]
        top = "unknown"
        for candidate in ("critical", "high", "medium", "low", "info"):
            if candidate in severities:
                top = candidate
                break
        priority = str(item.properties.values.get("priority", "p3"))
        impact = {"critical": 80, "high": 60, "medium": 35, "low": 15, "info": 5}.get(top, 10)
        priorities.append(
            RecommendationPriorityView(
                node_id=item.node_id.value,
                display_name=item.display_name,
                priority=priority,
                related_finding_severity=top,
                impact_score=impact,
                findings_resolved=len(related),
            )
        )
    priorities.sort(
        key=lambda item: (
            item.priority,
            -item.impact_score,
            -item.findings_resolved,
            item.node_id,
        )
    )

    dependency_views = tuple(
        RecommendationDependencyView(
            node_id=item.node_id.value,
            depends_on=tuple(sorted(depends.get(item.node_id.value, []))),
        )
        for item in recommendations
    )

    order, cycles = _topological_order(
        [item.node_id.value for item in recommendations],
        depends,
    )
    node_names = {item.node_id.value: item.display_name for item in recommendations}
    node_priority = {
        item.node_id.value: str(item.properties.values.get("priority", "p3"))
        for item in recommendations
    }
    execution = tuple(
        RecommendationExecutionStep(
            node_id=node_id,
            display_name=node_names.get(node_id, node_id),
            priority=node_priority.get(node_id, "p3"),
            order=index,
        )
        for index, node_id in enumerate(order, start=1)
    )

    conflicts: list[RecommendationConflict] = []
    for node_id, deps in depends.items():
        meta = next((item for item in recommendations if item.node_id.value == node_id), None)
        if meta is None:
            continue
        incompatible = meta.properties.values.get("incompatible_with")
        if isinstance(incompatible, list):
            known = {item.node_id.value for item in recommendations}
            for other in incompatible:
                if isinstance(other, str) and other in known:
                    conflicts.append(
                        RecommendationConflict(
                            left_node_id=node_id,
                            right_node_id=other,
                            reason="canonical_incompatible_with",
                        )
                    )
        for dep in deps:
            if node_id in depends.get(dep, []):
                conflicts.append(
                    RecommendationConflict(
                        left_node_id=node_id,
                        right_node_id=dep,
                        reason="mutual_dependency",
                    )
                )

    return RecommendationAnalysis(
        coverage=RecommendationCoverage(
            total=len(recommendations),
            linked_to_findings=linked,
            with_dependencies=with_deps,
        ),
        priorities=tuple(priorities),
        dependencies=dependency_views,
        execution_order=execution,
        cycles=tuple(cycles),
        conflicts=tuple(conflicts),
    )


def _topological_order(
    node_ids: list[str],
    depends: dict[str, list[str]],
) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    """Order recommendations so dependencies come first. Report cycles separately."""

    incoming: dict[str, int] = {node_id: 0 for node_id in node_ids}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for node_id in node_ids:
        for dep in depends.get(node_id, []):
            if dep not in incoming:
                continue
            # node depends on dep => edge dep -> node
            outgoing[dep].append(node_id)
            incoming[node_id] += 1

    queue = deque(sorted(node_id for node_id, count in incoming.items() if count == 0))
    ordered: list[str] = []
    while queue:
        current = queue.popleft()
        ordered.append(current)
        for nxt in sorted(outgoing.get(current, [])):
            incoming[nxt] -= 1
            if incoming[nxt] == 0:
                queue.append(nxt)

    remaining = [node_id for node_id, count in incoming.items() if count > 0]
    cycles: list[tuple[str, ...]] = []
    if remaining:
        cycles.append(tuple(sorted(remaining)))
    return tuple(ordered), tuple(cycles)
