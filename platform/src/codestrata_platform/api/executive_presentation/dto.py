"""Executive Presentation API DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PresentationIdentityDto(BaseModel):
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


class PresentationKpiCardDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identifier: str
    metric_key: str
    title: str
    score: int
    status: str
    confidence: float
    confidence_band: str
    coverage: float
    description: str
    calculation_disclosure: str
    limitations: list[str]
    drill_down_reference: str
    inputs: list[str]


class PresentationScorecardDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    cards: list[PresentationKpiCardDto]


class PresentationFindingDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str
    title: str
    category: str
    severity: str
    description: str
    affected_repository_ids: list[str]
    confidence: float
    confidence_band: str
    evidence_references: list[str]
    source_references: list[str]
    limitations: list[str]


class PresentationRecommendationDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation_id: str
    title: str
    theme: str
    priority_score: int
    rationale: str
    expected_impact: str
    affected_repository_ids: list[str]
    confidence: float
    confidence_band: str
    supporting_finding_ids: list[str]
    source_references: list[str]
    limitations: list[str]


class PresentationObservationDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation_key: str
    title: str
    summary: str
    related_metric_keys: list[str]
    related_finding_ids: list[str]
    confidence: float
    confidence_band: str


class PresentationStrengthWeaknessItemDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    title: str
    summary: str
    related_metric_keys: list[str]
    related_finding_ids: list[str]
    confidence: float
    confidence_band: str
    definitive: bool


class PresentationTechnologyItemDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    title: str
    category: str
    summary: str
    affected_repository_ids: list[str]
    confidence: float
    evidence_references: list[str]
    source_references: list[str]


class PresentationTechnologyLandscapeDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fragmentation: list[PresentationTechnologyItemDto]
    duplicated_stacks: list[PresentationTechnologyItemDto]
    unsupported_technologies: list[PresentationTechnologyItemDto]
    standardization_opportunities: list[PresentationTechnologyItemDto]
    limitations: list[str]


class PresentationRepositoryReferenceDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_id: str
    display_name: str | None = None
    snapshot_id: str | None = None
    status: str | None = None
    participation_state: str | None = None


class PresentationConfidenceSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_confidence_score: int | None
    overall_confidence: float | None
    overall_confidence_band: str | None
    metric_confidence_average: float
    finding_confidence_average: float
    recommendation_confidence_average: float
    low_confidence_metric_keys: list[str]
    limitations: list[str]


class PresentationCoverageSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assessment_coverage_score: int | None
    repository_coverage_score: int | None
    assessment_coverage: float | None
    repository_coverage: float | None
    metric_coverage_average: float
    incomplete_metric_keys: list[str]
    limitations: list[str]


class PresentationTrendPointDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_key: str
    current_value: int
    snapshot_timestamp: datetime | None
    portfolio_snapshot_id: str
    executive_intelligence_id: str
    comparison_metadata: dict[str, str]
    direction: str


class PresentationExecutiveSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headline: str
    overall_engineering_health: int
    overall_health_status: str
    portfolio_risk: int
    portfolio_risk_status: str
    modernization_outlook: str
    major_strengths: list[str]
    major_weaknesses: list[str]
    highest_priority_recommendations: list[str]
    confidence_statement: str
    coverage_statement: str
    limitations: list[str]


class PresentationCtoSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    engineering_health: PresentationKpiCardDto
    architecture_maturity: PresentationKpiCardDto
    technical_debt: PresentationKpiCardDto
    security_posture: PresentationKpiCardDto
    dependency_health: PresentationKpiCardDto
    technology_standardization: PresentationKpiCardDto
    modernization_readiness: PresentationKpiCardDto
    cloud_adoption: PresentationKpiCardDto
    ai_readiness: PresentationKpiCardDto
    critical_findings: list[PresentationFindingDto]
    strategic_priorities: list[PresentationRecommendationDto]
    limitations: list[str]


class ExecutivePresentationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identity: PresentationIdentityDto
    executive_summary: PresentationExecutiveSummaryDto
    cto_summary: PresentationCtoSummaryDto
    portfolio_scorecard: PresentationScorecardDto
    kpi_cards: list[PresentationKpiCardDto]
    portfolio_health: PresentationKpiCardDto
    portfolio_risk: PresentationKpiCardDto
    modernization_readiness: PresentationKpiCardDto
    technology_landscape: PresentationTechnologyLandscapeDto
    architecture_posture: PresentationKpiCardDto
    technical_debt_posture: PresentationKpiCardDto
    security_posture: PresentationKpiCardDto
    dependency_posture: PresentationKpiCardDto
    cloud_posture: PresentationKpiCardDto
    ai_readiness: PresentationKpiCardDto
    engineering_strengths: list[PresentationStrengthWeaknessItemDto]
    engineering_weaknesses: list[PresentationStrengthWeaknessItemDto]
    findings: list[PresentationFindingDto]
    recommendations: list[PresentationRecommendationDto]
    observations: list[PresentationObservationDto]
    confidence_summary: PresentationConfidenceSummaryDto
    coverage_summary: PresentationCoverageSummaryDto
    limitations_and_assumptions: list[str]
    repository_references: list[PresentationRepositoryReferenceDto]
    trend_ready_metrics: list[PresentationTrendPointDto]
