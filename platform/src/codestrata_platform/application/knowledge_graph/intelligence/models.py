"""Application models for graph intelligence responses."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.knowledge_graph.analysis.context import ImpactSeverity
from codestrata_platform.domain.knowledge_graph.analysis.coverage import CoverageRatio
from codestrata_platform.domain.knowledge_graph.analysis.impact import ImpactFactor


@dataclass(frozen=True, slots=True)
class ImpactFactorModel:
    code: str
    description: str
    points: int
    source_node_ids: tuple[str, ...]
    source_edge_ids: tuple[str, ...]

    @classmethod
    def from_domain(cls, item: ImpactFactor) -> ImpactFactorModel:
        return cls(
            code=item.code,
            description=item.description,
            points=item.points,
            source_node_ids=item.source_node_ids,
            source_edge_ids=item.source_edge_ids,
        )


@dataclass(frozen=True, slots=True)
class ImpactPathSummary:
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ImpactAnalysisSummary:
    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    subject_node_id: str
    subject_node_type: str
    score: int
    severity: ImpactSeverity
    policy_version: str
    contributing_factors: tuple[ImpactFactorModel, ...]
    impacted_node_ids: tuple[str, ...]
    source_node_ids: tuple[str, ...]
    source_edge_ids: tuple[str, ...]
    paths: tuple[ImpactPathSummary, ...]
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TraceabilityGapSummary:
    gap_type: str
    node_id: str
    message: str


@dataclass(frozen=True, slots=True)
class TraceabilitySummary:
    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    subject_node_id: str
    subject_node_type: str
    related: dict[str, tuple[str, ...]]
    edge_ids: tuple[str, ...]
    gaps: tuple[TraceabilityGapSummary, ...]


@dataclass(frozen=True, slots=True)
class CoverageMetricModel:
    numerator: int
    denominator: int
    percentage: float | None

    @classmethod
    def from_ratio(cls, ratio: CoverageRatio) -> CoverageMetricModel:
        return cls(
            numerator=ratio.numerator,
            denominator=ratio.denominator,
            percentage=ratio.percentage,
        )


@dataclass(frozen=True, slots=True)
class CoverageSummary:
    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    findings_with_evidence: CoverageMetricModel
    high_critical_with_recommendations: CoverageMetricModel
    findings_linked_to_components: CoverageMetricModel
    technologies_linked_to_components: CoverageMetricModel
    recommendations_linked_to_findings: CoverageMetricModel
    objects_with_source_reference: CoverageMetricModel


@dataclass(frozen=True, slots=True)
class DependencyCycleSummary:
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DependencyHotspotSummary:
    node_id: str
    display_name: str
    fan_in: int
    fan_out: int
    kind: str


@dataclass(frozen=True, slots=True)
class DependencyAnalysisSummary:
    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    direct_dependencies: tuple[str, ...]
    transitive_dependencies: tuple[str, ...]
    upstream_dependencies: tuple[str, ...]
    downstream_dependencies: tuple[str, ...]
    cycles: tuple[DependencyCycleSummary, ...]
    hotspots: tuple[DependencyHotspotSummary, ...]
    orphan_component_ids: tuple[str, ...]
    maximum_depth: int


@dataclass(frozen=True, slots=True)
class RiskHotspotSummary:
    node_id: str
    node_type: str
    display_name: str
    score: int
    factors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RiskSummary:
    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    by_severity: dict[str, int]
    by_category: dict[str, int]
    hotspots: tuple[RiskHotspotSummary, ...]
    unresolved_finding_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RecommendationExecutionStepModel:
    node_id: str
    display_name: str
    priority: str
    order: int


@dataclass(frozen=True, slots=True)
class RecommendationAnalysisSummary:
    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    total: int
    linked_to_findings: int
    execution_order: tuple[RecommendationExecutionStepModel, ...]
    cycles: tuple[tuple[str, ...], ...]
    conflict_count: int


@dataclass(frozen=True, slots=True)
class GraphIntegrityIssueSummary:
    issue_type: str
    severity: str
    message: str
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GraphIntegritySummary:
    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    integrity_version: str
    passed: bool
    issue_count: int
    critical_issue_count: int
    issues: tuple[GraphIntegrityIssueSummary, ...]


@dataclass(frozen=True, slots=True)
class RepositoryEngineeringOverview:
    graph_id: str
    graph_version: int
    engineering_snapshot_id: str
    generated_at: datetime
    repository_id: str
    technology_count: int
    component_count: int
    finding_distribution: dict[str, int]
    recommendation_count: int
    evidence_coverage: CoverageMetricModel
    recommendation_coverage: CoverageMetricModel
    dependency_hotspots: tuple[DependencyHotspotSummary, ...]
    risk_hotspots: tuple[RiskHotspotSummary, ...]
    highest_impact_components: tuple[str, ...]
    highest_impact_technologies: tuple[str, ...]
    integrity_passed: bool
    policy_version: str
