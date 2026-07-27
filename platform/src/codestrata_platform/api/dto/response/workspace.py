"""Workspace response DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    organization_id: str
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime
