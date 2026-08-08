"""Route registration for Insights auth and protected overview."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.constants import API_VERSION_V1
from codestrata_platform.community_cloud_api.insights.service import InsightsAggregationService
from codestrata_platform.community_cloud_api.insights_auth.handlers import (
    handle_login,
    handle_logout,
    handle_overview,
    handle_session_status,
)
from codestrata_platform.community_cloud_api.insights_auth.request_models import (
    InsightsLoginRequest,
)
from codestrata_platform.community_cloud_api.insights_auth.service import InsightsAuthService
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.registry import RouteRegistry, RouteSpec
from codestrata_platform.community_cloud_api.validation.models import (
    BodyPolicy,
    NO_BODY_SCHEMA,
    RequestSchemaDescriptor,
)
from starlette.responses import Response

LOGIN_PATH = "/insights/auth/login"
LOGOUT_PATH = "/insights/auth/logout"
SESSION_PATH = "/insights/auth/session"
OVERVIEW_PATH = "/insights/api/overview"

LOGIN_ROUTE = "insights.auth.login"
LOGOUT_ROUTE = "insights.auth.logout"
SESSION_ROUTE = "insights.auth.session"
OVERVIEW_ROUTE = "insights.api.overview"

LOGIN_SCHEMA_ID = "community.insights.auth.login"
LOGIN_SCHEMA_VERSION = "1.0"


def login_request_schema() -> RequestSchemaDescriptor:
    return RequestSchemaDescriptor(
        schema_id=LOGIN_SCHEMA_ID,
        schema_version=LOGIN_SCHEMA_VERSION,
        model_type=InsightsLoginRequest,
        body_policy=BodyPolicy.REQUIRED,
    )


def register_insights_auth_routes(
    registry: RouteRegistry,
    *,
    auth: InsightsAuthService,
    aggregation: InsightsAggregationService | None = None,
) -> None:
    """Register Insights auth + narrow overview under /api/v1.

    Routes use authentication_group=public so Community client-credential auth
    does not apply; session checks run inside Insights handlers.
    """

    agg = aggregation if aggregation is not None else InsightsAggregationService()

    def _login(context: RequestContext) -> Response:
        return handle_login(context, auth=auth)

    def _logout(context: RequestContext) -> Response:
        return handle_logout(context, auth=auth)

    def _session(context: RequestContext) -> Response:
        return handle_session_status(context, auth=auth)

    def _overview(context: RequestContext) -> Response:
        return handle_overview(context, auth=auth, aggregation=agg)

    registry.register(
        RouteSpec(
            version=API_VERSION_V1,
            method="POST",
            path=LOGIN_PATH,
            name=LOGIN_ROUTE,
            rate_limit_group="auth_attempt",
            authentication_group="public",
        ),
        handler=_login,
        request_schema=login_request_schema(),
    )
    registry.register(
        RouteSpec(
            version=API_VERSION_V1,
            method="POST",
            path=LOGOUT_PATH,
            name=LOGOUT_ROUTE,
            rate_limit_group="health",
            authentication_group="public",
        ),
        handler=_logout,
        request_schema=NO_BODY_SCHEMA,
    )
    registry.register(
        RouteSpec(
            version=API_VERSION_V1,
            method="GET",
            path=SESSION_PATH,
            name=SESSION_ROUTE,
            rate_limit_group="health",
            authentication_group="public",
        ),
        handler=_session,
        request_schema=NO_BODY_SCHEMA,
    )
    registry.register(
        RouteSpec(
            version=API_VERSION_V1,
            method="GET",
            path=OVERVIEW_PATH,
            name=OVERVIEW_ROUTE,
            rate_limit_group="health",
            authentication_group="public",
        ),
        handler=_overview,
        request_schema=NO_BODY_SCHEMA,
    )
