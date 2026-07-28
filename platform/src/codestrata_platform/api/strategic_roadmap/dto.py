"""Strategic Portfolio Roadmap API DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RoadmapIdentityDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_intelligence_id: str
    organization_id: str
    workspace_id: str
    portfolio_id: str
    portfolio_snapshot_id: str
    portfolio_snapshot_version: int
    executive_version: int
    projection_completed_at: datetime | None
    schema_version: str
    policy_version: str
    source_policy_version: str
    source_schema_version: str


class RoadmapInitiativeDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    initiative_id: str
    title: str
    category: str
    description: str
    rationale: str
    affected_repository_ids: list[str]
    supporting_finding_ids: list[str]
    supporting_recommendation_ids: list[str]
    expected_impact: str
    confidence: float
    confidence_band: str
    coverage: float
    limitations: list[str]
    priority: int
    effort_band: str
    sequencing_wave: str
    related_initiative_ids: list[str]
    depends_on_initiative_ids: list[str]
    priority_inputs: list[str]
    effort_rule: str
    wave_rule: str


class RoadmapWaveBucketDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wave: str
    title: str
    description: str
    initiative_ids: list[str]
    initiative_count: int


class RoadmapSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    initiative_count: int
    effort_distribution: list[list[object]]
    wave_distribution: list[list[object]]
    category_distribution: list[list[object]]
    portfolio_investment_themes: list[str]
    strategic_observations: list[str]
    limitations: list[str]


class StrategicRoadmapResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identity: RoadmapIdentityDto
    summary: RoadmapSummaryDto
    initiatives: list[RoadmapInitiativeDto]
    waves: list[RoadmapWaveBucketDto]
    limitations: list[str]


class RoadmapInitiativesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identity: RoadmapIdentityDto
    initiatives: list[RoadmapInitiativeDto]
    total: int


class RoadmapWavesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identity: RoadmapIdentityDto
    waves: list[RoadmapWaveBucketDto]


class RoadmapSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identity: RoadmapIdentityDto
    summary: RoadmapSummaryDto
