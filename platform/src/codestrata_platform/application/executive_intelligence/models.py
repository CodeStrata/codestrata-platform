"""Executive Intelligence application read models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.executive_intelligence.lifecycle import ExecutiveIntelligenceStatus
from codestrata_platform.domain.executive_intelligence.models import (
    ExecutiveFinding,
    ExecutiveMetric,
    ExecutiveRecommendation,
    StrategicObservation,
)


@dataclass(frozen=True, slots=True)
class ExecutiveIntelligenceSummary:
    executive_intelligence_id: str
    organization_id: str
    workspace_id: str
    portfolio_id: str
    portfolio_snapshot_id: str
    portfolio_snapshot_version: int
    version: int
    status: ExecutiveIntelligenceStatus
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


@dataclass(frozen=True, slots=True)
class ExecutiveIntelligenceDetails:
    summary: ExecutiveIntelligenceSummary
    metrics: tuple[ExecutiveMetric, ...]
    findings: tuple[ExecutiveFinding, ...]
    recommendations: tuple[ExecutiveRecommendation, ...]
    observations: tuple[StrategicObservation, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExecutiveMetricsModel:
    summary: ExecutiveIntelligenceSummary
    metrics: tuple[ExecutiveMetric, ...]


@dataclass(frozen=True, slots=True)
class ExecutiveFindingsModel:
    summary: ExecutiveIntelligenceSummary
    findings: tuple[ExecutiveFinding, ...]


@dataclass(frozen=True, slots=True)
class ExecutiveRecommendationsModel:
    summary: ExecutiveIntelligenceSummary
    recommendations: tuple[ExecutiveRecommendation, ...]
