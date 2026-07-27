"""Assessment intelligence query controllers."""

from __future__ import annotations

from fastapi import APIRouter, Query

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.api.dto.response.intelligence import (
    FindingDetailsResponse,
    FindingSummaryResponse,
    MetricDetailsResponse,
    RecommendationDetailsResponse,
)
from codestrata_platform.application.queries.intelligence import (
    GetFindingQuery,
    GetRecommendationQuery,
    ListAssessmentFindingsQuery,
    ListAssessmentMetricsQuery,
    ListAssessmentRecommendationsQuery,
)
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.intelligence import FindingId, FindingSeverity, RecommendationId

router = APIRouter(prefix="/assessments/{assessment_id}", tags=["Assessment Intelligence"])


@router.get(
    "/findings",
    response_model=list[FindingSummaryResponse],
    summary="List assessment findings",
)
def list_findings(
    assessment_id: str,
    services: ServicesDep,
    severity: str | None = Query(default=None),
) -> list[FindingSummaryResponse]:
    severity_filter = FindingSeverity(severity.strip().lower()) if severity else None
    items = services.intelligence.list_assessment_findings(
        ListAssessmentFindingsQuery(
            assessment_id=AssessmentId(assessment_id.strip()),
            severity=severity_filter,
        )
    )
    return [
        FindingSummaryResponse(
            finding_id=item.finding_id.value,
            assessment_id=item.assessment_id.value,
            category=item.category.value,
            rule_id=item.rule_id,
            title=item.title,
            severity=item.severity.value,
            confidence=item.confidence,
        )
        for item in items
    ]


@router.get(
    "/findings/{finding_id}",
    response_model=FindingDetailsResponse,
    summary="Get assessment finding",
)
def get_finding(
    assessment_id: str,
    finding_id: str,
    services: ServicesDep,
) -> FindingDetailsResponse:
    _ = assessment_id
    details = services.intelligence.get_finding(
        GetFindingQuery(finding_id=FindingId(finding_id.strip()))
    )
    return FindingDetailsResponse(
        finding_id=details.finding_id.value,
        assessment_id=details.assessment_id.value,
        category=details.category.value,
        rule_id=details.rule_id,
        title=details.title,
        summary=details.summary,
        severity=details.severity.value,
        confidence=details.confidence,
        production_scope=details.production_scope,
        affected_component=details.affected_component,
        affected_path_reference=details.affected_path_reference,
        remediation_reference=details.remediation_reference,
        metadata=dict(details.metadata),
        evidence_references=[
            {
                "evidence_id": item.evidence_id.value,
                "path_reference": item.path_reference,
                "line_start": item.line_start,
                "line_end": item.line_end,
                "symbol": item.symbol,
                "component": item.component,
                "evidence_type": item.evidence_type,
                "checksum": item.checksum,
                "redacted_excerpt": item.redacted_excerpt,
                "source_artifact_id": item.source_artifact_id,
            }
            for item in details.evidence_references
        ],
    )


@router.get(
    "/metrics",
    response_model=list[MetricDetailsResponse],
    summary="List assessment metrics",
)
def list_metrics(assessment_id: str, services: ServicesDep) -> list[MetricDetailsResponse]:
    items = services.intelligence.list_assessment_metrics(
        ListAssessmentMetricsQuery(assessment_id=AssessmentId(assessment_id.strip()))
    )
    return [
        MetricDetailsResponse(
            name=item.name,
            kind=item.kind.value,
            value=item.value,
            unit=item.unit,
            metadata=dict(item.metadata),
        )
        for item in items
    ]


@router.get(
    "/recommendations",
    response_model=list[RecommendationDetailsResponse],
    summary="List assessment recommendations",
)
def list_recommendations(
    assessment_id: str,
    services: ServicesDep,
) -> list[RecommendationDetailsResponse]:
    items = services.intelligence.list_assessment_recommendations(
        ListAssessmentRecommendationsQuery(assessment_id=AssessmentId(assessment_id.strip()))
    )
    return [_recommendation_response(item) for item in items]


@router.get(
    "/recommendations/{recommendation_id}",
    response_model=RecommendationDetailsResponse,
    summary="Get assessment recommendation",
)
def get_recommendation(
    assessment_id: str,
    recommendation_id: str,
    services: ServicesDep,
) -> RecommendationDetailsResponse:
    _ = assessment_id
    item = services.intelligence.get_recommendation(
        GetRecommendationQuery(recommendation_id=RecommendationId(recommendation_id.strip()))
    )
    return _recommendation_response(item)


def _recommendation_response(item) -> RecommendationDetailsResponse:
    return RecommendationDetailsResponse(
        recommendation_id=item.recommendation_id.value,
        assessment_id=item.assessment_id.value,
        category=item.category.value,
        title=item.title,
        rationale=item.rationale,
        priority=item.priority.value,
        effort=item.effort,
        impact=item.impact,
        roadmap_horizon=item.roadmap_horizon,
        dependencies=list(item.dependencies),
        related_finding_ids=list(item.related_finding_ids),
        metadata=dict(item.metadata),
    )
