"""Central telemetry route registration for Community Cloud API v1."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.constants import API_VERSION_V1
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.registry import RouteRegistry, RouteSpec
from codestrata_platform.community_cloud_api.telemetry.models import (
    TelemetryIngestionRequest,
)
from codestrata_platform.community_cloud_api.telemetry.policy import (
    COMMUNITY_TELEMETRY_SCHEMA_VERSION,
)
from codestrata_platform.community_cloud_api.telemetry.service import IngestTelemetryEvent
from codestrata_platform.community_cloud_api.telemetry.validation import (
    validate_telemetry_semantics,
)
from codestrata_platform.community_cloud_api.validation.models import (
    BodyPolicy,
    RequestSchemaDescriptor,
)
from starlette.responses import Response

TELEMETRY_PATH = "/telemetry"
TELEMETRY_ROUTE_NAME = "telemetry.ingest"
TELEMETRY_SCHEMA_ID = "community.telemetry.ingest"


def telemetry_request_schema() -> RequestSchemaDescriptor:
    return RequestSchemaDescriptor(
        schema_id=TELEMETRY_SCHEMA_ID,
        schema_version=COMMUNITY_TELEMETRY_SCHEMA_VERSION,
        model_type=TelemetryIngestionRequest,
        body_policy=BodyPolicy.REQUIRED,
        semantic_validator=validate_telemetry_semantics,
    )


def register_telemetry_routes(
    registry: RouteRegistry,
    *,
    service: IngestTelemetryEvent,
) -> None:
    """Register POST /telemetry on the given registry (v1)."""

    def _handle(context: RequestContext) -> Response:
        return service.handle(context)

    registry.register(
        RouteSpec(
            version=API_VERSION_V1,
            method="POST",
            path=TELEMETRY_PATH,
            name=TELEMETRY_ROUTE_NAME,
        ),
        handler=_handle,
        request_schema=telemetry_request_schema(),
    )
