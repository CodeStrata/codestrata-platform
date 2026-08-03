"""Community Cloud API health endpoint (Slice 7.2)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.health.handler import handle_health
from codestrata_platform.community_cloud_api.health.models import (
    HEALTH_SERVICE_NAME,
    HEALTH_STATUS_OK,
    CommunityHealthResponse,
)
from codestrata_platform.community_cloud_api.health.routes import (
    HEALTH_PATH,
    HEALTH_ROUTE_NAME,
    register_health_routes,
)

__all__ = [
    "HEALTH_PATH",
    "HEALTH_ROUTE_NAME",
    "HEALTH_SERVICE_NAME",
    "HEALTH_STATUS_OK",
    "CommunityHealthResponse",
    "handle_health",
    "register_health_routes",
]
