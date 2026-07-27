"""Assessment response DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    repository_id: str
    workspace_id: str
    engine_version: str
    assessment_version: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    failure_reason: str | None
    report_count: int
    created_at: datetime
    updated_at: datetime
