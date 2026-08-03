"""Central extension event route registration for Community Cloud API v1."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.constants import API_VERSION_V1
from codestrata_platform.community_cloud_api.extension_events.models import (
    ExtensionEventRequest,
)
from codestrata_platform.community_cloud_api.extension_events.policy import (
    COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
)
from codestrata_platform.community_cloud_api.extension_events.service import (
    IngestExtensionEvent,
)
from codestrata_platform.community_cloud_api.extension_events.validation import (
    validate_extension_event_semantics,
)
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.registry import RouteRegistry, RouteSpec
from codestrata_platform.community_cloud_api.validation.models import (
    BodyPolicy,
    RequestSchemaDescriptor,
)
from starlette.responses import Response

EXTENSION_EVENTS_PATH = "/extension-events"
EXTENSION_EVENTS_ROUTE_NAME = "extension_events.ingest"
EXTENSION_EVENTS_SCHEMA_ID = "community.extension-events.ingest"


def extension_event_request_schema() -> RequestSchemaDescriptor:
    return RequestSchemaDescriptor(
        schema_id=EXTENSION_EVENTS_SCHEMA_ID,
        schema_version=COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
        model_type=ExtensionEventRequest,
        body_policy=BodyPolicy.REQUIRED,
        semantic_validator=validate_extension_event_semantics,
    )


def register_extension_event_routes(
    registry: RouteRegistry,
    *,
    service: IngestExtensionEvent,
) -> None:
    def _handle(context: RequestContext) -> Response:
        return service.handle(context)

    registry.register(
        RouteSpec(
            version=API_VERSION_V1,
            method="POST",
            path=EXTENSION_EVENTS_PATH,
            name=EXTENSION_EVENTS_ROUTE_NAME,
        ),
        handler=_handle,
        request_schema=extension_event_request_schema(),
    )
