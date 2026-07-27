"""Workspace request DTOs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CreateWorkspaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: str = Field(min_length=1, max_length=160)
    name: str = Field(min_length=1, max_length=512)
    description: str | None = Field(default=None, max_length=4000)


class UpdateWorkspaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=512)
    activate: bool | None = None
