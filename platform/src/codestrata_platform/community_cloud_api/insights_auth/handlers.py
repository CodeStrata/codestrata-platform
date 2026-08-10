"""HTTP handlers for Insights auth and protected overview."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from starlette.responses import Response

from codestrata_platform.community_cloud_api.insights.models import OverviewRequest
from codestrata_platform.community_cloud_api.insights.service import InsightsAggregationService
from codestrata_platform.community_cloud_api.insights_auth.errors import (
    ERROR_AUTHENTICATION_REQUIRED,
    ERROR_INVALID_CREDENTIALS,
    ERROR_INTERNAL_AUTH,
    SAFE_MESSAGES,
)
from codestrata_platform.community_cloud_api.insights_auth.models import (
    LoginSuccessResponse,
    LogoutResponse,
    SessionStatusResponse,
)
from codestrata_platform.community_cloud_api.insights_auth.request_models import (
    InsightsLoginRequest,
)
from codestrata_platform.community_cloud_api.insights_auth.service import InsightsAuthService
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.serialization import (
    build_error_response,
    build_json_response,
)

_STATUS_FOR_CODE = {
    "authentication_required": 401,
    "invalid_credentials": 401,
    "session_expired": 401,
    "invalid_session": 401,
    "authorization_denied": 403,
    "auth_service_unavailable": 503,
    "invalid_origin": 403,
    "rate_limited": 429,
    "internal_auth_error": 500,
}


def _auth_error(code: str, context: RequestContext) -> Response:
    return build_error_response(
        code,
        http_status=_STATUS_FOR_CODE.get(code, 401),
        api_version=context.api_version,
        request_id=context.request_id,
        details={"message": SAFE_MESSAGES.get(code, SAFE_MESSAGES[ERROR_INTERNAL_AUTH])},
    )


def handle_login(context: RequestContext, *, auth: InsightsAuthService) -> Response:
    origin_err = auth.check_origin(origin=context.origin_header, referer=context.referer_header)
    if origin_err:
        return _auth_error(origin_err, context)

    model = context.validated_request
    if not isinstance(model, InsightsLoginRequest):
        return _auth_error(ERROR_INVALID_CREDENTIALS, context)

    cookie, err = auth.login(model.password)
    if err or cookie is None:
        return _auth_error(err or ERROR_INVALID_CREDENTIALS, context)

    return build_json_response(
        LoginSuccessResponse(),
        status_code=200,
        api_version=context.api_version,
        request_id=context.request_id,
        extra_headers={
            "Set-Cookie": cookie,
            "Cache-Control": "no-store",
        },
    )


def handle_logout(context: RequestContext, *, auth: InsightsAuthService) -> Response:
    origin_err = auth.check_origin(origin=context.origin_header, referer=context.referer_header)
    if origin_err:
        return _auth_error(origin_err, context)
    cookie = auth.logout_cookie()
    return build_json_response(
        LogoutResponse(),
        status_code=200,
        api_version=context.api_version,
        request_id=context.request_id,
        extra_headers={
            "Set-Cookie": cookie,
            "Cache-Control": "no-store",
        },
    )


def handle_session_status(
    context: RequestContext, *, auth: InsightsAuthService
) -> Response:
    claims, err = auth.session_from_cookie_header(context.cookie_header)
    authenticated = claims is not None and err is None
    return build_json_response(
        SessionStatusResponse(authenticated=authenticated),
        status_code=200,
        api_version=context.api_version,
        request_id=context.request_id,
        extra_headers={"Cache-Control": "no-store"},
    )


def handle_overview(
    context: RequestContext,
    *,
    auth: InsightsAuthService,
    aggregation: InsightsAggregationService,
) -> Response:
    principal, err = auth.require_authenticated(context.cookie_header)
    if principal is None:
        return _auth_error(err or ERROR_AUTHENTICATION_REQUIRED, context)

    # Auth middleware does not know metric semantics; aggregation does not know sessions.
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=29)
    try:
        results = aggregation.aggregate_dashboard_overview(
            OverviewRequest(start_date_utc=start, end_date_utc=end)
        )
    except Exception:  # noqa: BLE001 — never leak aggregation internals
        return build_error_response(
            ERROR_INTERNAL_AUTH,
            http_status=500,
            api_version=context.api_version,
            request_id=context.request_id,
        )

    payload = {"metrics": [item.to_stable_dict() for item in results]}
    return build_json_response(
        payload,
        status_code=200,
        api_version=context.api_version,
        request_id=context.request_id,
        extra_headers={"Cache-Control": "no-store"},
    )


def handle_published_reports(
    context: RequestContext,
    *,
    auth: InsightsAuthService,
    report_service: object | None,
) -> Response:
    """Authenticated Insights index of published reports (current/previous only)."""

    from codestrata_platform.community_cloud_api.reports.service import (
        ReportPublishingService,
    )

    principal, err = auth.require_authenticated(context.cookie_header)
    if principal is None:
        return _auth_error(err or ERROR_AUTHENTICATION_REQUIRED, context)

    if not isinstance(report_service, ReportPublishingService) or not getattr(
        report_service, "_available", False
    ):
        return build_json_response(
            {
                "assessments": [],
                "engineering_intelligence": [],
                "note": "report registry unavailable",
                "source": "report_metadata",
            },
            status_code=200,
            api_version=context.api_version,
            request_id=context.request_id,
            extra_headers={"Cache-Control": "no-store"},
        )

    try:
        registry = report_service.list_published_registry()
    except Exception:  # noqa: BLE001
        return build_error_response(
            ERROR_INTERNAL_AUTH,
            http_status=500,
            api_version=context.api_version,
            request_id=context.request_id,
        )

    payload = {
        "assessments": registry.get("assessments") or [],
        "engineering_intelligence": registry.get("engineering_intelligence") or [],
        "note": "Validation evidence remains separate; rendering stays on reports.codestrata.ai",
        "source": "report_metadata",
    }
    return build_json_response(
        payload,
        status_code=200,
        api_version=context.api_version,
        request_id=context.request_id,
        extra_headers={"Cache-Control": "no-store"},
    )
