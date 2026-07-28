"""Engineering inventory response DTOs (stable Platform contracts)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EngineeringTechnologyItemDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    technology_id: str = Field(min_length=1)
    canonical_key: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    category: str = Field(min_length=1)


class EngineeringFindingItemDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(min_length=1)
    source_finding_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    title: str = Field(min_length=1)
    rule_id: str = Field(min_length=1)
    confidence: float


class EngineeringRecommendationItemDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation_id: str = Field(min_length=1)
    source_recommendation_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    title: str = Field(min_length=1)
    priority: str = Field(min_length=1)
    related_finding_ids: list[str] = Field(default_factory=list)


class EngineeringMetricItemDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    value: str
    unit: str | None = None
