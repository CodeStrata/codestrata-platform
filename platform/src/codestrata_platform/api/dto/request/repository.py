"""Repository request DTOs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class RegisterRepositoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=160)
    organization_id: str = Field(min_length=1, max_length=160)
    display_name: str = Field(min_length=1, max_length=512)
    provider: str = Field(min_length=1, max_length=64)
    repository_url: HttpUrl
    default_branch: str = Field(default="main", min_length=1, max_length=256)
    visibility: str = Field(default="private", min_length=1, max_length=32)
    description: str | None = Field(default=None, max_length=4000)
    metadata: dict[str, str] | None = None


class UpdateRepositoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=512)
    metadata: dict[str, str] | None = None
