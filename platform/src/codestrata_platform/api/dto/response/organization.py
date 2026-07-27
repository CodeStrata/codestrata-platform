"""Organization response DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
