"""Ingestion request/response DTOs for Engine → Platform publishing."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class IngestRepositoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: str = Field(min_length=1, max_length=160)
    workspace_id: str = Field(min_length=1, max_length=160)
    display_name: str = Field(min_length=1, max_length=512)
    provider: str = Field(default="other", min_length=1, max_length=64)
    repository_url: HttpUrl
    default_branch: str = Field(default="main", min_length=1, max_length=256)
    visibility: str = Field(default="private", min_length=1, max_length=32)
    description: str | None = Field(default=None, max_length=4000)
    engine_repository_id: str | None = Field(default=None, max_length=160)
    metadata: dict[str, str] | None = None


class IngestRepositoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_id: str
    workspace_id: str
    organization_id: str
    display_name: str
    repository_url: str
    status: str
    created: bool


class IngestAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_id: str = Field(min_length=1, max_length=160)
    workspace_id: str = Field(min_length=1, max_length=160)
    engine_assessment_id: str = Field(min_length=1, max_length=160)
    engine_version: str = Field(min_length=1, max_length=64)
    assessment_version: str = Field(min_length=1, max_length=64)
    started_at: datetime | None = None
    technology_summary: str | None = Field(default=None, max_length=4000)
    metadata: dict[str, str] | None = None


class IngestAssessmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assessment_id: str
    repository_id: str
    workspace_id: str
    engine_assessment_id: str
    engine_version: str
    assessment_version: str
    status: str


class IngestReportPointer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_type: str = Field(min_length=1, max_length=64)
    location: str = Field(min_length=1, max_length=2048)


class IngestReferencePointer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_uri: str = Field(min_length=1, max_length=2048)
    label: str | None = Field(default=None, max_length=256)


class IngestCompleteAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_reports: list[IngestReportPointer] = Field(default_factory=list)
    references: list[IngestReferencePointer] = Field(default_factory=list)
    completed_at: datetime | None = None


class IngestFailAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=2000)


class RegisterArtifactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    engine_assessment_id: str = Field(min_length=1, max_length=160)
    artifact_type: str = Field(min_length=1, max_length=64)
    format: str = Field(min_length=1, max_length=32)
    schema_version: str = Field(min_length=1, max_length=64)
    checksum: str = Field(min_length=64, max_length=64, pattern=r"^[a-fA-F0-9]{64}$")
    size_bytes: int = Field(gt=0, le=104_857_600)
    metadata: dict[str, str] | None = None


class RegisterArtifactResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    assessment_id: str
    artifact_type: str
    checksum: str
    status: str
    version: int
    created: bool


class ArtifactSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    assessment_id: str
    artifact_type: str
    format: str
    checksum: str
    size_bytes: int
    status: str
    version: int
    schema_version: str


class ArtifactDetailsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    organization_id: str
    workspace_id: str
    repository_id: str
    assessment_id: str
    engine_assessment_id: str
    artifact_type: str
    format: str
    schema_version: str
    checksum: str
    size_bytes: int
    status: str
    version: int
    metadata: dict[str, str]
    storage_key: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    failure_reason: str | None


class UploadArtifactResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    status: str
    checksum: str
    size_bytes: int
    storage_key: str | None


class FailArtifactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=2000)
