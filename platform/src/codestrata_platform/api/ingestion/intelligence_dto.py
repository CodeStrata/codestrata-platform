"""Intelligence ingestion DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IntelligenceProcessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_ids: list[str] | None = None
    parser_version: str = Field(default="1.0.0", min_length=1, max_length=64)


class IntelligenceProcessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intelligence_id: str
    assessment_id: str
    revision: int
    status: str
    created: bool
    idempotent: bool
    finding_count: int
    metric_count: int
    recommendation_count: int
    failure_reason: str | None = None


class IntelligenceDetailsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intelligence_id: str
    organization_id: str
    workspace_id: str
    repository_id: str
    assessment_id: str
    engine_assessment_id: str
    schema_version: str
    parser_version: str
    revision: int
    idempotency_key: str
    status: str
    source_artifact_ids: list[str]
    finding_count: int
    metric_count: int
    recommendation_count: int
    failure_reason: str | None
    diagnostics: list[str]
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
