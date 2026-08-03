"""HTTP responses for rate-limit outcomes."""

from __future__ import annotations

from starlette.responses import Response

from codestrata_platform.community_cloud_api.errors import (
    ERROR_RATE_LIMIT_EXCEEDED,
    ERROR_RATE_LIMIT_UNAVAILABLE,
    ApiErrorResponse,
)
from codestrata_platform.community_cloud_api.rate_limiting.decisions import (
    DECISION_LIMITED,
    DECISION_UNAVAILABLE,
    RateLimitDecision,
)
from codestrata_platform.community_cloud_api.rate_limiting.models import (
    CommunityRateLimitPolicy,
    ResponseHeaderPolicy,
)
from codestrata_platform.community_cloud_api.serialization import (
    build_error_response,
    build_json_response,
)

HEADER_RETRY_AFTER = "Retry-After"
HEADER_RATE_LIMIT_LIMIT = "RateLimit-Limit"
HEADER_RATE_LIMIT_REMAINING = "RateLimit-Remaining"
HEADER_RATE_LIMIT_RESET = "RateLimit-Reset"


def rate_limit_headers(
    decision: RateLimitDecision,
    *,
    header_policy: ResponseHeaderPolicy,
    for_limited: bool,
) -> dict[str, str]:
    """Bounded integer rate-limit headers — no scope identity."""

    headers: dict[str, str] = {}
    include_meta = (
        header_policy.include_on_limited if for_limited else header_policy.include_on_allowed
    )
    if include_meta:
        headers[HEADER_RATE_LIMIT_LIMIT] = str(int(decision.limit))
        headers[HEADER_RATE_LIMIT_REMAINING] = str(max(0, int(decision.remaining)))
        headers[HEADER_RATE_LIMIT_RESET] = str(max(0, int(decision.reset_after_seconds)))
    if (
        for_limited
        and header_policy.include_retry_after_on_limited
        and decision.retry_after_seconds is not None
    ):
        headers[HEADER_RETRY_AFTER] = str(max(1, int(decision.retry_after_seconds)))
    return headers


def build_rate_limit_exceeded_response(
    decision: RateLimitDecision,
    *,
    api_version: str,
    request_id: str | None,
    policy: CommunityRateLimitPolicy,
) -> Response:
    headers = rate_limit_headers(
        decision,
        header_policy=policy.response_header_policy,
        for_limited=True,
    )
    envelope = ApiErrorResponse.build(
        ERROR_RATE_LIMIT_EXCEEDED,
        http_status=429,
        api_version=api_version,
        request_id=request_id,
    )
    return build_json_response(
        envelope,
        status_code=429,
        api_version=api_version,
        request_id=request_id,
        extra_headers=headers,
    )


def build_rate_limit_unavailable_response(
    decision: RateLimitDecision,
    *,
    api_version: str,
    request_id: str | None,
) -> Response:
    _ = decision
    return build_error_response(
        ERROR_RATE_LIMIT_UNAVAILABLE,
        http_status=503,
        api_version=api_version,
        request_id=request_id,
    )


def apply_allowed_rate_limit_headers(
    response: Response,
    decision: RateLimitDecision,
    *,
    policy: CommunityRateLimitPolicy,
) -> Response:
    """Attach RateLimit-* headers to an allowed response without changing the body."""

    if not policy.response_header_policy.include_on_allowed:
        return response
    headers = rate_limit_headers(
        decision,
        header_policy=policy.response_header_policy,
        for_limited=False,
    )
    for key, value in headers.items():
        response.headers[key] = value
    return response


def decision_error_code(decision: RateLimitDecision) -> str | None:
    if decision.status == DECISION_LIMITED:
        return ERROR_RATE_LIMIT_EXCEEDED
    if decision.status == DECISION_UNAVAILABLE:
        return ERROR_RATE_LIMIT_UNAVAILABLE
    return None
