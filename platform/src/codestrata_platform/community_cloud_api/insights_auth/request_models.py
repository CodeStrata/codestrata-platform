"""Request validation models for Insights auth endpoints."""

from __future__ import annotations

from pydantic import Field

from codestrata_platform.community_cloud_api.validation.models import (
    CommunityApiRequestModel,
)


class InsightsLoginRequest(CommunityApiRequestModel):
    password: str = Field(min_length=1, max_length=256)
