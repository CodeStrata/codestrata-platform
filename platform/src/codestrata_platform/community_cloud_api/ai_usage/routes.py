"""Central AI usage route registration for Community Cloud API v1."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest
from codestrata_platform.community_cloud_api.ai_usage.policy import (
    COMMUNITY_AI_USAGE_SCHEMA_VERSION,
)
from codestrata_platform.community_cloud_api.ai_usage.service import IngestAiUsage
from codestrata_platform.community_cloud_api.ai_usage.validation import (
    validate_ai_usage_semantics,
)
from codestrata_platform.community_cloud_api.constants import API_VERSION_V1
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.registry import RouteRegistry, RouteSpec
from codestrata_platform.community_cloud_api.validation.models import (
    BodyPolicy,
    RequestSchemaDescriptor,
)
from starlette.responses import Response

AI_USAGE_PATH = "/ai-usage"
AI_USAGE_ROUTE_NAME = "ai_usage.ingest"
AI_USAGE_SCHEMA_ID = "community.ai-usage.ingest"


def ai_usage_request_schema() -> RequestSchemaDescriptor:
    return RequestSchemaDescriptor(
        schema_id=AI_USAGE_SCHEMA_ID,
        schema_version=COMMUNITY_AI_USAGE_SCHEMA_VERSION,
        model_type=AiUsageRequest,
        body_policy=BodyPolicy.REQUIRED,
        semantic_validator=validate_ai_usage_semantics,
    )


def register_ai_usage_routes(
    registry: RouteRegistry,
    *,
    service: IngestAiUsage,
) -> None:
    def _handle(context: RequestContext) -> Response:
        return service.handle(context)

    registry.register(
        RouteSpec(
            version=API_VERSION_V1,
            method="POST",
            path=AI_USAGE_PATH,
            name=AI_USAGE_ROUTE_NAME,
        ),
        handler=_handle,
        request_schema=ai_usage_request_schema(),
    )
