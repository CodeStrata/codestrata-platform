"""Intelligence query response DTOs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FindingSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str
    assessment_id: str
    category: str
    rule_id: str
    title: str
    severity: str
    confidence: float


class FindingDetailsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str
    assessment_id: str
    category: str
    rule_id: str
    title: str
    summary: str
    severity: str
    confidence: float
    production_scope: str | None = None
    affected_component: str | None = None
    affected_path_reference: str | None = None
    remediation_reference: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    evidence_references: list[dict[str, object]] = Field(default_factory=list)


class MetricDetailsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    kind: str
    value: str
    unit: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class RecommendationDetailsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation_id: str
    assessment_id: str
    category: str
    title: str
    rationale: str
    priority: str
    effort: str | None = None
    impact: str | None = None
    roadmap_horizon: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    related_finding_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
