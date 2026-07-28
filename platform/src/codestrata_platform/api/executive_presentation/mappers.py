"""Executive Presentation API mappers."""

from __future__ import annotations

from codestrata_platform.api.executive_presentation.dto import (
    ExecutivePresentationResponse,
    PresentationConfidenceSummaryDto,
    PresentationCoverageSummaryDto,
    PresentationCtoSummaryDto,
    PresentationExecutiveSummaryDto,
    PresentationFindingDto,
    PresentationIdentityDto,
    PresentationKpiCardDto,
    PresentationObservationDto,
    PresentationRecommendationDto,
    PresentationRepositoryReferenceDto,
    PresentationScorecardDto,
    PresentationStrengthWeaknessItemDto,
    PresentationTechnologyItemDto,
    PresentationTechnologyLandscapeDto,
    PresentationTrendPointDto,
)
from codestrata_platform.application.executive_presentation.models import (
    ExecutivePresentationModel,
    PresentationConfidenceSummary,
    PresentationCoverageSummary,
    PresentationCtoSummary,
    PresentationExecutiveSummary,
    PresentationFinding,
    PresentationIdentity,
    PresentationKpiCard,
    PresentationObservation,
    PresentationRecommendation,
    PresentationRepositoryReference,
    PresentationScorecard,
    PresentationStrengthWeaknessItem,
    PresentationTechnologyItem,
    PresentationTechnologyLandscape,
    PresentationTrendPoint,
)


def _kpi(card: PresentationKpiCard) -> PresentationKpiCardDto:
    return PresentationKpiCardDto(
        identifier=card.identifier,
        metric_key=card.metric_key.value,
        title=card.title,
        score=card.score,
        status=card.status.value,
        confidence=card.confidence,
        confidence_band=card.confidence_band.value,
        coverage=card.coverage,
        description=card.description,
        calculation_disclosure=card.calculation_disclosure,
        limitations=list(card.limitations),
        drill_down_reference=card.drill_down_reference,
        inputs=list(card.inputs),
    )


def _finding(item: PresentationFinding) -> PresentationFindingDto:
    return PresentationFindingDto(
        finding_id=item.finding_id,
        title=item.title,
        category=item.category.value,
        severity=item.severity.value,
        description=item.description,
        affected_repository_ids=list(item.affected_repository_ids),
        confidence=item.confidence,
        confidence_band=item.confidence_band.value,
        evidence_references=list(item.evidence_references),
        source_references=list(item.source_references),
        limitations=list(item.limitations),
    )


def _recommendation(item: PresentationRecommendation) -> PresentationRecommendationDto:
    return PresentationRecommendationDto(
        recommendation_id=item.recommendation_id,
        title=item.title,
        theme=item.theme.value,
        priority_score=item.priority_score,
        rationale=item.rationale,
        expected_impact=item.expected_impact.value,
        affected_repository_ids=list(item.affected_repository_ids),
        confidence=item.confidence,
        confidence_band=item.confidence_band.value,
        supporting_finding_ids=list(item.supporting_finding_ids),
        source_references=list(item.source_references),
        limitations=list(item.limitations),
    )


def _observation(item: PresentationObservation) -> PresentationObservationDto:
    return PresentationObservationDto(
        observation_key=item.observation_key,
        title=item.title,
        summary=item.summary,
        related_metric_keys=list(item.related_metric_keys),
        related_finding_ids=list(item.related_finding_ids),
        confidence=item.confidence,
        confidence_band=item.confidence_band.value,
    )


def _strength(item: PresentationStrengthWeaknessItem) -> PresentationStrengthWeaknessItemDto:
    return PresentationStrengthWeaknessItemDto(
        key=item.key,
        title=item.title,
        summary=item.summary,
        related_metric_keys=list(item.related_metric_keys),
        related_finding_ids=list(item.related_finding_ids),
        confidence=item.confidence,
        confidence_band=item.confidence_band.value,
        definitive=item.definitive,
    )


