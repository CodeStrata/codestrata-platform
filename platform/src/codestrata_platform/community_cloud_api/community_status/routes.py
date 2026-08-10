"""Route registration for Community Status (Slice 17.23)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.community_status.handler import (
    handle_community_status,
)
from codestrata_platform.community_cloud_api.community_status.service import (
    CommunityStatusService,
)
from codestrata_platform.community_cloud_api.constants import API_VERSION_V1
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.registry import RouteRegistry, RouteSpec
from codestrata_platform.community_cloud_api.validation.models import NO_BODY_SCHEMA
from starlette.responses import Response

STATUS_PATH = "/community/status"
STATUS_ROUTE_NAME = "community.status.get"


def register_community_status_routes(
    registry: RouteRegistry,
    *,
    service: CommunityStatusService | None = None,
) -> None:
    active = service or CommunityStatusService()

    def _handler(context: RequestContext) -> Response:
        return handle_community_status(context, service=active)

    registry.register(
        RouteSpec(
            version=API_VERSION_V1,
            method="GET",
            path=STATUS_PATH,
            name=STATUS_ROUTE_NAME,
            rate_limit_group="health",
            authentication_group="public",
        ),
        handler=_handler,
        request_schema=NO_BODY_SCHEMA,
    )


__all__ = [
    "STATUS_PATH",
    "STATUS_ROUTE_NAME",
    "register_community_status_routes",
]
