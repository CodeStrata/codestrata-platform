"""HTTP handler for GET /api/v1/community/status."""

from __future__ import annotations

from starlette.responses import Response

from codestrata_platform.community_cloud_api.community_status.service import (
    CommunityStatusService,
)
from codestrata_platform.community_cloud_api.constants import API_VERSION_V1
from codestrata_platform.community_cloud_api.errors import ERROR_INTERNAL
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.serialization import (
    build_error_response,
    build_json_response,
)

# Public website origins may call this unauthenticated GET (no credentials).
_WEBSITE_ORIGINS = frozenset(
    {
        "https://codestrata.ai",
        "https://www.codestrata.ai",
    }
)


def _public_cors_headers(origin: str | None) -> dict[str, str]:
    cleaned = (origin or "").strip().rstrip("/")
    headers: dict[str, str] = {
        "Cache-Control": "public, max-age=300",
    }
    if cleaned in _WEBSITE_ORIGINS:
        headers["Access-Control-Allow-Origin"] = cleaned
        headers["Vary"] = "Origin"
        headers["Access-Control-Allow-Methods"] = "GET,OPTIONS"
        headers["Access-Control-Allow-Headers"] = "Accept,Content-Type"
    return headers


def handle_community_status(
    context: RequestContext,
    *,
    service: CommunityStatusService,
) -> Response:
    """Public read-only Community Status — never 500 solely because GitHub fails."""

    try:
        payload = service.build()
        max_age = service.cache_control_max_age
        headers = _public_cors_headers(context.origin_header)
        headers["Cache-Control"] = f"public, max-age={max_age}"
        return build_json_response(
            payload,
            status_code=200,
            api_version=API_VERSION_V1,
            request_id=context.request_id,
            extra_headers=headers,
        )
    except Exception:  # noqa: BLE001
        return build_error_response(
            ERROR_INTERNAL,
            http_status=500,
            api_version=API_VERSION_V1,
            request_id=context.request_id,
        )