def _tech_item(item: PresentationTechnologyItem) -> PresentationTechnologyItemDto:
    return PresentationTechnologyItemDto(
        key=item.key,
        title=item.title,
        category=item.category,
        summary=item.summary,
        affected_repository_ids=list(item.affected_repository_ids),
        confidence=item.confidence,
        evidence_references=list(item.evidence_references),
        source_references=list(item.source_references),
    )


def _tech_landscape(
    landscape: PresentationTechnologyLandscape,
) -> PresentationTechnologyLandscapeDto:
    return PresentationTechnologyLandscapeDto(
        fragmentation=[_tech_item(item) for item in landscape.fragmentation],
        duplicated_stacks=[_tech_item(item) for item in landscape.duplicated_stacks],
        unsupported_technologies=[
            _tech_item(item) for item in landscape.unsupported_technologies
        ],
        standardization_opportunities=[
            _tech_item(item) for item in landscape.standardization_opportunities
        ],
        limitations=list(landscape.limitations),
    )


def _repo(item: PresentationRepositoryReference) -> PresentationRepositoryReferenceDto:
    return PresentationRepositoryReferenceDto(
        repository_id=item.repository_id,
        display_name=item.display_name,
        snapshot_id=item.snapshot_id,
        status=item.status,
        participation_state=item.participation_state,
    )


def _identity(identity: PresentationIdentity) -> PresentationIdentityDto:
    return PresentationIdentityDto(
        executive_intelligence_id=identity.executive_intelligence_id,
        organization_id=identity.organization_id,
        workspace_id=identity.workspace_id,
        portfolio_id=identity.portfolio_id,
        portfolio_snapshot_id=identity.portfolio_snapshot_id,
        portfolio_snapshot_version=identity.portfolio_snapshot_version,
        executive_version=identity.executive_version,
        projection_completed_at=identity.projection_completed_at,
        schema_version=identity.schema_version,
        policy_version=identity.policy_version,
        source_policy_version=identity.source_policy_version,
        source_schema_version=identity.source_schema_version,
    )


def _executive_summary(summary: PresentationExecutiveSummary) -> PresentationExecutiveSummaryDto:
    return PresentationExecutiveSummaryDto(
        headline=summary.headline,
        overall_engineering_health=summary.overall_engineering_health,
        overall_health_status=summary.overall_health_status.value,
        portfolio_risk=summary.portfolio_risk,
        portfolio_risk_status=summary.portfolio_risk_status.value,
        modernization_outlook=summary.modernization_outlook,
        major_strengths=list(summary.major_strengths),
        major_weaknesses=list(summary.major_weaknesses),
        highest_priority_recommendations=list(summary.highest_priority_recommendations),
        confidence_statement=summary.confidence_statement,
        coverage_statement=summary.coverage_statement,
        limitations=list(summary.limitations),
    )


def _cto_summary(summary: PresentationCtoSummary) -> PresentationCtoSummaryDto:
    return PresentationCtoSummaryDto(
        engineering_health=_kpi(summary.engineering_health),
        architecture_maturity=_kpi(summary.architecture_maturity),
        technical_debt=_kpi(summary.technical_debt),
        security_posture=_kpi(summary.security_posture),
        dependency_health=_kpi(summary.dependency_health),
        technology_standardization=_kpi(summary.technology_standardization),
        modernization_readiness=_kpi(summary.modernization_readiness),
        cloud_adoption=_kpi(summary.cloud_adoption),
        ai_readiness=_kpi(summary.ai_readiness),
        critical_findings=[_finding(item) for item in summary.critical_findings],
        strategic_priorities=[_recommendation(item) for item in summary.strategic_priorities],
        limitations=list(summary.limitations),
    )


def _scorecard(scorecard: PresentationScorecard) -> PresentationScorecardDto:
    return PresentationScorecardDto(
        title=scorecard.title,
        cards=[_kpi(item) for item in scorecard.cards],
    )


