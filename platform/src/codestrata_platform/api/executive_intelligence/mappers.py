"""Executive Intelligence API mappers."""

from __future__ import annotations

from codestrata_platform.api.executive_intelligence.dto import (
    ExecutiveFindingResponse,
    ExecutiveFindingsResponse,
    ExecutiveIntelligenceDetailsResponse,
    ExecutiveIntelligencePageResponse,
    ExecutiveIntelligenceSummaryResponse,
    ExecutiveMetricResponse,
    ExecutiveMetricsResponse,
    ExecutiveRecommendationResponse,
    ExecutiveRecommendationsResponse,
    StrategicObservationResponse,
)
from codestrata_platform.application.common.pagination import PageResult
from codestrata_platform.application.executive_intelligence.models import (
    ExecutiveFindingsModel,
    ExecutiveIntelligenceDetails,
    ExecutiveIntelligenceSummary,
    ExecutiveMetricsModel,
    ExecutiveRecommendationsModel,
)
from codestrata_platform.domain.executive_intelligence.models import (
    ExecutiveFinding,
    ExecutiveMetric,
    ExecutiveRecommendation,
    StrategicObservation,
)


def summary_response(summary: ExecutiveIntelligenceSummary) -> ExecutiveIntelligenceSummaryResponse:
    return ExecutiveIntelligenceSummaryResponse(
        executive_intelligence_id=summary.executive_intelligence_id,
        organization_id=summary.organization_id,
        workspace_id=summary.workspace_id,
        portfolio_id=summary.portfolio_id,
        portfolio_snapshot_id=summary.portfolio_snapshot_id,
        portfolio_snapshot_version=summary.portfolio_snapshot_version,
        version=summary.version,
        status=summary.status.value,
        projection_key=summary.projection_key,
        schema_version=summary.schema_version,
        policy_version=summary.policy_version,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
        completed_at=summary.completed_at,
        superseded_at=summary.superseded_at,
        failure_reason=summary.failure_reason,
        metric_count=summary.metric_count,
        finding_count=summary.finding_count,
        recommendation_count=summary.recommendation_count,
        observation_count=summary.observation_count,
    )


def metric_response(item: ExecutiveMetric) -> ExecutiveMetricResponse:
    return ExecutiveMetricResponse(
        metric_id=item.metric_id.value,
        key=item.key.value,
        score=item.score,
        confidence=item.confidence,
        confidence_band=item.confidence_band.value,
        coverage=item.coverage,
        inputs=list(item.inputs),
        calculation_rule=item.calculation_rule,
        limitations=list(item.limitations),
        policy_version=item.policy_version,
    )


def finding_response(item: ExecutiveFinding) -> ExecutiveFindingResponse:
    return ExecutiveFindingResponse(
        finding_id=item.finding_id.value,
        category=item.category.value,
        title=item.title,
        summary=item.summary,
        severity_band=item.severity_band.value,
        confidence=item.confidence,
        confidence_band=item.confidence_band.value,
        affected_repository_ids=list(item.affected_repository_ids),
        source_references=list(item.source_references),
        evidence=list(item.evidence),
        policy_version=item.policy_version,
    )


def recommendation_response(item: ExecutiveRecommendation) -> ExecutiveRecommendationResponse:
    return ExecutiveRecommendationResponse(
        recommendation_id=item.recommendation_id.value,
        theme=item.theme.value,
        title=item.title,
        rationale=item.rationale,
        affected_repository_ids=list(item.affected_repository_ids),
        confidence=item.confidence,
        confidence_band=item.confidence_band.value,
        expected_impact=item.expected_impact.value,
        source_references=list(item.source_references),
        priority_score=item.priority_score,
        policy_version=item.policy_version,
    )


def observation_response(item: StrategicObservation) -> StrategicObservationResponse:
    return StrategicObservationResponse(
        observation_key=item.observation_key,
        title=item.title,
        summary=item.summary,
        related_metric_keys=list(item.related_metric_keys),
        related_finding_ids=list(item.related_finding_ids),
        confidence=item.confidence,
        confidence_band=item.confidence_band.value,
    )


def details_response(details: ExecutiveIntelligenceDetails) -> ExecutiveIntelligenceDetailsResponse:
    return ExecutiveIntelligenceDetailsResponse(
        summary=summary_response(details.summary),
        metrics=[metric_response(item) for item in details.metrics],
        findings=[finding_response(item) for item in details.findings],
        recommendations=[recommendation_response(item) for item in details.recommendations],
        observations=[observation_response(item) for item in details.observations],
        limitations=list(details.limitations),
    )


def metrics_response(model: ExecutiveMetricsModel) -> ExecutiveMetricsResponse:
    return ExecutiveMetricsResponse(
        summary=summary_response(model.summary),
        metrics=[metric_response(item) for item in model.metrics],
    )


def findings_response(model: ExecutiveFindingsModel) -> ExecutiveFindingsResponse:
    return ExecutiveFindingsResponse(
        summary=summary_response(model.summary),
        findings=[finding_response(item) for item in model.findings],
    )


def recommendations_response(
    model: ExecutiveRecommendationsModel,
) -> ExecutiveRecommendationsResponse:
    return ExecutiveRecommendationsResponse(
        summary=summary_response(model.summary),
        recommendations=[recommendation_response(item) for item in model.recommendations],
    )


def page_response(page: PageResult) -> ExecutiveIntelligencePageResponse:
    return ExecutiveIntelligencePageResponse(
        items=[summary_response(item) for item in page.items],
        total=page.total,
        offset=page.offset,
        limit=page.limit,
    )
