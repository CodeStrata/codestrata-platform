"""Strategic Portfolio Roadmap API mappers."""

from __future__ import annotations

from codestrata_platform.api.strategic_roadmap.dto import (
    RoadmapIdentityDto,
    RoadmapInitiativeDto,
    RoadmapInitiativesResponse,
    RoadmapSummaryDto,
    RoadmapSummaryResponse,
    RoadmapWaveBucketDto,
    RoadmapWavesResponse,
    StrategicRoadmapResponse,
)
from codestrata_platform.application.strategic_roadmap.models import (
    RoadmapIdentity,
    RoadmapInitiative,
    RoadmapSummary,
    RoadmapWaveBucket,
    StrategicRoadmapModel,
)


def _identity(identity: RoadmapIdentity) -> RoadmapIdentityDto:
    return RoadmapIdentityDto(
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


def _initiative(item: RoadmapInitiative) -> RoadmapInitiativeDto:
    return RoadmapInitiativeDto(
        initiative_id=item.initiative_id,
        title=item.title,
        category=item.category.value,
        description=item.description,
        rationale=item.rationale,
        affected_repository_ids=list(item.affected_repository_ids),
        supporting_finding_ids=list(item.supporting_finding_ids),
        supporting_recommendation_ids=list(item.supporting_recommendation_ids),
        expected_impact=item.expected_impact,
        confidence=item.confidence,
        confidence_band=item.confidence_band,
        coverage=item.coverage,
        limitations=list(item.limitations),
        priority=item.priority,
        effort_band=item.effort_band.value,
        sequencing_wave=item.sequencing_wave.value,
        related_initiative_ids=list(item.related_initiative_ids),
        depends_on_initiative_ids=list(item.depends_on_initiative_ids),
        priority_inputs=list(item.priority_inputs),
        effort_rule=item.effort_rule,
        wave_rule=item.wave_rule,
    )


def _wave(item: RoadmapWaveBucket) -> RoadmapWaveBucketDto:
    return RoadmapWaveBucketDto(
        wave=item.wave.value,
        title=item.title,
        description=item.description,
        initiative_ids=list(item.initiative_ids),
        initiative_count=item.initiative_count,
    )


def _summary(summary: RoadmapSummary) -> RoadmapSummaryDto:
    return RoadmapSummaryDto(
        initiative_count=summary.initiative_count,
        effort_distribution=[list(item) for item in summary.effort_distribution],
        wave_distribution=[list(item) for item in summary.wave_distribution],
        category_distribution=[list(item) for item in summary.category_distribution],
        portfolio_investment_themes=list(summary.portfolio_investment_themes),
        strategic_observations=list(summary.strategic_observations),
        limitations=list(summary.limitations),
    )


def roadmap_response(model: StrategicRoadmapModel) -> StrategicRoadmapResponse:
    return StrategicRoadmapResponse(
        identity=_identity(model.identity),
        summary=_summary(model.summary),
        initiatives=[_initiative(item) for item in model.initiatives],
        waves=[_wave(item) for item in model.waves],
        limitations=list(model.limitations),
    )


def initiatives_response(
    model: StrategicRoadmapModel,
    *,
    category: str | None = None,
    wave: str | None = None,
) -> RoadmapInitiativesResponse:
    items = model.initiatives
    if category is not None:
        items = tuple(item for item in items if item.category.value == category)
    if wave is not None:
        items = tuple(item for item in items if item.sequencing_wave.value == wave)
    return RoadmapInitiativesResponse(
        identity=_identity(model.identity),
        initiatives=[_initiative(item) for item in items],
        total=len(items),
    )


def waves_response(model: StrategicRoadmapModel) -> RoadmapWavesResponse:
    return RoadmapWavesResponse(
        identity=_identity(model.identity),
        waves=[_wave(item) for item in model.waves],
    )


def summary_response(model: StrategicRoadmapModel) -> RoadmapSummaryResponse:
    return RoadmapSummaryResponse(
        identity=_identity(model.identity),
        summary=_summary(model.summary),
    )
