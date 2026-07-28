"""Portfolio API DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreatePortfolioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=4000)
    max_repositories: int | None = Field(default=None, ge=1, le=2000)


class UpdatePortfolioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    name: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=4000)


class AddRepositoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    repository_id: str = Field(min_length=1)
    criticality: str = "unspecified"
    business_capability: str | None = Field(default=None, max_length=256)
    owner_reference: str | None = Field(default=None, max_length=256)
    lifecycle_status: str | None = Field(default=None, max_length=64)
    tags: list[str] = Field(default_factory=list, max_length=32)


class BuildSnapshotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    aggregation_policy_version: str | None = Field(default=None, max_length=64)


class TenantScopeQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)


class PortfolioMembershipResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    membership_id: str
    repository_id: str
    criticality: str
    business_capability: str | None
    owner_reference: str | None
    lifecycle_status: str | None
    tags: list[str]
    added_at: datetime
    removed_at: datetime | None
    active: bool


class PortfolioSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    portfolio_id: str
    organization_id: str
    workspace_id: str
    name: str
    description: str | None
    status: str
    repository_count: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


class PortfolioDetailsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    portfolio: PortfolioSummaryResponse
    memberships: list[PortfolioMembershipResponse]


class PortfolioSnapshotSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    portfolio_snapshot_id: str
    portfolio_id: str
    organization_id: str
    workspace_id: str
    snapshot_version: int
    status: str
    projection_key: str
    aggregation_policy_version: str
    repository_count: int
    available_repository_count: int
    unavailable_repository_count: int
    created_at: datetime
    completed_at: datetime | None
    superseded_at: datetime | None
    failure_reason: str | None


class PortfolioRepositorySelectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_id: str
    availability_status: str
    criticality: str
    assessment_id: str | None
    engineering_snapshot_id: str | None
    engineering_snapshot_version: int | None
    knowledge_graph_id: str | None
    knowledge_graph_version: int | None
    selected_at: datetime


class PortfolioEnvelopeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    portfolio_id: str
    portfolio_snapshot_id: str
    portfolio_snapshot_version: int
    generated_at: datetime
    aggregation_policy_version: str
    selected_repository_count: int
    unavailable_repository_count: int
    source_snapshot_references: list[str]


class PortfolioSnapshotDetailsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot: PortfolioSnapshotSummaryResponse
    repository_selections: list[PortfolioRepositorySelectionResponse]
    envelope: PortfolioEnvelopeResponse


class PageResponse[T](BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[T]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1)