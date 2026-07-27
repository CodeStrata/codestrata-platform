"""Deterministic risk concentration analysis over persisted graphs."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from codestrata_platform.domain.knowledge_graph.analysis.impact import (
    DefaultImpactScoringPolicy,
    finding_severity,
)
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType


@dataclass(frozen=True, slots=True)
class RiskConcentration:
    key: str
    dimension: str
    finding_count: int
    critical_count: int
    high_count: int


@dataclass(frozen=True, slots=True)
class RiskHotspot:
    node_id: str
    node_type: str
    display_name: str
    score: int
    factors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RiskDistribution:
    by_severity: dict[str, int]
    by_category: dict[str, int]


@dataclass(frozen=True, slots=True)
class UnresolvedRisk:
    finding_node_id: str
    severity: str
    title: str


@dataclass(frozen=True, slots=True)
class GraphRiskSummary:
    distribution: RiskDistribution
    concentrations: tuple[RiskConcentration, ...]
    hotspots: tuple[RiskHotspot, ...]
    unresolved: tuple[UnresolvedRisk, ...]


def analyze_risk(
    nodes: tuple[GraphNode, ...],
    edges: tuple[GraphEdge, ...],
    *,
    fan_in: dict[str, int] | None = None,
) -> GraphRiskSummary:
    findings = [item for item in nodes if item.node_type is GraphNodeType.FINDING]
    recommendations_by_finding: set[str] = {
        edge.target_node_id.value
        for edge in edges
        if edge.edge_type is GraphEdgeType.RECOMMENDATION_RESOLVES_FINDING
    }
    evidence_by_finding: set[str] = {
        edge.source_node_id.value
        for edge in edges
        if edge.edge_type is GraphEdgeType.FINDING_SUPPORTED_BY_EVIDENCE
    }
    components_by_finding: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        if edge.edge_type is GraphEdgeType.COMPONENT_HAS_FINDING:
            components_by_finding[edge.target_node_id.value].append(edge.source_node_id.value)

    by_severity: dict[str, int] = defaultdict(int)
    by_category: dict[str, int] = defaultdict(int)
    for finding in findings:
        severity = finding_severity(finding)
        by_severity[severity] += 1
        category = str(finding.properties.values.get("category", "other"))
        by_category[category] += 1

    concentrations = [
        RiskConcentration(
            key=severity,
            dimension="severity",
            finding_count=count,
            critical_count=count if severity == "critical" else 0,
            high_count=count if severity == "high" else 0,
        )
        for severity, count in sorted(by_severity.items())
    ]

    unresolved = tuple(
        UnresolvedRisk(
            finding_node_id=item.node_id.value,
            severity=finding_severity(item),
            title=item.display_name,
        )
        for item in findings
        if finding_severity(item) in {"high", "critical"}
        and item.node_id.value not in recommendations_by_finding
    )

    policy = DefaultImpactScoringPolicy()
    hotspots: list[RiskHotspot] = []
    subjects = [
        item
        for item in nodes
        if item.node_type
        in {GraphNodeType.COMPONENT, GraphNodeType.TECHNOLOGY, GraphNodeType.FINDING}
    ]
    for subject in subjects:
        related = _related_findings(subject, findings, edges, components_by_finding)
        if not related and subject.node_type is not GraphNodeType.FINDING:
            continue
        if subject.node_type is GraphNodeType.FINDING:
            related = (subject,)
        score = policy.score(
            subject=subject,
            related_findings=related,
            related_edges=tuple(
                edge
                for edge in edges
                if edge.source_node_id == subject.node_id or edge.target_node_id == subject.node_id
            ),
            direct_dependents=(fan_in or {}).get(subject.node_id.value, 0),
            transitive_dependents=(fan_in or {}).get(subject.node_id.value, 0),
            max_depth=1,
            unresolved_recommendation_count=sum(
                1
                for item in related
                if item.node_id.value not in recommendations_by_finding
                and finding_severity(item) in {"high", "critical"}
            ),
            production_scoped_findings=sum(
                1
                for item in related
                if str(item.properties.values.get("production_scope", "")).lower()
                in {"true", "production", "prod"}
            ),
        )
        factors: list[str] = [item.code for item in score.contributing_factors]
        if (
            subject.node_id.value not in evidence_by_finding
            and subject.node_type is GraphNodeType.FINDING
        ):
            factors.append("evidence_gap")
        if score.score >= 50:
            hotspots.append(
                RiskHotspot(
                    node_id=subject.node_id.value,
                    node_type=subject.node_type.value,
                    display_name=subject.display_name,
                    score=score.score,
                    factors=tuple(factors),
                )
            )
    hotspots.sort(key=lambda item: (-item.score, item.node_id))

    return GraphRiskSummary(
        distribution=RiskDistribution(
            by_severity=dict(sorted(by_severity.items())),
            by_category=dict(sorted(by_category.items())),
        ),
        concentrations=tuple(concentrations),
        hotspots=tuple(hotspots[:50]),
        unresolved=unresolved,
    )


def _related_findings(
    subject: GraphNode,
    findings: list[GraphNode],
    edges: tuple[GraphEdge, ...],
    components_by_finding: dict[str, list[str]],
) -> tuple[GraphNode, ...]:
    if subject.node_type is GraphNodeType.FINDING:
        return (subject,)
    finding_map = {item.node_id.value: item for item in findings}
    related_ids: set[str] = set()
    for edge in edges:
        if subject.node_type is GraphNodeType.COMPONENT:
            if (
                edge.edge_type is GraphEdgeType.COMPONENT_HAS_FINDING
                and edge.source_node_id == subject.node_id
            ):
                related_ids.add(edge.target_node_id.value)
        if subject.node_type is GraphNodeType.TECHNOLOGY:
            if (
                edge.edge_type is GraphEdgeType.COMPONENT_USES_TECHNOLOGY
                and edge.target_node_id == subject.node_id
            ):
                for finding_id, component_ids in components_by_finding.items():
                    if edge.source_node_id.value in component_ids:
                        related_ids.add(finding_id)
            if (
                edge.edge_type is GraphEdgeType.REPOSITORY_USES_TECHNOLOGY
                and edge.target_node_id == subject.node_id
            ):
                for finding in findings:
                    related_ids.add(finding.node_id.value)
    return tuple(finding_map[item] for item in sorted(related_ids) if item in finding_map)
