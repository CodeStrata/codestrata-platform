"""Executive Intelligence API DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BuildExecutiveIntelligenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    portfolio_snapshot_id: str | None = Field(default=None, min_length=1)


class TenantScopeQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)


class ExecutiveIntelligenceSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_intelligence_id: str
    organization_id: str
    workspace_id: str
    portfolio_id: str
    portfolio_snapshot_id: str
    portfolio_snapshot_version: int
    version: int
    status: str
    projection_key: str
    schema_version: str
    policy_version: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    superseded_at: datetime | None
    failure_reason: str | None
    metric_count: int
    finding_count: int
    recommendation_count: int
    observation_count: int


class ExecutiveMetricResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_id: str
    key: str
    score: int
    confidence: float
    confidence_band: str
    coverage: float
    inputs: list[str]
    calculation_rule: str
    limitations: list[str]
    policy_version: str


class ExecutiveFindingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str
    category: str
    title: str
    summary: str
    severity_band: str
    confidence: float
    confidence_band: str
    affected_repository_ids: list[str]
    source_references: list[str]
    evidence: list[str]
    policy_version: str


class ExecutiveRecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation_id: str
    theme: str
    title: str
    rationale: str
    affected_repository_ids: list[str]
    confidence: float
    confidence_band: str
    expected_impact: str
    source_references: list[str]
    priority_score: int
    policy_version: str


class StrategicObservationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation_key: str
    title: str
    summary: str
    related_metric_keys: list[str]
    related_finding_ids: list[str]
    confidence: float
    confidence_band: str


class ExecutiveIntelligenceDetailsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: ExecutiveIntelligenceSummaryResponse
    metrics: list[ExecutiveMetricResponse]
    findings: list[ExecutiveFindingResponse]
    recommendations: list[ExecutiveRecommendationResponse]
    observations: list[StrategicObservationResponse]
    limitations: list[str]


class ExecutiveMetricsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: ExecutiveIntelligenceSummaryResponse
    metrics: list[ExecutiveMetricResponse]


class ExecutiveFindingsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: ExecutiveIntelligenceSummaryResponse
    findings: list[ExecutiveFindingResponse]


class ExecutiveRecommendationsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: ExecutiveIntelligenceSummaryResponse
    recommendations: list[ExecutiveRecommendationResponse]


class ExecutiveIntelligencePageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ExecutiveIntelligenceSummaryResponse]
    total: int
    offset: int
    limit: int
