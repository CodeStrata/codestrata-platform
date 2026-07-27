"""Graph intelligence application services."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from codestrata_platform.application.common.errors import NotFoundError
from codestrata_platform.application.knowledge_graph.intelligence.errors import GraphNotReadyError
from codestrata_platform.application.knowledge_graph.intelligence.models import (
    CoverageMetricModel,
    CoverageSummary,
    DependencyAnalysisSummary,
    DependencyCycleSummary,
    DependencyHotspotSummary,
    GraphIntegrityIssueSummary,
    GraphIntegritySummary,
    ImpactAnalysisSummary,
    ImpactFactorModel,
    ImpactPathSummary,
    RecommendationAnalysisSummary,
    RecommendationExecutionStepModel,
    RepositoryEngineeringOverview,
    RiskHotspotSummary,
    RiskSummary,
    TraceabilityGapSummary,
    TraceabilitySummary,
)
from codestrata_platform.application.knowledge_graph.intelligence.policies import (
    ANALYSIS_POLICY_VERSION,
    default_impact_policy,
)
from codestrata_platform.application.knowledge_graph.intelligence.queries import (
    AnalyzeComponentImpactQuery,
    AnalyzeFindingImpactQuery,
    AnalyzeRecommendationImpactQuery,
    AnalyzeTechnologyImpactQuery,
    GetDependencyAnalysisQuery,
    GetEvidenceTraceabilityQuery,
    GetFindingTraceabilityQuery,
    GetGraphCoverageQuery,
    GetGraphRiskSummaryQuery,
    GetRecommendationAnalysisQuery,
    GetRecommendationTraceabilityQuery,
    GetRepositoryEngineeringOverviewQuery,
    TenantGraphScope,
    ValidateGraphIntegrityQuery,
)
from codestrata_platform.domain.knowledge_graph.analysis.context import (
    GraphQueryContext,
    GraphQueryScope,
    ImpactDirection,
)
from codestrata_platform.domain.knowledge_graph.analysis.coverage import analyze_coverage
from codestrata_platform.domain.knowledge_graph.analysis.dependency import analyze_dependencies
from codestrata_platform.domain.knowledge_graph.analysis.impact import (
    collect_connected_by_types,
    finding_severity,
)
from codestrata_platform.domain.knowledge_graph.analysis.integrity import validate_graph_integrity
from codestrata_platform.domain.knowledge_graph.analysis.ports import GraphIntelligenceRepository
from codestrata_platform.domain.knowledge_graph.analysis.recommendation import (
    analyze_recommendations,
)
from codestrata_platform.domain.knowledge_graph.analysis.risk import analyze_risk
from codestrata_platform.domain.knowledge_graph.analysis.traceability import (
    trace_evidence,
    trace_finding,
    trace_recommendation,
)
from codestrata_platform.domain.knowledge_graph.edge import GraphEdge
from codestrata_platform.domain.knowledge_graph.graph import EngineeringKnowledgeGraph
from codestrata_platform.domain.knowledge_graph.identifiers import GraphNodeId, KnowledgeGraphId
from codestrata_platform.domain.knowledge_graph.lifecycle import GraphStatus
from codestrata_platform.domain.knowledge_graph.node import GraphNode
from codestrata_platform.domain.knowledge_graph.ports import KnowledgeGraphRepository
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphEdgeType, GraphNodeType


def _now() -> datetime:
    return datetime.now(UTC)


def _adjacency(
    edges: tuple[GraphEdge, ...],
) -> tuple[dict[str, list[tuple[str, GraphEdge]]], dict[str, list[tuple[str, GraphEdge]]]]:
    outgoing: dict[str, list[tuple[str, GraphEdge]]] = defaultdict(list)
    incoming: dict[str, list[tuple[str, GraphEdge]]] = defaultdict(list)
    for edge in edges:
        outgoing[edge.source_node_id.value].append((edge.target_node_id.value, edge))
        incoming[edge.target_node_id.value].append((edge.source_node_id.value, edge))
    return outgoing, incoming


class _GraphAccess:
    """Shared completed-graph loading and tenant checks."""

    def __init__(
        self,
        *,
        graphs: KnowledgeGraphRepository,
        intelligence: GraphIntelligenceRepository,
    ) -> None:
        self._graphs = graphs
        self._intelligence = intelligence

    def require_completed(
        self,
        graph_id: KnowledgeGraphId,
        scope: TenantGraphScope,
    ) -> tuple[EngineeringKnowledgeGraph, GraphQueryContext]:
        graph = self._graphs.get(graph_id)
        if graph is None:
            raise NotFoundError(
                f"Knowledge graph not found: {graph_id.value}",
                reason_code="knowledge_graph_not_found",
            )
        if graph.status is not GraphStatus.COMPLETED:
            raise GraphNotReadyError(
                f"Knowledge graph {graph_id.value} is not completed",
                reason_code="graph_not_completed",
            )
        if scope.organization_id is not None and graph.organization_id != scope.organization_id:
            raise GraphNotReadyError(
                "Graph organization ownership mismatch",
                reason_code="graph_tenant_mismatch",
            )
        if scope.workspace_id is not None and graph.workspace_id != scope.workspace_id:
            raise GraphNotReadyError(
                "Graph workspace ownership mismatch",
                reason_code="graph_tenant_mismatch",
            )
        if scope.repository_id is not None and graph.repository_id != scope.repository_id:
            raise GraphNotReadyError(
                "Graph repository ownership mismatch",
                reason_code="graph_tenant_mismatch",
            )
        query_scope = GraphQueryScope(
            organization_id=graph.organization_id,
            workspace_id=graph.workspace_id,
            repository_id=graph.repository_id,
        )
        context = self._intelligence.get_graph_context(graph_id, query_scope)
        return graph, context


class DefaultGraphImpactService:
    def __init__(
        self,
        *,
        graphs: KnowledgeGraphRepository,
        intelligence: GraphIntelligenceRepository,
    ) -> None:
        self._access = _GraphAccess(graphs=graphs, intelligence=intelligence)
        self._policy = default_impact_policy()

    def analyze_component(self, query: AnalyzeComponentImpactQuery) -> ImpactAnalysisSummary:
        return self._analyze(query.graph_id, query.node_id, GraphNodeType.COMPONENT, query)

    def analyze_technology(self, query: AnalyzeTechnologyImpactQuery) -> ImpactAnalysisSummary:
        return self._analyze(query.graph_id, query.node_id, GraphNodeType.TECHNOLOGY, query)

    def analyze_finding(self, query: AnalyzeFindingImpactQuery) -> ImpactAnalysisSummary:
        return self._analyze(query.graph_id, query.node_id, GraphNodeType.FINDING, query)

    def analyze_recommendation(
        self,
        query: AnalyzeRecommendationImpactQuery,
    ) -> ImpactAnalysisSummary:
        return self._analyze(query.graph_id, query.node_id, GraphNodeType.RECOMMENDATION, query)

    def _analyze(
        self,
        graph_id: KnowledgeGraphId,
        node_id: GraphNodeId,
        expected_type: GraphNodeType,
        query: AnalyzeComponentImpactQuery
        | AnalyzeTechnologyImpactQuery
        | AnalyzeFindingImpactQuery
        | AnalyzeRecommendationImpactQuery,
    ) -> ImpactAnalysisSummary:
        graph, context = self._access.require_completed(graph_id, query.scope)
        subject = next((item for item in graph.nodes if item.node_id == node_id), None)
        if subject is None or subject.node_type is not expected_type:
            raise NotFoundError(
                f"Graph node not found or wrong type: {node_id.value}",
                reason_code="graph_node_not_found",
            )
        nodes = {item.node_id.value: item for item in graph.nodes}
        outgoing, incoming = _adjacency(graph.edges)
        target_types = frozenset(
            {
                GraphNodeType.COMPONENT,
                GraphNodeType.TECHNOLOGY,
                GraphNodeType.FINDING,
                GraphNodeType.RECOMMENDATION,
                GraphNodeType.EVIDENCE,
                GraphNodeType.RISK,
            }
        )
        use_out = query.direction in {
            ImpactDirection.DOWNSTREAM,
            ImpactDirection.BOTH,
        }
        use_in = query.direction in {
            ImpactDirection.UPSTREAM,
            ImpactDirection.BOTH,
        }
        impacted, related_edges = collect_connected_by_types(
            subject_id=subject.node_id.value,
            nodes=nodes,
            adjacency_out=outgoing if use_out else {},
            adjacency_in=incoming if use_in else {},
            node_types=target_types,
            max_depth=query.limits.maximum_depth,
            max_nodes=query.limits.maximum_nodes,
        )
        findings = tuple(
            nodes[item.node_id]
            for item in impacted
            if item.node_type is GraphNodeType.FINDING and item.node_id in nodes
        )
        if subject.node_type is GraphNodeType.FINDING:
            findings = (subject,)
        resolved = {
            edge.target_node_id.value
            for edge in graph.edges
            if edge.edge_type is GraphEdgeType.RECOMMENDATION_RESOLVES_FINDING
        }
        unresolved = sum(
            1
            for item in findings
            if finding_severity(item) in {"high", "critical"} and item.node_id.value not in resolved
        )
        direct = len(outgoing.get(subject.node_id.value, []))
        transitive = len({item.node_id for item in impacted})
        score = self._policy.score(
            subject=subject,
            related_findings=findings,
            related_edges=related_edges,
            direct_dependents=direct,
            transitive_dependents=transitive,
            max_depth=max((item.depth for item in impacted), default=0),
            unresolved_recommendation_count=unresolved,
        )
        paths: tuple[ImpactPathSummary, ...] = ()
        if query.include_paths:
            paths = tuple(
                ImpactPathSummary(node_ids=(subject.node_id.value, item.node_id), edge_ids=())
                for item in impacted[: query.limits.maximum_paths]
            )
        diagnostics = ()
        if query.include_diagnostics:
            diagnostics = (
                f"direction={query.direction.value}",
                f"max_depth={query.limits.maximum_depth}",
                f"impacted={len(impacted)}",
            )
        return ImpactAnalysisSummary(
            graph_id=context.graph_id.value,
            graph_version=context.graph_version.value,
            engineering_snapshot_id=context.engineering_snapshot_id.value,
            generated_at=_now(),
            subject_node_id=subject.node_id.value,
            subject_node_type=subject.node_type.value,
            score=score.score,
            severity=score.severity,
            policy_version=score.policy_version,
            contributing_factors=tuple(
                ImpactFactorModel.from_domain(item) for item in score.contributing_factors
            ),
            impacted_node_ids=tuple(item.node_id for item in impacted),
            source_node_ids=score.source_node_ids,
            source_edge_ids=score.source_edge_ids,
            paths=paths,
            diagnostics=diagnostics,
        )


class DefaultGraphTraceabilityService:
    def __init__(
        self,
        *,
        graphs: KnowledgeGraphRepository,
        intelligence: GraphIntelligenceRepository,
    ) -> None:
        self._access = _GraphAccess(graphs=graphs, intelligence=intelligence)

    def finding(self, query: GetFindingTraceabilityQuery) -> TraceabilitySummary:
        graph, context = self._access.require_completed(query.graph_id, query.scope)
        node = self._require_node(graph, query.node_id, GraphNodeType.FINDING)
        result = trace_finding(
            node,
            {item.node_id.value: item for item in graph.nodes},
            graph.edges,
        )
        return TraceabilitySummary(
            graph_id=context.graph_id.value,
            graph_version=context.graph_version.value,
            engineering_snapshot_id=context.engineering_snapshot_id.value,
            generated_at=_now(),
            subject_node_id=node.node_id.value,
            subject_node_type=node.node_type.value,
            related={
                "repository": result.repository_node_ids,
                "component": result.component_node_ids,
                "technology": result.technology_node_ids,
                "category": result.category_node_ids,
                "risk": result.risk_node_ids,
                "evidence": result.evidence_node_ids,
                "recommendation": result.recommendation_node_ids,
            },
            edge_ids=result.edge_ids,
            gaps=tuple(
                TraceabilityGapSummary(
                    gap_type=item.gap_type.value,
                    node_id=item.node_id,
                    message=item.message,
                )
                for item in result.gaps
            ),
        )

    def recommendation(self, query: GetRecommendationTraceabilityQuery) -> TraceabilitySummary:
        graph, context = self._access.require_completed(query.graph_id, query.scope)
        node = self._require_node(graph, query.node_id, GraphNodeType.RECOMMENDATION)
        result = trace_recommendation(
            node,
            {item.node_id.value: item for item in graph.nodes},
            graph.edges,
        )
        return TraceabilitySummary(
            graph_id=context.graph_id.value,
            graph_version=context.graph_version.value,
            engineering_snapshot_id=context.engineering_snapshot_id.value,
            generated_at=_now(),
            subject_node_id=node.node_id.value,
            subject_node_type=node.node_type.value,
            related={
                "finding": result.finding_node_ids,
                "component": result.component_node_ids,
                "evidence": result.evidence_node_ids,
                "dependency": result.dependency_node_ids,
            },
            edge_ids=result.edge_ids,
            gaps=tuple(
                TraceabilityGapSummary(
                    gap_type=item.gap_type.value,
                    node_id=item.node_id,
                    message=item.message,
                )
                for item in result.gaps
            ),
        )

    def evidence(self, query: GetEvidenceTraceabilityQuery) -> TraceabilitySummary:
        graph, context = self._access.require_completed(query.graph_id, query.scope)
        node = self._require_node(graph, query.node_id, GraphNodeType.EVIDENCE)
        result = trace_evidence(
            node,
            {item.node_id.value: item for item in graph.nodes},
            graph.edges,
        )
        return TraceabilitySummary(
            graph_id=context.graph_id.value,
            graph_version=context.graph_version.value,
            engineering_snapshot_id=context.engineering_snapshot_id.value,
            generated_at=_now(),
            subject_node_id=node.node_id.value,
            subject_node_type=node.node_type.value,
            related={
                "finding": result.finding_node_ids,
                "component": result.component_node_ids,
                "technology": result.technology_node_ids,
            },
            edge_ids=result.edge_ids,
            gaps=(),
        )

    @staticmethod
    def _require_node(
        graph: EngineeringKnowledgeGraph,
        node_id: GraphNodeId,
        expected: GraphNodeType,
    ) -> GraphNode:
        node = next((item for item in graph.nodes if item.node_id == node_id), None)
        if node is None or node.node_type is not expected:
            raise NotFoundError(
                f"Graph node not found or wrong type: {node_id.value}",
                reason_code="graph_node_not_found",
            )
        return node


class DefaultGraphCoverageService:
    def __init__(
        self,
        *,
        graphs: KnowledgeGraphRepository,
        intelligence: GraphIntelligenceRepository,
    ) -> None:
        self._access = _GraphAccess(graphs=graphs, intelligence=intelligence)

    def get_coverage(self, query: GetGraphCoverageQuery) -> CoverageSummary:
        graph, context = self._access.require_completed(query.graph_id, query.scope)
        analysis = analyze_coverage(graph.nodes, graph.edges)
        return CoverageSummary(
            graph_id=context.graph_id.value,
            graph_version=context.graph_version.value,
            engineering_snapshot_id=context.engineering_snapshot_id.value,
            generated_at=_now(),
            findings_with_evidence=CoverageMetricModel.from_ratio(
                analysis.findings.with_evidence
            ),
            high_critical_with_recommendations=CoverageMetricModel.from_ratio(
                analysis.findings.high_critical_with_recommendations
            ),
            findings_linked_to_components=CoverageMetricModel.from_ratio(
                analysis.findings.linked_to_components
            ),
            technologies_linked_to_components=CoverageMetricModel.from_ratio(
                analysis.technologies.linked_to_components
            ),
            recommendations_linked_to_findings=CoverageMetricModel.from_ratio(
                analysis.recommendations.linked_to_findings
            ),
            objects_with_source_reference=CoverageMetricModel.from_ratio(
                analysis.objects_with_source_reference
            ),
        )


class DefaultGraphDependencyService:
    def __init__(
        self,
        *,
        graphs: KnowledgeGraphRepository,
        intelligence: GraphIntelligenceRepository,
    ) -> None:
        self._access = _GraphAccess(graphs=graphs, intelligence=intelligence)

    def analyze(self, query: GetDependencyAnalysisQuery) -> DependencyAnalysisSummary:
        graph, context = self._access.require_completed(query.graph_id, query.scope)
        analysis = analyze_dependencies(
            graph.nodes,
            graph.edges,
            subject_node_id=query.node_id.value if query.node_id else None,
            max_depth=query.limits.maximum_depth,
            max_nodes=query.limits.maximum_nodes,
            max_paths=query.limits.maximum_paths,
        )
        return DependencyAnalysisSummary(
            graph_id=context.graph_id.value,
            graph_version=context.graph_version.value,
            engineering_snapshot_id=context.engineering_snapshot_id.value,
            generated_at=_now(),
            direct_dependencies=analysis.direct_dependencies,
            transitive_dependencies=analysis.transitive_dependencies,
            upstream_dependencies=analysis.upstream_dependencies,
            downstream_dependencies=analysis.downstream_dependencies,
            cycles=tuple(
                DependencyCycleSummary(node_ids=item.node_ids, edge_ids=item.edge_ids)
                for item in analysis.cycles
            ),
            hotspots=tuple(
                DependencyHotspotSummary(
                    node_id=item.node_id,
                    display_name=item.display_name,
                    fan_in=item.fan_in,
                    fan_out=item.fan_out,
                    kind=item.kind,
                )
                for item in analysis.hotspots
            ),
            orphan_component_ids=tuple(item.node_id for item in analysis.orphans),
            maximum_depth=analysis.depth_summary.maximum_depth,
        )


class DefaultGraphRiskService:
    def __init__(
        self,
        *,
        graphs: KnowledgeGraphRepository,
        intelligence: GraphIntelligenceRepository,
    ) -> None:
        self._access = _GraphAccess(graphs=graphs, intelligence=intelligence)

    def summarize(self, query: GetGraphRiskSummaryQuery) -> RiskSummary:
        graph, context = self._access.require_completed(query.graph_id, query.scope)
        deps = analyze_dependencies(
            graph.nodes,
            graph.edges,
            max_depth=5,
            max_nodes=500,
            max_paths=25,
        )
        fan_in = {item.node_id: item.fan_in for item in deps.hotspots}
        analysis = analyze_risk(graph.nodes, graph.edges, fan_in=fan_in)
        return RiskSummary(
            graph_id=context.graph_id.value,
            graph_version=context.graph_version.value,
            engineering_snapshot_id=context.engineering_snapshot_id.value,
            generated_at=_now(),
            by_severity=analysis.distribution.by_severity,
            by_category=analysis.distribution.by_category,
            hotspots=tuple(
                RiskHotspotSummary(
                    node_id=item.node_id,
                    node_type=item.node_type,
                    display_name=item.display_name,
                    score=item.score,
                    factors=item.factors,
                )
                for item in analysis.hotspots
            ),
            unresolved_finding_ids=tuple(item.finding_node_id for item in analysis.unresolved),
        )


class DefaultGraphRecommendationService:
    def __init__(
        self,
        *,
        graphs: KnowledgeGraphRepository,
        intelligence: GraphIntelligenceRepository,
    ) -> None:
        self._access = _GraphAccess(graphs=graphs, intelligence=intelligence)

    def analyze(self, query: GetRecommendationAnalysisQuery) -> RecommendationAnalysisSummary:
        graph, context = self._access.require_completed(query.graph_id, query.scope)
        analysis = analyze_recommendations(graph.nodes, graph.edges)
        return RecommendationAnalysisSummary(
            graph_id=context.graph_id.value,
            graph_version=context.graph_version.value,
            engineering_snapshot_id=context.engineering_snapshot_id.value,
            generated_at=_now(),
            total=analysis.coverage.total,
            linked_to_findings=analysis.coverage.linked_to_findings,
            execution_order=tuple(
                RecommendationExecutionStepModel(
                    node_id=item.node_id,
                    display_name=item.display_name,
                    priority=item.priority,
                    order=item.order,
                )
                for item in analysis.execution_order
            ),
            cycles=analysis.cycles,
            conflict_count=len(analysis.conflicts),
        )


class DefaultGraphIntegrityService:
    def __init__(
        self,
        *,
        graphs: KnowledgeGraphRepository,
        intelligence: GraphIntelligenceRepository,
    ) -> None:
        self._access = _GraphAccess(graphs=graphs, intelligence=intelligence)

    def validate(self, query: ValidateGraphIntegrityQuery) -> GraphIntegritySummary:
        graph, context = self._access.require_completed(query.graph_id, query.scope)
        report = validate_graph_integrity(graph)
        return GraphIntegritySummary(
            graph_id=context.graph_id.value,
            graph_version=context.graph_version.value,
            engineering_snapshot_id=context.engineering_snapshot_id.value,
            generated_at=_now(),
            integrity_version=report.integrity_version,
            passed=report.passed,
            issue_count=report.issue_count,
            critical_issue_count=report.critical_issue_count,
            issues=tuple(
                GraphIntegrityIssueSummary(
                    issue_type=item.issue_type.value,
                    severity=item.severity.value,
                    message=item.message,
                    node_ids=item.node_ids,
                    edge_ids=item.edge_ids,
                )
                for item in report.issues
            ),
        )


class DefaultRepositoryEngineeringOverviewService:
    def __init__(
        self,
        *,
        graphs: KnowledgeGraphRepository,
        intelligence: GraphIntelligenceRepository,
        impact: DefaultGraphImpactService | None = None,
        coverage: DefaultGraphCoverageService | None = None,
        dependencies: DefaultGraphDependencyService | None = None,
        risks: DefaultGraphRiskService | None = None,
        integrity: DefaultGraphIntegrityService | None = None,
    ) -> None:
        self._graphs = graphs
        self._intelligence = intelligence
        self._access = _GraphAccess(graphs=graphs, intelligence=intelligence)
        self._impact = impact or DefaultGraphImpactService(
            graphs=graphs, intelligence=intelligence
        )
        self._coverage = coverage or DefaultGraphCoverageService(
            graphs=graphs, intelligence=intelligence
        )
        self._dependencies = dependencies or DefaultGraphDependencyService(
            graphs=graphs, intelligence=intelligence
        )
        self._risks = risks or DefaultGraphRiskService(
            graphs=graphs, intelligence=intelligence
        )
        self._integrity = integrity or DefaultGraphIntegrityService(
            graphs=graphs, intelligence=intelligence
        )

    def get_overview(
        self,
        query: GetRepositoryEngineeringOverviewQuery,
    ) -> RepositoryEngineeringOverview:
        graph = self._graphs.get_latest_completed(query.repository_id)
        if graph is None:
            raise NotFoundError(
                f"Knowledge graph not found for repository {query.repository_id.value}",
                reason_code="knowledge_graph_not_found",
            )
        scope = TenantGraphScope(
            organization_id=query.organization_id,
            workspace_id=query.workspace_id,
            repository_id=query.repository_id,
        )
        _graph, context = self._access.require_completed(graph.graph_id, scope)
        coverage = self._coverage.get_coverage(
            GetGraphCoverageQuery(graph_id=graph.graph_id, scope=scope)
        )
        deps = self._dependencies.analyze(
            GetDependencyAnalysisQuery(graph_id=graph.graph_id, scope=scope)
        )
        risks = self._risks.summarize(
            GetGraphRiskSummaryQuery(graph_id=graph.graph_id, scope=scope)
        )
        integrity = self._integrity.validate(
            ValidateGraphIntegrityQuery(graph_id=graph.graph_id, scope=scope)
        )
        finding_distribution: dict[str, int] = defaultdict(int)
        for node in graph.nodes:
            if node.node_type is GraphNodeType.FINDING:
                finding_distribution[finding_severity(node)] += 1
        components = [
            item for item in graph.nodes if item.node_type is GraphNodeType.COMPONENT
        ]
        technologies = [
            item for item in graph.nodes if item.node_type is GraphNodeType.TECHNOLOGY
        ]
        recommendations = [
            item for item in graph.nodes if item.node_type is GraphNodeType.RECOMMENDATION
        ]
        highest_components = tuple(
            item.node_id
            for item in sorted(
                risks.hotspots,
                key=lambda hotspot: (-hotspot.score, hotspot.node_id),
            )
            if item.node_type == GraphNodeType.COMPONENT.value
        )[:10]
        highest_technologies = tuple(
            item.node_id
            for item in sorted(
                risks.hotspots,
                key=lambda hotspot: (-hotspot.score, hotspot.node_id),
            )
            if item.node_type == GraphNodeType.TECHNOLOGY.value
        )[:10]
        return RepositoryEngineeringOverview(
            graph_id=context.graph_id.value,
            graph_version=context.graph_version.value,
            engineering_snapshot_id=context.engineering_snapshot_id.value,
            generated_at=_now(),
            repository_id=query.repository_id.value,
            technology_count=len(technologies),
            component_count=len(components),
            finding_distribution=dict(sorted(finding_distribution.items())),
            recommendation_count=len(recommendations),
            evidence_coverage=coverage.findings_with_evidence,
            recommendation_coverage=coverage.high_critical_with_recommendations,
            dependency_hotspots=deps.hotspots[:10],
            risk_hotspots=risks.hotspots[:10],
            highest_impact_components=highest_components,
            highest_impact_technologies=highest_technologies,
            integrity_passed=integrity.passed,
            policy_version=ANALYSIS_POLICY_VERSION,
        )


class GraphIntelligenceFacade:
    """Aggregate facade used by API wiring."""

    def __init__(
        self,
        *,
        graphs: KnowledgeGraphRepository,
        intelligence: GraphIntelligenceRepository,
    ) -> None:
        self.impact = DefaultGraphImpactService(graphs=graphs, intelligence=intelligence)
        self.traceability = DefaultGraphTraceabilityService(
            graphs=graphs, intelligence=intelligence
        )
        self.coverage = DefaultGraphCoverageService(graphs=graphs, intelligence=intelligence)
        self.dependencies = DefaultGraphDependencyService(
            graphs=graphs, intelligence=intelligence
        )
        self.risks = DefaultGraphRiskService(graphs=graphs, intelligence=intelligence)
        self.recommendations = DefaultGraphRecommendationService(
            graphs=graphs, intelligence=intelligence
        )
        self.integrity = DefaultGraphIntegrityService(graphs=graphs, intelligence=intelligence)
        self.overview = DefaultRepositoryEngineeringOverviewService(
            graphs=graphs,
            intelligence=intelligence,
            impact=self.impact,
            coverage=self.coverage,
            dependencies=self.dependencies,
            risks=self.risks,
            integrity=self.integrity,
        )
