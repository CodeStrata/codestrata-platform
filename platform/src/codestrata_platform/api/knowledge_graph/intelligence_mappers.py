"""Map graph intelligence application models to API DTOs."""

from __future__ import annotations

from codestrata_platform.api.knowledge_graph.intelligence_dto import (
    CoverageMetricResponse,
    CoverageResponse,
    DependencyAnalysisResponse,
    DependencyCycleResponse,
    DependencyHotspotResponse,
    ImpactAnalysisResponse,
    ImpactFactorResponse,
    ImpactPathResponse,
    IntegrityIssueResponse,
    IntegrityResponse,
    RecommendationAnalysisResponse,
    RecommendationStepResponse,
    RepositoryOverviewResponse,
    RiskHotspotResponse,
    RiskSummaryResponse,
    TraceabilityGapResponse,
    TraceabilityResponse,
)
from codestrata_platform.application.knowledge_graph.intelligence.models import (
    CoverageSummary,
    DependencyAnalysisSummary,
    GraphIntegritySummary,
    ImpactAnalysisSummary,
    RecommendationAnalysisSummary,
    RepositoryEngineeringOverview,
    RiskSummary,
    TraceabilitySummary,
)


def impact_response(item: ImpactAnalysisSummary) -> ImpactAnalysisResponse:
    return ImpactAnalysisResponse(
        graph_id=item.graph_id,
        graph_version=item.graph_version,
        engineering_snapshot_id=item.engineering_snapshot_id,
        generated_at=item.generated_at,
        subject_node_id=item.subject_node_id,
        subject_node_type=item.subject_node_type,
        score=item.score,
        severity=item.severity.value,
        policy_version=item.policy_version,
        contributing_factors=[
            ImpactFactorResponse(
                code=factor.code,
                description=factor.description,
                points=factor.points,
                source_node_ids=list(factor.source_node_ids),
                source_edge_ids=list(factor.source_edge_ids),
            )
            for factor in item.contributing_factors
        ],
        impacted_node_ids=list(item.impacted_node_ids),
        source_node_ids=list(item.source_node_ids),
        source_edge_ids=list(item.source_edge_ids),
        paths=[
            ImpactPathResponse(node_ids=list(path.node_ids), edge_ids=list(path.edge_ids))
            for path in item.paths
        ],
        diagnostics=list(item.diagnostics),
    )


def traceability_response(item: TraceabilitySummary) -> TraceabilityResponse:
    return TraceabilityResponse(
        graph_id=item.graph_id,
        graph_version=item.graph_version,
        engineering_snapshot_id=item.engineering_snapshot_id,
        generated_at=item.generated_at,
        subject_node_id=item.subject_node_id,
        subject_node_type=item.subject_node_type,
        related={key: list(value) for key, value in item.related.items()},
        edge_ids=list(item.edge_ids),
        gaps=[
            TraceabilityGapResponse(
                gap_type=gap.gap_type,
                node_id=gap.node_id,
                message=gap.message,
            )
            for gap in item.gaps
        ],
    )


def _coverage_metric(item) -> CoverageMetricResponse:
    return CoverageMetricResponse(
        numerator=item.numerator,
        denominator=item.denominator,
        percentage=item.percentage,
    )


def coverage_response(item: CoverageSummary) -> CoverageResponse:
    return CoverageResponse(
        graph_id=item.graph_id,
        graph_version=item.graph_version,
        engineering_snapshot_id=item.engineering_snapshot_id,
        generated_at=item.generated_at,
        findings_with_evidence=_coverage_metric(item.findings_with_evidence),
        high_critical_with_recommendations=_coverage_metric(
            item.high_critical_with_recommendations
        ),
        findings_linked_to_components=_coverage_metric(item.findings_linked_to_components),
        technologies_linked_to_components=_coverage_metric(
            item.technologies_linked_to_components
        ),
        recommendations_linked_to_findings=_coverage_metric(
            item.recommendations_linked_to_findings
        ),
        objects_with_source_reference=_coverage_metric(item.objects_with_source_reference),
    )


