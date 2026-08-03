"""Central CLI event route registration for Community Cloud API v1."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.cli_events.models import CliEventRequest
from codestrata_platform.community_cloud_api.cli_events.policy import (
    COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
)
from codestrata_platform.community_cloud_api.cli_events.service import IngestCliEvent
from codestrata_platform.community_cloud_api.cli_events.validation import (
    validate_cli_event_semantics,
)
from codestrata_platform.community_cloud_api.constants import API_VERSION_V1
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.registry import RouteRegistry, RouteSpec
from codestrata_platform.community_cloud_api.validation.models import (
    BodyPolicy,
    RequestSchemaDescriptor,
)
from starlette.responses import Response

CLI_EVENTS_PATH = "/cli-events"
CLI_EVENTS_ROUTE_NAME = "cli_events.ingest"
CLI_EVENTS_SCHEMA_ID = "community.cli-events.ingest"


def cli_event_request_schema() -> RequestSchemaDescriptor:
    return RequestSchemaDescriptor(
        schema_id=CLI_EVENTS_SCHEMA_ID,
        schema_version=COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
        model_type=CliEventRequest,
        body_policy=BodyPolicy.REQUIRED,
        semantic_validator=validate_cli_event_semantics,
    )


def register_cli_event_routes(
    registry: RouteRegistry,
    *,
    service: IngestCliEvent,
) -> None:
    def _handle(context: RequestContext) -> Response:
        return service.handle(context)

    registry.register(
        RouteSpec(
            version=API_VERSION_V1,
            method="POST",
            path=CLI_EVENTS_PATH,
            name=CLI_EVENTS_ROUTE_NAME,
        ),
        handler=_handle,
        request_schema=cli_event_request_schema(),
    )
