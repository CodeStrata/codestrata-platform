"""Route registration for Community report publishing (Slice 17.16)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.constants import API_VERSION_V1
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.registry import RouteRegistry, RouteSpec
from codestrata_platform.community_cloud_api.reports.models import (
    ReportPublishRequest,
    ReportUploadIntentRequest,
)
from codestrata_platform.community_cloud_api.reports.service import ReportPublishingService
from codestrata_platform.community_cloud_api.validation.models import (
    BodyPolicy,
    NO_BODY_SCHEMA,
    RequestSchemaDescriptor,
)
from starlette.responses import Response

UPLOAD_INTENT_PATH = "/reports/upload-intents"
PUBLISH_PATH = "/reports"
PUBLIC_GET_PATH = "/reports/{public_id}"
REVOKE_PATH = "/reports/{public_id}"

UPLOAD_INTENT_ROUTE = "reports.upload_intent"
PUBLISH_ROUTE = "reports.publish"
PUBLIC_GET_ROUTE = "reports.get"
REVOKE_ROUTE = "reports.revoke"

UPLOAD_SCHEMA_ID = "community.reports.upload_intent"
PUBLISH_SCHEMA_ID = "community.reports.publish"
SCHEMA_VERSION = "1.0"


def upload_intent_schema() -> RequestSchemaDescriptor:
    return RequestSchemaDescriptor(
        schema_id=UPLOAD_SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        model_type=ReportUploadIntentRequest,
        body_policy=BodyPolicy.REQUIRED,
    )


def publish_schema() -> RequestSchemaDescriptor:
    return RequestSchemaDescriptor(
        schema_id=PUBLISH_SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        model_type=ReportPublishRequest,
        body_policy=BodyPolicy.REQUIRED,
    )


def register_report_routes(
    registry: RouteRegistry,
    *,
    service: ReportPublishingService,
) -> None:
    """Register report upload-intent / publish / public get / revoke routes."""

    def _upload(context: RequestContext) -> Response:
        return service.handle_upload_intent(context)

    def _publish(context: RequestContext) -> Response:
        return service.handle_publish(context)

    def _get(context: RequestContext) -> Response:
        return service.handle_public_get(context)

    def _revoke(context: RequestContext) -> Response:
        return service.handle_revoke(context)

    registry.register(
        RouteSpec(
            version=API_VERSION_V1,
            method="POST",
            path=UPLOAD_INTENT_PATH,
            name=UPLOAD_INTENT_ROUTE,
            rate_limit_group="ingestion",
            authentication_group="community_ingestion",
        ),
        handler=_upload,
        request_schema=upload_intent_schema(),
    )
    registry.register(
        RouteSpec(
            version=API_VERSION_V1,
            method="POST",
            path=PUBLISH_PATH,
            name=PUBLISH_ROUTE,
            rate_limit_group="ingestion",
            authentication_group="community_ingestion",
        ),
        handler=_publish,
        request_schema=publish_schema(),
    )
    registry.register(
        RouteSpec(
            version=API_VERSION_V1,
            method="GET",
            path=PUBLIC_GET_PATH,
            name=PUBLIC_GET_ROUTE,
            rate_limit_group="health",
            authentication_group="public",
        ),
        handler=_get,
        request_schema=NO_BODY_SCHEMA,
    )
    registry.register(
        RouteSpec(
            version=API_VERSION_V1,
            method="DELETE",
            path=REVOKE_PATH,
            name=REVOKE_ROUTE,
            rate_limit_group="ingestion",
            authentication_group="community_ingestion",
        ),
        handler=_revoke,
        request_schema=NO_BODY_SCHEMA,
    )


__all__ = [
    "PUBLISH_PATH",
    "PUBLISH_ROUTE",
    "PUBLIC_GET_PATH",
    "PUBLIC_GET_ROUTE",
    "REVOKE_PATH",
    "REVOKE_ROUTE",
    "UPLOAD_INTENT_PATH",
    "UPLOAD_INTENT_ROUTE",
    "register_report_routes",
]
