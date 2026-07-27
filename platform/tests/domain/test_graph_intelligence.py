"""Domain tests for graph intelligence analysis."""

from __future__ import annotations

import pytest

from codestrata_platform.domain.knowledge_graph.analysis.context import (
    HARD_MAX_DEPTH,
    GraphQueryLimits,
    ImpactSeverity,
)
from codestrata_platform.domain.knowledge_graph.analysis.coverage import (
    CoverageRatio,
    analyze_coverage,
)
from codestrata_platform.domain.knowledge_graph.analysis.dependency import (
    analyze_dependencies,
    detect_cycles,
)
from codestrata_platform.domain.knowledge_graph.analysis.errors import GraphAnalysisLimitError
from codestrata_platform.domain.knowledge_graph.analysis.impact import (
    DefaultImpactScoringPolicy,
    severity_band,
)
from codestrata_platform.domain.knowledge_graph.analysis.recommendation import (
    analyze_recommendations,
)
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.identifiers import (
    GraphEdgeId,
    GraphNodeId,
)
from codestrata_platform.domain.knowledge_graph.node import GraphNode, GraphProperty
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType


def _node(
    node_id: str,
    node_type: GraphNodeType,
    *,
    severity: str | None = None,
    priority: str | None = None,
) -> GraphNode:
    props: dict[str, object] = {}
    if severity is not None:
        props["severity"] = severity
    if priority is not None:
        props["priority"] = priority
    return GraphNode(
        node_id=GraphNodeId(node_id),
        node_type=node_type,
        canonical_type=node_type.value,
        canonical_id=node_id,
        display_name=node_id,
        properties=GraphProperty(values=props),
    )


def _edge(
    edge_id: str,
    source: str,
    target: str,
    edge_type: GraphEdgeType,
) -> GraphEdge:
    return GraphEdge(
        edge_id=GraphEdgeId(edge_id),
        source_node_id=GraphNodeId(source),
        target_node_id=GraphNodeId(target),
        edge_type=edge_type,
    )


def test_severity_bands_and_score_bounds() -> None:
    assert severity_band(0) is ImpactSeverity.LOW
    assert severity_band(19) is ImpactSeverity.LOW
    assert severity_band(20) is ImpactSeverity.MEDIUM
    assert severity_band(50) is ImpactSeverity.HIGH
    assert severity_band(80) is ImpactSeverity.CRITICAL
    with pytest.raises(ValueError):
        severity_band(101)


def test_impact_scoring_factors_are_explicit() -> None:
    policy = DefaultImpactScoringPolicy()
    finding = _node("graph-node:f1", GraphNodeType.FINDING, severity="critical")
    subject = _node("graph-node:c1", GraphNodeType.COMPONENT)
    score = policy.score(
        subject=subject,
        related_findings=(finding,),
        related_edges=(),
        direct_dependents=2,
        transitive_dependents=4,
        max_depth=3,
        unresolved_recommendation_count=1,
    )
    assert 0 <= score.score <= 100
    assert score.contributing_factors
    assert score.policy_version
    assert any(item.code == "critical_findings" for item in score.contributing_factors)


def test_coverage_empty_denominator() -> None:
    ratio = CoverageRatio.from_counts(0, 0)
    assert ratio.percentage is None
    assert ratio.denominator == 0


def test_coverage_and_trace_gaps() -> None:
    finding = _node("graph-node:f1", GraphNodeType.FINDING, severity="critical")
    evidence = _node("graph-node:e1", GraphNodeType.EVIDENCE)
    nodes = (finding, evidence)
    edges = (
        _edge(
            "graph-edge:1",
            "graph-node:f1",
            "graph-edge:e1",
            GraphEdgeType.FINDING_SUPPORTED_BY_EVIDENCE,
        ),
    )
    # Fix edge target - use evidence node id
    edges = (
        _edge(
            "graph-edge:1",
            "graph-node:f1",
            "graph-node:e1",
            GraphEdgeType.FINDING_SUPPORTED_BY_EVIDENCE,
        ),
    )
    coverage = analyze_coverage(nodes, edges)
    assert coverage.findings.with_evidence.percentage == 100.0
    assert coverage.findings.high_critical_with_recommendations.percentage == 0.0


def test_dependency_cycle_detection() -> None:
    a = _node("graph-node:a", GraphNodeType.COMPONENT)
    b = _node("graph-node:b", GraphNodeType.COMPONENT)
    nodes = (a, b)
    edges = (
        _edge(
            "graph-edge:ab",
            "graph-node:a",
            "graph-node:b",
            GraphEdgeType.COMPONENT_DEPENDS_ON_COMPONENT,
        ),
        _edge(
            "graph-edge:ba",
            "graph-node:b",
            "graph-node:a",
            GraphEdgeType.COMPONENT_DEPENDS_ON_COMPONENT,
        ),
    )
    cycles = detect_cycles(nodes, edges, max_depth=5, max_cycles=10)
    assert cycles
    analysis = analyze_dependencies(
        nodes,
        edges,
        subject_node_id="graph-node:a",
        max_depth=5,
        max_nodes=50,
        max_paths=10,
    )
    assert analysis.cycles


def test_recommendation_ordering_and_cycle() -> None:
    r1 = _node("graph-node:r1", GraphNodeType.RECOMMENDATION, priority="p1")
    r2 = _node("graph-node:r2", GraphNodeType.RECOMMENDATION, priority="p2")
    nodes = (r1, r2)
    edges = (
        _edge(
            "graph-edge:r12",
            "graph-node:r1",
            "graph-node:r2",
            GraphEdgeType.RECOMMENDATION_DEPENDS_ON_RECOMMENDATION,
        ),
        _edge(
            "graph-edge:r21",
            "graph-node:r2",
            "graph-node:r1",
            GraphEdgeType.RECOMMENDATION_DEPENDS_ON_RECOMMENDATION,
        ),
    )
    analysis = analyze_recommendations(nodes, edges)
    assert analysis.cycles
    assert analysis.execution_order == ()


def test_query_limits_hard_bounds() -> None:
    with pytest.raises(GraphAnalysisLimitError):
        GraphQueryLimits(maximum_depth=HARD_MAX_DEPTH + 1)
