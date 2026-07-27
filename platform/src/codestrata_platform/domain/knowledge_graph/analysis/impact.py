"""Deterministic impact scoring and impact analysis value objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from codestrata_platform.domain.knowledge_graph.analysis.context import ImpactSeverity
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType

IMPACT_POLICY_VERSION = "1.0.0"

_SEVERITY_POINTS = {
    "critical": 40,
    "high": 25,
    "medium": 10,
    "low": 4,
    "info": 1,
    "unknown": 0,
}


def severity_band(score: int) -> ImpactSeverity:
    if score < 0 or score > 100:
        raise ValueError("score_out_of_bounds")
    if score <= 19:
        return ImpactSeverity.LOW
    if score <= 49:
        return ImpactSeverity.MEDIUM
    if score <= 79:
        return ImpactSeverity.HIGH
    return ImpactSeverity.CRITICAL


def finding_severity(node: GraphNode) -> str:
    raw = node.properties.values.get("severity")
    if isinstance(raw, str):
        return raw.strip().lower()
    return "unknown"


@dataclass(frozen=True, slots=True)
class ImpactFactor:
    code: str
    description: str
    points: int
    source_node_ids: tuple[str, ...] = ()
    source_edge_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ImpactScore:
    score: int
    severity: ImpactSeverity
    contributing_factors: tuple[ImpactFactor, ...]
    source_node_ids: tuple[str, ...]
    source_edge_ids: tuple[str, ...]
    policy_version: str


@dataclass(frozen=True, slots=True)
class ImpactedEngineeringObject:
    node_id: str
    node_type: GraphNodeType
    canonical_type: str
    canonical_id: str
    display_name: str
    depth: int


@dataclass(frozen=True, slots=True)
class ChangeImpactPath:
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ComponentImpactAnalysis:
    subject_node_id: str
    impacted_objects: tuple[ImpactedEngineeringObject, ...]
    paths: tuple[ChangeImpactPath, ...]
    score: ImpactScore


@dataclass(frozen=True, slots=True)
class TechnologyImpactAnalysis:
    subject_node_id: str
    impacted_objects: tuple[ImpactedEngineeringObject, ...]
    paths: tuple[ChangeImpactPath, ...]
    score: ImpactScore


@dataclass(frozen=True, slots=True)
class FindingImpactAnalysis:
    subject_node_id: str
    impacted_objects: tuple[ImpactedEngineeringObject, ...]
    paths: tuple[ChangeImpactPath, ...]
    score: ImpactScore


@dataclass(frozen=True, slots=True)
class RecommendationImpactAnalysis:
    subject_node_id: str
    impacted_objects: tuple[ImpactedEngineeringObject, ...]
    paths: tuple[ChangeImpactPath, ...]
    score: ImpactScore


class ImpactScoringPolicy(Protocol):
    @property
    def version(self) -> str: ...

    def score(
        self,
        *,
        subject: GraphNode,
        related_findings: tuple[GraphNode, ...],
        related_edges: tuple[GraphEdge, ...],
        direct_dependents: int,
        transitive_dependents: int,
        max_depth: int,
        unresolved_recommendation_count: int,
        production_scoped_findings: int = 0,
    ) -> ImpactScore: ...


@dataclass(frozen=True, slots=True)
class DefaultImpactScoringPolicy:
    """Explicit deterministic impact scoring (0–100)."""

    version: str = IMPACT_POLICY_VERSION

    def score(
        self,
        *,
        subject: GraphNode,
        related_findings: tuple[GraphNode, ...],
        related_edges: tuple[GraphEdge, ...],
        direct_dependents: int,
        transitive_dependents: int,
        max_depth: int,
        unresolved_recommendation_count: int,
        production_scoped_findings: int = 0,
    ) -> ImpactScore:
        factors: list[ImpactFactor] = []
        points = 0
        finding_ids = tuple(item.node_id.value for item in related_findings)
        edge_ids = tuple(item.edge_id.value for item in related_edges)

        critical = [item for item in related_findings if finding_severity(item) == "critical"]
        high = [item for item in related_findings if finding_severity(item) == "high"]
        if critical:
            add = min(40, 20 + 5 * (len(critical) - 1))
            factors.append(
                ImpactFactor(
                    code="critical_findings",
                    description=f"{len(critical)} critical finding(s) connected",
                    points=add,
                    source_node_ids=tuple(item.node_id.value for item in critical),
                )
            )
            points += add
        if high:
            add = min(25, 15 + 5 * (len(high) - 1))
            factors.append(
                ImpactFactor(
                    code="high_findings",
                    description=f"{len(high)} high finding(s) connected",
                    points=add,
                    source_node_ids=tuple(item.node_id.value for item in high),
                )
            )
            points += add

        other = [
            item
            for item in related_findings
            if finding_severity(item) not in {"critical", "high"}
        ]
        if other:
            add = min(15, sum(_SEVERITY_POINTS.get(finding_severity(item), 0) for item in other))
            factors.append(
                ImpactFactor(
                    code="other_findings",
                    description=f"{len(other)} additional finding(s) connected",
                    points=add,
                    source_node_ids=tuple(item.node_id.value for item in other),
                )
            )
            points += add

        if production_scoped_findings > 0:
            add = min(15, 5 * production_scoped_findings)
            factors.append(
                ImpactFactor(
                    code="production_scope",
                    description=f"{production_scoped_findings} production-scoped finding(s)",
                    points=add,
                    source_node_ids=finding_ids,
                )
            )
            points += add

        if direct_dependents > 0:
            add = min(15, direct_dependents * 3)
            factors.append(
                ImpactFactor(
                    code="direct_dependents",
                    description=f"{direct_dependents} direct dependent(s)",
                    points=add,
                    source_node_ids=(subject.node_id.value,),
                    source_edge_ids=edge_ids,
                )
            )
            points += add

        if transitive_dependents > direct_dependents:
            add = min(10, (transitive_dependents - direct_dependents))
            factors.append(
                ImpactFactor(
                    code="transitive_dependents",
                    description=f"{transitive_dependents} transitive dependent(s)",
                    points=add,
                    source_node_ids=(subject.node_id.value,),
                )
            )
            points += add

        if max_depth > 0:
            add = min(10, max_depth * 2)
            factors.append(
                ImpactFactor(
                    code="dependency_depth",
                    description=f"maximum dependency depth {max_depth}",
                    points=add,
                    source_node_ids=(subject.node_id.value,),
                )
            )
            points += add

        if unresolved_recommendation_count > 0:
            add = min(15, unresolved_recommendation_count * 5)
            factors.append(
                ImpactFactor(
                    code="unresolved_recommendations",
                    description=(
                        f"{unresolved_recommendation_count} finding(s) without recommendation"
                    ),
                    points=add,
                    source_node_ids=finding_ids,
                )
            )
            points += add

        bounded = max(0, min(100, points))
        return ImpactScore(
            score=bounded,
            severity=severity_band(bounded),
            contributing_factors=tuple(factors),
            source_node_ids=tuple(sorted({subject.node_id.value, *finding_ids})),
            source_edge_ids=tuple(sorted(set(edge_ids))),
            policy_version=self.version,
        )


def collect_connected_by_types(
    *,
    subject_id: str,
    nodes: dict[str, GraphNode],
    adjacency_out: dict[str, list[tuple[str, GraphEdge]]],
    adjacency_in: dict[str, list[tuple[str, GraphEdge]]],
    node_types: frozenset[GraphNodeType],
    max_depth: int,
    max_nodes: int,
) -> tuple[tuple[ImpactedEngineeringObject, ...], tuple[GraphEdge, ...]]:
    """BFS over both directions collecting nodes of requested types."""

    seen: set[str] = {subject_id}
    queue: list[tuple[str, int]] = [(subject_id, 0)]
    impacted: list[ImpactedEngineeringObject] = []
    edges: list[GraphEdge] = []
    while queue and len(impacted) < max_nodes:
        current, depth = queue.pop(0)
        if depth >= max_depth:
            continue
        for neighbor_id, edge in adjacency_out.get(current, []) + adjacency_in.get(current, []):
            if neighbor_id in seen:
                continue
            seen.add(neighbor_id)
            neighbor = nodes.get(neighbor_id)
            if neighbor is None:
                continue
            edges.append(edge)
            if neighbor.node_type in node_types:
                impacted.append(
                    ImpactedEngineeringObject(
                        node_id=neighbor.node_id.value,
                        node_type=neighbor.node_type,
                        canonical_type=neighbor.canonical_type,
                        canonical_id=neighbor.canonical_id,
                        display_name=neighbor.display_name,
                        depth=depth + 1,
                    )
                )
            queue.append((neighbor_id, depth + 1))
            if len(impacted) >= max_nodes:
                break
    return tuple(impacted), tuple(edges)


DEPENDENCY_EDGE_TYPES = frozenset(
    {
        GraphEdgeType.COMPONENT_DEPENDS_ON_COMPONENT,
        GraphEdgeType.COMPONENT_USES_TECHNOLOGY,
        GraphEdgeType.REPOSITORY_HAS_COMPONENT,
        GraphEdgeType.REPOSITORY_USES_TECHNOLOGY,
        GraphEdgeType.COMPONENT_HAS_FINDING,
        GraphEdgeType.REPOSITORY_HAS_FINDING,
        GraphEdgeType.FINDING_SUPPORTED_BY_EVIDENCE,
        GraphEdgeType.RECOMMENDATION_RESOLVES_FINDING,
        GraphEdgeType.RECOMMENDATION_TARGETS_COMPONENT,
        GraphEdgeType.FINDING_ASSOCIATED_WITH_RISK,
        GraphEdgeType.FINDING_CLASSIFIED_AS_CATEGORY,
    }
)
