"""Thin controllers for graph intelligence queries."""

from __future__ import annotations

from fastapi import APIRouter, Query

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.knowledge_graph.intelligence_dto import (
    CoverageResponse,
    DependencyAnalysisResponse,
    ImpactAnalysisResponse,
    ImpactRequest,
    IntegrityResponse,
    RecommendationAnalysisResponse,
    RepositoryOverviewResponse,
    RiskSummaryResponse,
    TraceabilityResponse,
)
from codestrata_platform.api.knowledge_graph.intelligence_mappers import (
    coverage_response,
    dependency_response,
    impact_response,
    integrity_response,
    overview_response,
    recommendation_response,
    risk_response,
    traceability_response,
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
    ValidateGraphIntegrityQuery,
)
from codestrata_platform.domain.knowledge_graph.analysis.context import (
    GraphQueryLimits,
    ImpactDirection,
)
from codestrata_platform.domain.knowledge_graph.identifiers import GraphNodeId, KnowledgeGraphId
from codestrata_platform.domain.repository.ids import RepositoryId

router = APIRouter(tags=["Knowledge Graph Intelligence"])


def _limits(body: ImpactRequest) -> GraphQueryLimits:
    return GraphQueryLimits(
        maximum_depth=body.max_depth,
        maximum_nodes=body.maximum_nodes,
        maximum_edges=body.maximum_edges,
        maximum_paths=body.maximum_paths,
    )


@router.get(
    "/knowledge-graphs/{graph_id}/overview",
    response_model=RepositoryOverviewResponse,
)
def graph_overview(graph_id: str, services: ServicesDep) -> RepositoryOverviewResponse:
    from codestrata_platform.application.knowledge_graph.queries import GetKnowledgeGraphQuery

    summary = services.knowledge_graphs.get_knowledge_graph(
        GetKnowledgeGraphQuery(graph_id=KnowledgeGraphId(graph_id.strip()))
    )
    result = services.graph_intelligence.overview.get_overview(
        GetRepositoryEngineeringOverviewQuery(
            repository_id=RepositoryId(summary.repository_id),
        )
    )
    return overview_response(result)


@router.post(
    "/knowledge-graphs/{graph_id}/impact/components/{node_id}",
    response_model=ImpactAnalysisResponse,
)
def component_impact(
    graph_id: str,
    node_id: str,
    services: ServicesDep,
    body: ImpactRequest | None = None,
) -> ImpactAnalysisResponse:
    request = body or ImpactRequest()
    result = services.graph_intelligence.impact.analyze_component(
        AnalyzeComponentImpactQuery(
            graph_id=KnowledgeGraphId(graph_id.strip()),
            node_id=GraphNodeId(node_id.strip()),
            direction=ImpactDirection(request.direction),
            limits=_limits(request),
            include_paths=request.include_paths,
            include_diagnostics=request.include_diagnostics,
        )
    )
    return impact_response(result)


@router.post(
    "/knowledge-graphs/{graph_id}/impact/technologies/{node_id}",
    response_model=ImpactAnalysisResponse,
)
def technology_impact(
    graph_id: str,
    node_id: str,
    services: ServicesDep,
    body: ImpactRequest | None = None,
) -> ImpactAnalysisResponse:
    request = body or ImpactRequest()
    result = services.graph_intelligence.impact.analyze_technology(
        AnalyzeTechnologyImpactQuery(
            graph_id=KnowledgeGraphId(graph_id.strip()),
            node_id=GraphNodeId(node_id.strip()),
            direction=ImpactDirection(request.direction),
            limits=_limits(request),
            include_paths=request.include_paths,
            include_diagnostics=request.include_diagnostics,
        )
    )
    return impact_response(result)


@router.post(
    "/knowledge-graphs/{graph_id}/impact/findings/{node_id}",
    response_model=ImpactAnalysisResponse,
)
def finding_impact(
    graph_id: str,
    node_id: str,
    services: ServicesDep,
    body: ImpactRequest | None = None,
) -> ImpactAnalysisResponse:
    request = body or ImpactRequest()
    result = services.graph_intelligence.impact.analyze_finding(
        AnalyzeFindingImpactQuery(
            graph_id=KnowledgeGraphId(graph_id.strip()),
            node_id=GraphNodeId(node_id.strip()),
            direction=ImpactDirection(request.direction),
            limits=_limits(request),
            include_paths=request.include_paths,
            include_diagnostics=request.include_diagnostics,
        )
    )
    return impact_response(result)


