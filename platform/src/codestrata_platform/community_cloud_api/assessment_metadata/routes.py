"""Central assessment-metadata route registration for Community Cloud API v1."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentMetadataRequest,
)
from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
    COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
)
from codestrata_platform.community_cloud_api.assessment_metadata.service import (
    IngestAssessmentMetadata,
)
from codestrata_platform.community_cloud_api.assessment_metadata.validation import (
    validate_assessment_metadata_semantics,
)
from codestrata_platform.community_cloud_api.constants import API_VERSION_V1
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.registry import RouteRegistry, RouteSpec
from codestrata_platform.community_cloud_api.validation.models import (
    BodyPolicy,
    RequestSchemaDescriptor,
)
from starlette.responses import Response

ASSESSMENT_METADATA_PATH = "/assessment-metadata"
ASSESSMENT_METADATA_ROUTE_NAME = "assessment_metadata.ingest"
ASSESSMENT_METADATA_SCHEMA_ID = "community.assessment-metadata.ingest"


def assessment_metadata_request_schema() -> RequestSchemaDescriptor:
    return RequestSchemaDescriptor(
        schema_id=ASSESSMENT_METADATA_SCHEMA_ID,
        schema_version=COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
        model_type=AssessmentMetadataRequest,
        body_policy=BodyPolicy.REQUIRED,
        semantic_validator=validate_assessment_metadata_semantics,
    )


def register_assessment_metadata_routes(
    registry: RouteRegistry,
    *,
    service: IngestAssessmentMetadata,
) -> None:
    """Register POST /assessment-metadata on the given registry (v1)."""

    def _handle(context: RequestContext) -> Response:
        return service.handle(context)

    registry.register(
        RouteSpec(
            version=API_VERSION_V1,
            method="POST",
            path=ASSESSMENT_METADATA_PATH,
            name=ASSESSMENT_METADATA_ROUTE_NAME,
        ),
        handler=_handle,
        request_schema=assessment_metadata_request_schema(),
    )