def dependency_response(item: DependencyAnalysisSummary) -> DependencyAnalysisResponse:
    return DependencyAnalysisResponse(
        graph_id=item.graph_id,
        graph_version=item.graph_version,
        engineering_snapshot_id=item.engineering_snapshot_id,
        generated_at=item.generated_at,
        direct_dependencies=list(item.direct_dependencies),
        transitive_dependencies=list(item.transitive_dependencies),
        upstream_dependencies=list(item.upstream_dependencies),
        downstream_dependencies=list(item.downstream_dependencies),
        cycles=[
            DependencyCycleResponse(node_ids=list(cycle.node_ids), edge_ids=list(cycle.edge_ids))
            for cycle in item.cycles
        ],
        hotspots=[
            DependencyHotspotResponse(
                node_id=hotspot.node_id,
                display_name=hotspot.display_name,
                fan_in=hotspot.fan_in,
                fan_out=hotspot.fan_out,
                kind=hotspot.kind,
            )
            for hotspot in item.hotspots
        ],
        orphan_component_ids=list(item.orphan_component_ids),
        maximum_depth=item.maximum_depth,
    )


def risk_response(item: RiskSummary) -> RiskSummaryResponse:
    return RiskSummaryResponse(
        graph_id=item.graph_id,
        graph_version=item.graph_version,
        engineering_snapshot_id=item.engineering_snapshot_id,
        generated_at=item.generated_at,
        by_severity=dict(item.by_severity),
        by_category=dict(item.by_category),
        hotspots=[
            RiskHotspotResponse(
                node_id=hotspot.node_id,
                node_type=hotspot.node_type,
                display_name=hotspot.display_name,
                score=hotspot.score,
                factors=list(hotspot.factors),
            )
            for hotspot in item.hotspots
        ],
        unresolved_finding_ids=list(item.unresolved_finding_ids),
    )


def recommendation_response(
    item: RecommendationAnalysisSummary,
) -> RecommendationAnalysisResponse:
    return RecommendationAnalysisResponse(
        graph_id=item.graph_id,
        graph_version=item.graph_version,
        engineering_snapshot_id=item.engineering_snapshot_id,
        generated_at=item.generated_at,
        total=item.total,
        linked_to_findings=item.linked_to_findings,
        execution_order=[
            RecommendationStepResponse(
                node_id=step.node_id,
                display_name=step.display_name,
                priority=step.priority,
                order=step.order,
            )
            for step in item.execution_order
        ],
        cycles=[list(cycle) for cycle in item.cycles],
        conflict_count=item.conflict_count,
    )


def integrity_response(item: GraphIntegritySummary) -> IntegrityResponse:
    return IntegrityResponse(
        graph_id=item.graph_id,
        graph_version=item.graph_version,
        engineering_snapshot_id=item.engineering_snapshot_id,
        generated_at=item.generated_at,
        integrity_version=item.integrity_version,
        passed=item.passed,
        issue_count=item.issue_count,
        critical_issue_count=item.critical_issue_count,
        issues=[
            IntegrityIssueResponse(
                issue_type=issue.issue_type,
                severity=issue.severity,
                message=issue.message,
                node_ids=list(issue.node_ids),
                edge_ids=list(issue.edge_ids),
            )
            for issue in item.issues
        ],
    )


def overview_response(item: RepositoryEngineeringOverview) -> RepositoryOverviewResponse:
    return RepositoryOverviewResponse(
        graph_id=item.graph_id,
        graph_version=item.graph_version,
        engineering_snapshot_id=item.engineering_snapshot_id,
        generated_at=item.generated_at,
        repository_id=item.repository_id,
        technology_count=item.technology_count,
        component_count=item.component_count,
        finding_distribution=dict(item.finding_distribution),
        recommendation_count=item.recommendation_count,
        evidence_coverage=_coverage_metric(item.evidence_coverage),
        recommendation_coverage=_coverage_metric(item.recommendation_coverage),
        dependency_hotspots=[
            DependencyHotspotResponse(
                node_id=hotspot.node_id,
                display_name=hotspot.display_name,
                fan_in=hotspot.fan_in,
                fan_out=hotspot.fan_out,
                kind=hotspot.kind,
            )
            for hotspot in item.dependency_hotspots
        ],
        risk_hotspots=[
            RiskHotspotResponse(
                node_id=hotspot.node_id,
                node_type=hotspot.node_type,
                display_name=hotspot.display_name,
                score=hotspot.score,
                factors=list(hotspot.factors),
            )
            for hotspot in item.risk_hotspots
        ],
        highest_impact_components=list(item.highest_impact_components),
        highest_impact_technologies=list(item.highest_impact_technologies),
        integrity_passed=item.integrity_passed,
        policy_version=item.policy_version,
    )