@router.post(
    "/knowledge-graphs/{graph_id}/impact/recommendations/{node_id}",
    response_model=ImpactAnalysisResponse,
)
def recommendation_impact(
    graph_id: str,
    node_id: str,
    services: ServicesDep,
    body: ImpactRequest | None = None,
) -> ImpactAnalysisResponse:
    request = body or ImpactRequest()
    result = services.graph_intelligence.impact.analyze_recommendation(
        AnalyzeRecommendationImpactQuery(
            graph_id=KnowledgeGraphId(graph_id.strip()),
            node_id=GraphNodeId(node_id.strip()),
            direction=ImpactDirection(request.direction),
            limits=_limits(request),
            include_paths=request.include_paths,
            include_diagnostics=request.include_diagnostics,
        )
    )
    return impact_response(result)


@router.get(
    "/knowledge-graphs/{graph_id}/traceability/findings/{node_id}",
    response_model=TraceabilityResponse,
)
def finding_traceability(
    graph_id: str,
    node_id: str,
    services: ServicesDep,
) -> TraceabilityResponse:
    result = services.graph_intelligence.traceability.finding(
        GetFindingTraceabilityQuery(
            graph_id=KnowledgeGraphId(graph_id.strip()),
            node_id=GraphNodeId(node_id.strip()),
        )
    )
    return traceability_response(result)


@router.get(
    "/knowledge-graphs/{graph_id}/traceability/recommendations/{node_id}",
    response_model=TraceabilityResponse,
)
def recommendation_traceability(
    graph_id: str,
    node_id: str,
    services: ServicesDep,
) -> TraceabilityResponse:
    result = services.graph_intelligence.traceability.recommendation(
        GetRecommendationTraceabilityQuery(
            graph_id=KnowledgeGraphId(graph_id.strip()),
            node_id=GraphNodeId(node_id.strip()),
        )
    )
    return traceability_response(result)


@router.get(
    "/knowledge-graphs/{graph_id}/traceability/evidence/{node_id}",
    response_model=TraceabilityResponse,
)
def evidence_traceability(
    graph_id: str,
    node_id: str,
    services: ServicesDep,
) -> TraceabilityResponse:
    result = services.graph_intelligence.traceability.evidence(
        GetEvidenceTraceabilityQuery(
            graph_id=KnowledgeGraphId(graph_id.strip()),
            node_id=GraphNodeId(node_id.strip()),
        )
    )
    return traceability_response(result)


@router.get("/knowledge-graphs/{graph_id}/coverage", response_model=CoverageResponse)
def graph_coverage(graph_id: str, services: ServicesDep) -> CoverageResponse:
    result = services.graph_intelligence.coverage.get_coverage(
        GetGraphCoverageQuery(graph_id=KnowledgeGraphId(graph_id.strip()))
    )
    return coverage_response(result)


@router.get(
    "/knowledge-graphs/{graph_id}/dependencies",
    response_model=DependencyAnalysisResponse,
)
def graph_dependencies(
    graph_id: str,
    services: ServicesDep,
    node_id: str | None = Query(default=None),
    max_depth: int = Query(default=5, ge=1, le=10),
) -> DependencyAnalysisResponse:
    result = services.graph_intelligence.dependencies.analyze(
        GetDependencyAnalysisQuery(
            graph_id=KnowledgeGraphId(graph_id.strip()),
            node_id=GraphNodeId(node_id.strip()) if node_id else None,
            limits=GraphQueryLimits(maximum_depth=max_depth),
        )
    )
    return dependency_response(result)


@router.get("/knowledge-graphs/{graph_id}/risks", response_model=RiskSummaryResponse)
def graph_risks(graph_id: str, services: ServicesDep) -> RiskSummaryResponse:
    result = services.graph_intelligence.risks.summarize(
        GetGraphRiskSummaryQuery(graph_id=KnowledgeGraphId(graph_id.strip()))
    )
    return risk_response(result)


@router.get(
    "/knowledge-graphs/{graph_id}/recommendation-analysis",
    response_model=RecommendationAnalysisResponse,
)
def recommendation_analysis(
    graph_id: str,
    services: ServicesDep,
) -> RecommendationAnalysisResponse:
    result = services.graph_intelligence.recommendations.analyze(
        GetRecommendationAnalysisQuery(graph_id=KnowledgeGraphId(graph_id.strip()))
    )
    return recommendation_response(result)


@router.get("/knowledge-graphs/{graph_id}/integrity", response_model=IntegrityResponse)
def graph_integrity(graph_id: str, services: ServicesDep) -> IntegrityResponse:
    result = services.graph_intelligence.integrity.validate(
        ValidateGraphIntegrityQuery(graph_id=KnowledgeGraphId(graph_id.strip()))
    )
    return integrity_response(result)


@router.get(
    "/repositories/{repository_id}/engineering-overview",
    response_model=RepositoryOverviewResponse,
)
def repository_engineering_overview(
    repository_id: str,
    services: ServicesDep,
) -> RepositoryOverviewResponse:
    result = services.graph_intelligence.overview.get_overview(
        GetRepositoryEngineeringOverviewQuery(
            repository_id=RepositoryId(repository_id.strip()),
        )
    )
    return overview_response(result)
