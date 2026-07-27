"""Coverage metrics over persisted graph nodes and edges."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.knowledge_graph.analysis.impact import finding_severity
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType


@dataclass(frozen=True, slots=True)
class CoverageRatio:
    numerator: int
    denominator: int
    percentage: float | None

    @classmethod
    def from_counts(cls, numerator: int, denominator: int) -> CoverageRatio:
        if denominator <= 0:
            return cls(numerator=0, denominator=0, percentage=None)
        bounded = max(0, min(numerator, denominator))
        return cls(
            numerator=bounded,
            denominator=denominator,
            percentage=round((bounded / denominator) * 100.0, 2),
        )


@dataclass(frozen=True, slots=True)
class FindingCoverageSummary:
    total: int
    with_evidence: CoverageRatio
    high_critical_with_recommendations: CoverageRatio
    linked_to_components: CoverageRatio


@dataclass(frozen=True, slots=True)
class RecommendationCoverageSummary:
    total: int
    linked_to_findings: CoverageRatio


@dataclass(frozen=True, slots=True)
class EvidenceCoverageSummary:
    total: int
    supporting_findings: CoverageRatio


@dataclass(frozen=True, slots=True)
class ComponentCoverageSummary:
    total: int
    with_findings: CoverageRatio
    with_technologies: CoverageRatio


@dataclass(frozen=True, slots=True)
class TechnologyCoverageSummary:
    total: int
    linked_to_components: CoverageRatio


@dataclass(frozen=True, slots=True)
class GraphCoverageAnalysis:
    findings: FindingCoverageSummary
    recommendations: RecommendationCoverageSummary
    evidence: EvidenceCoverageSummary
    components: ComponentCoverageSummary
    technologies: TechnologyCoverageSummary
    objects_with_source_reference: CoverageRatio


def analyze_coverage(
    nodes: tuple[GraphNode, ...],
    edges: tuple[GraphEdge, ...],
) -> GraphCoverageAnalysis:
    findings = [item for item in nodes if item.node_type is GraphNodeType.FINDING]
    recommendations = [
        item for item in nodes if item.node_type is GraphNodeType.RECOMMENDATION
    ]
    evidence = [item for item in nodes if item.node_type is GraphNodeType.EVIDENCE]
    components = [item for item in nodes if item.node_type is GraphNodeType.COMPONENT]
    technologies = [item for item in nodes if item.node_type is GraphNodeType.TECHNOLOGY]

    finding_ids = {item.node_id.value for item in findings}
    evidence_by_finding: set[str] = set()
    component_by_finding: set[str] = set()
    recommendation_by_finding: set[str] = set()
    finding_by_recommendation: set[str] = set()
    evidence_with_finding: set[str] = set()
    component_with_finding: set[str] = set()
    component_with_tech: set[str] = set()
    tech_with_component: set[str] = set()

    for edge in edges:
        src = edge.source_node_id.value
        tgt = edge.target_node_id.value
        if edge.edge_type is GraphEdgeType.FINDING_SUPPORTED_BY_EVIDENCE and src in finding_ids:
            evidence_by_finding.add(src)
            evidence_with_finding.add(tgt)
        if edge.edge_type is GraphEdgeType.COMPONENT_HAS_FINDING and tgt in finding_ids:
            component_by_finding.add(tgt)
            component_with_finding.add(src)
        if edge.edge_type is GraphEdgeType.RECOMMENDATION_RESOLVES_FINDING and tgt in finding_ids:
            recommendation_by_finding.add(tgt)
            finding_by_recommendation.add(src)
        if edge.edge_type is GraphEdgeType.COMPONENT_USES_TECHNOLOGY:
            component_with_tech.add(src)
            tech_with_component.add(tgt)

    high_critical = [
        item
        for item in findings
        if finding_severity(item) in {"high", "critical"}
    ]
    high_critical_covered = [
        item for item in high_critical if item.node_id.value in recommendation_by_finding
    ]

    with_source = sum(1 for item in nodes if item.source_reference is not None)

    return GraphCoverageAnalysis(
        findings=FindingCoverageSummary(
            total=len(findings),
            with_evidence=CoverageRatio.from_counts(len(evidence_by_finding), len(findings)),
            high_critical_with_recommendations=CoverageRatio.from_counts(
                len(high_critical_covered),
                len(high_critical),
            ),
            linked_to_components=CoverageRatio.from_counts(
                len(component_by_finding),
                len(findings),
            ),
        ),
        recommendations=RecommendationCoverageSummary(
            total=len(recommendations),
            linked_to_findings=CoverageRatio.from_counts(
                len(finding_by_recommendation),
                len(recommendations),
            ),
        ),
        evidence=EvidenceCoverageSummary(
            total=len(evidence),
            supporting_findings=CoverageRatio.from_counts(
                len(evidence_with_finding),
                len(evidence),
            ),
        ),
        components=ComponentCoverageSummary(
            total=len(components),
            with_findings=CoverageRatio.from_counts(
                len(component_with_finding),
                len(components),
            ),
            with_technologies=CoverageRatio.from_counts(
                len(component_with_tech),
                len(components),
            ),
        ),
        technologies=TechnologyCoverageSummary(
            total=len(technologies),
            linked_to_components=CoverageRatio.from_counts(
                len(tech_with_component),
                len(technologies),
            ),
        ),
        objects_with_source_reference=CoverageRatio.from_counts(with_source, len(nodes)),
    )
