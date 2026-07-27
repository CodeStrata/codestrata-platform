"""Organization request DTOs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CreateOrganizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=512)


class UpdateOrganizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=512)
    activate: bool | None = None
