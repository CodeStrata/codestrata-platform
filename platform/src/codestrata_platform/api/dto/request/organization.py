"""Organization request DTOs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CreateOrganizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=1,
        max_length=512,
        description="Organization display name",
        examples=["Acme Engineering"],
    )


class UpdateOrganizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=512,
        description="New display name when renaming",
    )
    activate: bool | None = Field(
        default=None,
        description="Set true to reactivate an archived organization",
    )