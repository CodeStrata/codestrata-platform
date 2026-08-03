"""Central health route registration for Community Cloud API v1."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.constants import API_VERSION_V1
from codestrata_platform.community_cloud_api.health.handler import handle_health
from codestrata_platform.community_cloud_api.registry import RouteRegistry, RouteSpec
from codestrata_platform.community_cloud_api.validation.models import NO_BODY_SCHEMA

HEALTH_PATH = "/health"
HEALTH_ROUTE_NAME = "health.get"


def register_health_routes(registry: RouteRegistry) -> None:
    """Register GET /health on the given registry (v1)."""

    registry.register(
        RouteSpec(
            version=API_VERSION_V1,
            method="GET",
            path=HEALTH_PATH,
            name=HEALTH_ROUTE_NAME,
            rate_limit_group="health",
            authentication_group="public",
        ),
        handler=handle_health,
        request_schema=NO_BODY_SCHEMA,
    )
