"""Traceability analysis over persisted graph relationships."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from codestrata_platform.domain.knowledge_graph.analysis.impact import finding_severity
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType


class TraceabilityGapType(StrEnum):
    FINDING_WITHOUT_EVIDENCE = "finding_without_evidence"
    HIGH_CRITICAL_WITHOUT_RECOMMENDATION = "high_critical_without_recommendation"
    RECOMMENDATION_WITHOUT_FINDING = "recommendation_without_finding"
    FINDING_WITHOUT_COMPONENT = "finding_without_component"
    DANGLING_CANONICAL_REFERENCE = "dangling_canonical_reference"
    METRIC_WITHOUT_REPOSITORY = "metric_without_repository"


@dataclass(frozen=True, slots=True)
class TraceabilityGap:
    gap_type: TraceabilityGapType
    node_id: str
    message: str


@dataclass(frozen=True, slots=True)
class TraceabilityCoverage:
    linked_count: int
    total_count: int


@dataclass(frozen=True, slots=True)
class FindingTraceability:
    finding_node_id: str
    repository_node_ids: tuple[str, ...]
    component_node_ids: tuple[str, ...]
    technology_node_ids: tuple[str, ...]
    category_node_ids: tuple[str, ...]
    risk_node_ids: tuple[str, ...]
    evidence_node_ids: tuple[str, ...]
    recommendation_node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    gaps: tuple[TraceabilityGap, ...]


@dataclass(frozen=True, slots=True)
class RecommendationTraceability:
    recommendation_node_id: str
    finding_node_ids: tuple[str, ...]
    component_node_ids: tuple[str, ...]
    evidence_node_ids: tuple[str, ...]
    dependency_node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    gaps: tuple[TraceabilityGap, ...]


@dataclass(frozen=True, slots=True)
class EvidenceTraceability:
    evidence_node_id: str
    finding_node_ids: tuple[str, ...]
    component_node_ids: tuple[str, ...]
    technology_node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    gaps: tuple[TraceabilityGap, ...]


def _neighbors(
    node_id: str,
    edges: tuple[GraphEdge, ...],
    *,
    edge_types: frozenset[GraphEdgeType],
    outgoing: bool = True,
    incoming: bool = True,
) -> tuple[tuple[str, str], ...]:
    results: list[tuple[str, str]] = []
    for edge in edges:
        if edge.edge_type not in edge_types:
            continue
        if outgoing and edge.source_node_id.value == node_id:
            results.append((edge.target_node_id.value, edge.edge_id.value))
        if incoming and edge.target_node_id.value == node_id:
            results.append((edge.source_node_id.value, edge.edge_id.value))
    return tuple(results)


def trace_finding(
    finding: GraphNode,
    nodes: dict[str, GraphNode],
    edges: tuple[GraphEdge, ...],
) -> FindingTraceability:
    edge_ids: list[str] = []
    repos = _neighbors(
        finding.node_id.value,
        edges,
        edge_types=frozenset({GraphEdgeType.REPOSITORY_HAS_FINDING}),
        outgoing=False,
        incoming=True,
    )
    components = _neighbors(
        finding.node_id.value,
        edges,
        edge_types=frozenset({GraphEdgeType.COMPONENT_HAS_FINDING}),
        outgoing=False,
        incoming=True,
    )
    categories = _neighbors(
        finding.node_id.value,
        edges,
        edge_types=frozenset({GraphEdgeType.FINDING_CLASSIFIED_AS_CATEGORY}),
    )
    risks = _neighbors(
        finding.node_id.value,
        edges,
        edge_types=frozenset({GraphEdgeType.FINDING_ASSOCIATED_WITH_RISK}),
    )
    evidence = _neighbors(
        finding.node_id.value,
        edges,
        edge_types=frozenset({GraphEdgeType.FINDING_SUPPORTED_BY_EVIDENCE}),
    )
    recommendations = _neighbors(
        finding.node_id.value,
        edges,
        edge_types=frozenset({GraphEdgeType.RECOMMENDATION_RESOLVES_FINDING}),
        outgoing=False,
        incoming=True,
    )
    for group in (repos, components, categories, risks, evidence, recommendations):
        edge_ids.extend(item[1] for item in group)

    tech_ids: list[str] = []
    for component_id, _edge in components:
        techs = _neighbors(
            component_id,
            edges,
            edge_types=frozenset({GraphEdgeType.COMPONENT_USES_TECHNOLOGY}),
        )
        for tech_id, edge_id in techs:
            tech_ids.append(tech_id)
            edge_ids.append(edge_id)

    gaps: list[TraceabilityGap] = []
    if not evidence:
        gaps.append(
            TraceabilityGap(
                gap_type=TraceabilityGapType.FINDING_WITHOUT_EVIDENCE,
                node_id=finding.node_id.value,
                message="Finding has no supporting evidence edges",
            )
        )
    if finding_severity(finding) in {"high", "critical"} and not recommendations:
        gaps.append(
            TraceabilityGap(
                gap_type=TraceabilityGapType.HIGH_CRITICAL_WITHOUT_RECOMMENDATION,
                node_id=finding.node_id.value,
                message="High/critical finding has no linked recommendation",
            )
        )
    if not components:
        gaps.append(
            TraceabilityGap(
                gap_type=TraceabilityGapType.FINDING_WITHOUT_COMPONENT,
                node_id=finding.node_id.value,
                message="Finding is not linked to a component",
            )
        )

    return FindingTraceability(
        finding_node_id=finding.node_id.value,
        repository_node_ids=tuple(item[0] for item in repos),
        component_node_ids=tuple(item[0] for item in components),
        technology_node_ids=tuple(sorted(set(tech_ids))),
        category_node_ids=tuple(item[0] for item in categories),
        risk_node_ids=tuple(item[0] for item in risks),
        evidence_node_ids=tuple(item[0] for item in evidence),
        recommendation_node_ids=tuple(item[0] for item in recommendations),
        edge_ids=tuple(sorted(set(edge_ids))),
        gaps=tuple(gaps),
    )


def trace_recommendation(
    recommendation: GraphNode,
    nodes: dict[str, GraphNode],
    edges: tuple[GraphEdge, ...],
) -> RecommendationTraceability:
    edge_ids: list[str] = []
    findings = _neighbors(
        recommendation.node_id.value,
        edges,
        edge_types=frozenset({GraphEdgeType.RECOMMENDATION_RESOLVES_FINDING}),
    )
    components = _neighbors(
        recommendation.node_id.value,
        edges,
        edge_types=frozenset({GraphEdgeType.RECOMMENDATION_TARGETS_COMPONENT}),
    )
    dependencies = _neighbors(
        recommendation.node_id.value,
        edges,
        edge_types=frozenset({GraphEdgeType.RECOMMENDATION_DEPENDS_ON_RECOMMENDATION}),
    )
    evidence_ids: list[str] = []
    for finding_id, edge_id in findings:
        edge_ids.append(edge_id)
        for evidence_id, evidence_edge in _neighbors(
            finding_id,
            edges,
            edge_types=frozenset({GraphEdgeType.FINDING_SUPPORTED_BY_EVIDENCE}),
        ):
            evidence_ids.append(evidence_id)
            edge_ids.append(evidence_edge)
    for group in (components, dependencies):
        edge_ids.extend(item[1] for item in group)

    gaps: list[TraceabilityGap] = []
    if not findings:
        gaps.append(
            TraceabilityGap(
                gap_type=TraceabilityGapType.RECOMMENDATION_WITHOUT_FINDING,
                node_id=recommendation.node_id.value,
                message="Recommendation is not linked to a finding",
            )
        )

    return RecommendationTraceability(
        recommendation_node_id=recommendation.node_id.value,
        finding_node_ids=tuple(item[0] for item in findings),
        component_node_ids=tuple(item[0] for item in components),
        evidence_node_ids=tuple(sorted(set(evidence_ids))),
        dependency_node_ids=tuple(item[0] for item in dependencies),
        edge_ids=tuple(sorted(set(edge_ids))),
        gaps=tuple(gaps),
    )


def trace_evidence(
    evidence: GraphNode,
    nodes: dict[str, GraphNode],
    edges: tuple[GraphEdge, ...],
) -> EvidenceTraceability:
    edge_ids: list[str] = []
    findings = _neighbors(
        evidence.node_id.value,
        edges,
        edge_types=frozenset({GraphEdgeType.FINDING_SUPPORTED_BY_EVIDENCE}),
        outgoing=False,
        incoming=True,
    )
    component_ids: list[str] = []
    technology_ids: list[str] = []
    for finding_id, edge_id in findings:
        edge_ids.append(edge_id)
        for component_id, component_edge in _neighbors(
            finding_id,
            edges,
            edge_types=frozenset({GraphEdgeType.COMPONENT_HAS_FINDING}),
            outgoing=False,
            incoming=True,
        ):
            component_ids.append(component_id)
            edge_ids.append(component_edge)
            for tech_id, tech_edge in _neighbors(
                component_id,
                edges,
                edge_types=frozenset({GraphEdgeType.COMPONENT_USES_TECHNOLOGY}),
            ):
                technology_ids.append(tech_id)
                edge_ids.append(tech_edge)

    return EvidenceTraceability(
        evidence_node_id=evidence.node_id.value,
        finding_node_ids=tuple(item[0] for item in findings),
        component_node_ids=tuple(sorted(set(component_ids))),
        technology_node_ids=tuple(sorted(set(technology_ids))),
        edge_ids=tuple(sorted(set(edge_ids))),
        gaps=(),
    )


def detect_graph_traceability_gaps(
    nodes: tuple[GraphNode, ...],
    edges: tuple[GraphEdge, ...],
) -> tuple[TraceabilityGap, ...]:
    node_map = {item.node_id.value: item for item in nodes}
    gaps: list[TraceabilityGap] = []
    for finding in nodes:
        if finding.node_type is GraphNodeType.FINDING:
            gaps.extend(trace_finding(finding, node_map, edges).gaps)
    for recommendation in nodes:
        if recommendation.node_type is GraphNodeType.RECOMMENDATION:
            gaps.extend(trace_recommendation(recommendation, node_map, edges).gaps)

    repo_linked_metrics = {
        edge.source_node_id.value
        for edge in edges
        if edge.edge_type is GraphEdgeType.REPOSITORY_HAS_METRIC
    }
    for metric in nodes:
        if metric.node_type is GraphNodeType.METRIC and metric.node_id.value not in {
            edge.target_node_id.value
            for edge in edges
            if edge.edge_type is GraphEdgeType.REPOSITORY_HAS_METRIC
        }:
            gaps.append(
                TraceabilityGap(
                    gap_type=TraceabilityGapType.METRIC_WITHOUT_REPOSITORY,
                    node_id=metric.node_id.value,
                    message="Metric is not linked to a repository",
                )
            )
    _ = repo_linked_metrics
    return tuple(gaps)
