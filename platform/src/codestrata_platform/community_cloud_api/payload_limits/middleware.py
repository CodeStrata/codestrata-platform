"""Payload-limit enforcement helpers for Community Cloud dispatch.

Limits are applied after route resolution (unknown routes stay 404) and after
Slice 7.3 request validation succeeds. This module is not a global pre-route
ASGI size filter — that would violate the 404-before-payload-evaluation rule.
"""

from __future__ import annotations

from typing import Any

from starlette.responses import Response

from codestrata_platform.community_cloud_api.payload_limits.diagnostics import (
    build_payload_limit_diagnostic,
)
from codestrata_platform.community_cloud_api.payload_limits.models import (
    PayloadLimitPolicy,
    PayloadLimitResult,
)
from codestrata_platform.community_cloud_api.payload_limits.validation import (
    enforce_payload_limits,
)
from codestrata_platform.community_cloud_api.serialization import (
    build_error_response,
)


def evaluate_payload_limits(
    *,
    body: bytes,
    policy: PayloadLimitPolicy,
    parsed: Any | None = None,
    route_name: str = "",
) -> tuple[PayloadLimitResult, object | None]:
    """Run payload limits and build a safe diagnostic (unused until Slice 7.5)."""

    result = enforce_payload_limits(body=body, policy=policy, parsed=parsed)
    diagnostic = build_payload_limit_diagnostic(
        route_name=route_name,
        result=result,
        request_bytes=len(body) if body else 0,
    )
    return result, diagnostic


def build_payload_limit_error_response(
    result: PayloadLimitResult,
    *,
    api_version: str,
    request_id: str | None = None,
) -> Response:
    """Canonical 413 envelope for payload-limit rejections."""

    if result.ok or not result.error_code or not result.http_status:
        raise ValueError("build_payload_limit_error_response requires a rejection")
    details = None
    if result.limit_name:
        details = {"limit": result.limit_name}
    return build_error_response(
        result.error_code,
        http_status=result.http_status,
        api_version=api_version,
        request_id=request_id,
        details=details,
        meta_extra={"payload_limit_policy": result.policy_version},
    )
