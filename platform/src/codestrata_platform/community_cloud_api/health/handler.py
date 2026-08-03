"""Health endpoint handler — process availability only."""

from __future__ import annotations

from starlette.responses import Response

from codestrata_platform.community_cloud_api.constants import API_VERSION_V1
from codestrata_platform.community_cloud_api.errors import ERROR_INTERNAL
from codestrata_platform.community_cloud_api.health.models import CommunityHealthResponse
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.serialization import (
    build_error_response,
    build_json_response,
)

_CACHE_CONTROL_NO_STORE = "no-store"


def handle_health(context: RequestContext) -> Response:
    """Return a deterministic healthy response for GET /api/v1/health.

    Success means the ASGI app started, the v1 registry loaded, this handler
    ran, and serialization succeeded. It does not verify storage, queues,
    auth configuration, or downstream providers.
    """

    try:
        payload = CommunityHealthResponse.build()
        return build_json_response(
            payload,
            status_code=200,
            api_version=API_VERSION_V1,
            # Echo transport request id when present; never put it in the body.
            request_id=context.request_id,
            extra_headers={"Cache-Control": _CACHE_CONTROL_NO_STORE},
        )
    except Exception:  # noqa: BLE001 - never leak construction failures
        return build_error_response(
            ERROR_INTERNAL,
            http_status=500,
            api_version=API_VERSION_V1,
            request_id=context.request_id,
        )
