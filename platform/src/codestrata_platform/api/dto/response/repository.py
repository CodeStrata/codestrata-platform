"""Repository response DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RepositorySummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    workspace_id: str
    organization_id: str
    display_name: str
    provider: str
    repository_url: str
    status: str
    visibility: str


class RepositoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    workspace_id: str
    organization_id: str
    display_name: str
    provider: str
    repository_url: str
    default_branch: str
    visibility: str
    description: str | None
    status: str
    metadata: dict[str, str]
    created_at: datetime
    updated_at: datetime