def _confidence(summary: PresentationConfidenceSummary) -> PresentationConfidenceSummaryDto:
    return PresentationConfidenceSummaryDto(
        overall_confidence_score=summary.overall_confidence_score,
        overall_confidence=summary.overall_confidence,
        overall_confidence_band=(
            summary.overall_confidence_band.value
            if summary.overall_confidence_band is not None
            else None
        ),
        metric_confidence_average=summary.metric_confidence_average,
        finding_confidence_average=summary.finding_confidence_average,
        recommendation_confidence_average=summary.recommendation_confidence_average,
        low_confidence_metric_keys=list(summary.low_confidence_metric_keys),
        limitations=list(summary.limitations),
    )


def _coverage(summary: PresentationCoverageSummary) -> PresentationCoverageSummaryDto:
    return PresentationCoverageSummaryDto(
        assessment_coverage_score=summary.assessment_coverage_score,
        repository_coverage_score=summary.repository_coverage_score,
        assessment_coverage=summary.assessment_coverage,
        repository_coverage=summary.repository_coverage,
        metric_coverage_average=summary.metric_coverage_average,
        incomplete_metric_keys=list(summary.incomplete_metric_keys),
        limitations=list(summary.limitations),
    )


def _trend(point: PresentationTrendPoint) -> PresentationTrendPointDto:
    return PresentationTrendPointDto(
        metric_key=point.metric_key.value,
        current_value=point.current_value,
        snapshot_timestamp=point.snapshot_timestamp,
        portfolio_snapshot_id=point.portfolio_snapshot_id,
        executive_intelligence_id=point.executive_intelligence_id,
        comparison_metadata=dict(point.comparison_metadata),
        direction=point.direction.value,
    )


def presentation_response(model: ExecutivePresentationModel) -> ExecutivePresentationResponse:
    return ExecutivePresentationResponse(
        identity=_identity(model.identity),
        executive_summary=_executive_summary(model.executive_summary),
        cto_summary=_cto_summary(model.cto_summary),
        portfolio_scorecard=_scorecard(model.portfolio_scorecard),
        kpi_cards=[_kpi(item) for item in model.kpi_cards],
        portfolio_health=_kpi(model.portfolio_health),
        portfolio_risk=_kpi(model.portfolio_risk),
        modernization_readiness=_kpi(model.modernization_readiness),
        technology_landscape=_tech_landscape(model.technology_landscape),
        architecture_posture=_kpi(model.architecture_posture),
        technical_debt_posture=_kpi(model.technical_debt_posture),
        security_posture=_kpi(model.security_posture),
        dependency_posture=_kpi(model.dependency_posture),
        cloud_posture=_kpi(model.cloud_posture),
        ai_readiness=_kpi(model.ai_readiness),
        engineering_strengths=[_strength(item) for item in model.engineering_strengths],
        engineering_weaknesses=[_strength(item) for item in model.engineering_weaknesses],
        findings=[_finding(item) for item in model.findings],
        recommendations=[_recommendation(item) for item in model.recommendations],
        observations=[_observation(item) for item in model.observations],
        confidence_summary=_confidence(model.confidence_summary),
        coverage_summary=_coverage(model.coverage_summary),
        limitations_and_assumptions=list(model.limitations_and_assumptions),
        repository_references=[_repo(item) for item in model.repository_references],
        trend_ready_metrics=[_trend(item) for item in model.trend_ready_metrics],
    )


def presentation_executive_summary_response(
    model: ExecutivePresentationModel,
) -> PresentationExecutiveSummaryDto:
    return _executive_summary(model.executive_summary)


def presentation_cto_summary_response(
    model: ExecutivePresentationModel,
) -> PresentationCtoSummaryDto:
    return _cto_summary(model.cto_summary)


def presentation_scorecard_response(
    model: ExecutivePresentationModel,
) -> PresentationScorecardDto:
    return _scorecard(model.portfolio_scorecard)
