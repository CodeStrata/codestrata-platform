"""Read-only Executive Presentation models (on-read projections)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from codestrata_platform.domain.executive_intelligence.lifecycle import (
    ExecutiveConfidenceBand,
    ExecutiveFindingCategory,
    ExecutiveImpactBand,
    ExecutiveMetricKey,
    ExecutiveRecommendationTheme,
)


class PresentationScoreStatus(StrEnum):
    """Deterministic status labels derived from score bands."""

    CRITICAL = "critical"
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class PresentationTrendDirection(StrEnum):
    """Trend direction placeholders — never invented without audited history."""

    UNKNOWN = "unknown"
    UP = "up"
    DOWN = "down"
    FLAT = "flat"


EXECUTIVE_PRESENTATION_SCHEMA_VERSION = "executive-presentation-v1"
EXECUTIVE_PRESENTATION_POLICY_VERSION = "executive-presentation-policy-v1"


@dataclass(frozen=True, slots=True)
class PresentationIdentity:
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


@dataclass(frozen=True, slots=True)
class PresentationKpiCard:
    identifier: str
    metric_key: ExecutiveMetricKey
    title: str
    score: int
    status: PresentationScoreStatus
    confidence: float
    confidence_band: ExecutiveConfidenceBand
    coverage: float
    description: str
    calculation_disclosure: str
    limitations: tuple[str, ...]
    drill_down_reference: str
    inputs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PresentationScorecard:
    title: str
    cards: tuple[PresentationKpiCard, ...]


@dataclass(frozen=True, slots=True)
class PresentationFinding:
    finding_id: str
    title: str
    category: ExecutiveFindingCategory
    severity: ExecutiveImpactBand
    description: str
    affected_repository_ids: tuple[str, ...]
    confidence: float
    confidence_band: ExecutiveConfidenceBand
    evidence_references: tuple[str, ...]
    source_references: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PresentationRecommendation:
    recommendation_id: str
    title: str
    theme: ExecutiveRecommendationTheme
    priority_score: int
    rationale: str
    expected_impact: ExecutiveImpactBand
    affected_repository_ids: tuple[str, ...]
    confidence: float
    confidence_band: ExecutiveConfidenceBand
    supporting_finding_ids: tuple[str, ...]
    source_references: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PresentationObservation:
    observation_key: str
    title: str
    summary: str
    related_metric_keys: tuple[str, ...]
    related_finding_ids: tuple[str, ...]
    confidence: float
    confidence_band: ExecutiveConfidenceBand


@dataclass(frozen=True, slots=True)
class PresentationStrengthWeaknessItem:
    key: str
    title: str
    summary: str
    related_metric_keys: tuple[str, ...]
    related_finding_ids: tuple[str, ...]
    confidence: float
    confidence_band: ExecutiveConfidenceBand
    definitive: bool


@dataclass(frozen=True, slots=True)
class PresentationTechnologyItem:
    key: str
    title: str
    category: str
    summary: str
    affected_repository_ids: tuple[str, ...]
    confidence: float
    evidence_references: tuple[str, ...]
    source_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PresentationTechnologyLandscape:
    fragmentation: tuple[PresentationTechnologyItem, ...]
    duplicated_stacks: tuple[PresentationTechnologyItem, ...]
    unsupported_technologies: tuple[PresentationTechnologyItem, ...]
    standardization_opportunities: tuple[PresentationTechnologyItem, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PresentationRepositoryReference:
    repository_id: str
    display_name: str | None
    snapshot_id: str | None
    status: str | None
    participation_state: str | None


@dataclass(frozen=True, slots=True)
class PresentationConfidenceSummary:
    overall_confidence_score: int | None
    overall_confidence: float | None
    overall_confidence_band: ExecutiveConfidenceBand | None
    metric_confidence_average: float
    finding_confidence_average: float
    recommendation_confidence_average: float
    low_confidence_metric_keys: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PresentationCoverageSummary:
    assessment_coverage_score: int | None
    repository_coverage_score: int | None
    assessment_coverage: float | None
    repository_coverage: float | None
    metric_coverage_average: float
    incomplete_metric_keys: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PresentationTrendPoint:
    metric_key: ExecutiveMetricKey
    current_value: int
    snapshot_timestamp: datetime | None
    portfolio_snapshot_id: str
    executive_intelligence_id: str
    comparison_metadata: dict[str, str]
    direction: PresentationTrendDirection


@dataclass(frozen=True, slots=True)
class PresentationExecutiveSummary:
    headline: str
    overall_engineering_health: int
    overall_health_status: PresentationScoreStatus
    portfolio_risk: int
    portfolio_risk_status: PresentationScoreStatus
    modernization_outlook: str
    major_strengths: tuple[str, ...]
    major_weaknesses: tuple[str, ...]
    highest_priority_recommendations: tuple[str, ...]
    confidence_statement: str
    coverage_statement: str
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PresentationCtoSummary:
    engineering_health: PresentationKpiCard
    architecture_maturity: PresentationKpiCard
    technical_debt: PresentationKpiCard
    security_posture: PresentationKpiCard
    dependency_health: PresentationKpiCard
    technology_standardization: PresentationKpiCard
    modernization_readiness: PresentationKpiCard
    cloud_adoption: PresentationKpiCard
    ai_readiness: PresentationKpiCard
    critical_findings: tuple[PresentationFinding, ...]
    strategic_priorities: tuple[PresentationRecommendation, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExecutivePresentationModel:
    """Complete customer-facing Executive Presentation projection."""

    identity: PresentationIdentity
    executive_summary: PresentationExecutiveSummary
    cto_summary: PresentationCtoSummary
    portfolio_scorecard: PresentationScorecard
    kpi_cards: tuple[PresentationKpiCard, ...]
    portfolio_health: PresentationKpiCard
    portfolio_risk: PresentationKpiCard
    modernization_readiness: PresentationKpiCard
    technology_landscape: PresentationTechnologyLandscape
    architecture_posture: PresentationKpiCard
    technical_debt_posture: PresentationKpiCard
    security_posture: PresentationKpiCard
    dependency_posture: PresentationKpiCard
    cloud_posture: PresentationKpiCard
    ai_readiness: PresentationKpiCard
    engineering_strengths: tuple[PresentationStrengthWeaknessItem, ...]
    engineering_weaknesses: tuple[PresentationStrengthWeaknessItem, ...]
    findings: tuple[PresentationFinding, ...]
    recommendations: tuple[PresentationRecommendation, ...]
    observations: tuple[PresentationObservation, ...]
    confidence_summary: PresentationConfidenceSummary
    coverage_summary: PresentationCoverageSummary
    limitations_and_assumptions: tuple[str, ...]
    repository_references: tuple[PresentationRepositoryReference, ...]
    trend_ready_metrics: tuple[PresentationTrendPoint, ...]
