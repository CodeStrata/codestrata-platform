"""Assessment request DTOs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GeneratedReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_type: str = Field(min_length=1, max_length=64)
    location: str = Field(min_length=1, max_length=2048)


class AssessmentReferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_uri: str = Field(min_length=1, max_length=2048)
    label: str | None = Field(default=None, max_length=256)


class RegisterAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_id: str = Field(min_length=1, max_length=160)
    workspace_id: str = Field(min_length=1, max_length=160)
    engine_version: str = Field(min_length=1, max_length=64)
    assessment_version: str = Field(min_length=1, max_length=64)


class CompleteAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_reports: list[GeneratedReportRequest] = Field(default_factory=list)
    references: list[AssessmentReferenceRequest] = Field(default_factory=list)


class FailAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=2000)
