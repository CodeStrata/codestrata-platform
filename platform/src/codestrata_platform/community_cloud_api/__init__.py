"""Community Cloud API (Platform-only, Epic 7).

Versioned HTTP surface. Slice 7.13 adds Community client authentication for
protected ingestion routes (health remains public). Default auth verifier is
unavailable (fail-closed). No user accounts, production credential store, or
client emitter wiring.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.ai_usage import (
    COMMUNITY_AI_USAGE_POLICY_URN,
    CommunityAiUsagePolicy,
)
from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.assessment_metadata import (
    COMMUNITY_ASSESSMENT_METADATA_POLICY_URN,
    CommunityAssessmentMetadataPolicy,
)
from codestrata_platform.community_cloud_api.cli_events import (
    COMMUNITY_CLI_EVENT_POLICY_URN,
    CommunityCliEventPolicy,
)
from codestrata_platform.community_cloud_api.constants import (
    API_PREFIX_V1,
    API_SURFACE,
    API_VERSION_V1,
    COMMUNITY_AI_CAPABILITY_CATALOG_VERSION,
    COMMUNITY_AI_MODEL_FAMILY_CATALOG_VERSION,
    COMMUNITY_AI_PROVIDER_FAMILY_CATALOG_VERSION,
    COMMUNITY_AI_USAGE_POLICY_VERSION,
    COMMUNITY_AI_USAGE_SCHEMA_VERSION,
    COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION,
    COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
    COMMUNITY_CLI_EVENT_POLICY_VERSION,
    COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
    COMMUNITY_CLI_OPERATION_CATALOG_VERSION,
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
    COMMUNITY_EVENT_IDENTITY_POLICY_VERSION,
    COMMUNITY_EXTENSION_EVENT_POLICY_VERSION,
    COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
    COMMUNITY_EXTENSION_OPERATION_CATALOG_VERSION,
    COMMUNITY_LOGGING_POLICY_VERSION,
    COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION,
    COMMUNITY_RATE_LIMIT_POLICY_VERSION,
    COMMUNITY_AUTHENTICATION_POLICY_VERSION,
    COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION,
    COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION,
    COMMUNITY_TELEMETRY_POLICY_VERSION,
    COMMUNITY_TELEMETRY_SCHEMA_VERSION,
    SUPPORTED_API_VERSIONS,
)
from codestrata_platform.community_cloud_api.event_identity import (
    COMMUNITY_EVENT_IDENTITY_POLICY_URN,
    CommunityEventIdentityPolicy,
)
from codestrata_platform.community_cloud_api.extension_events import (
    COMMUNITY_EXTENSION_EVENT_POLICY_URN,
    CommunityExtensionEventPolicy,
)
from codestrata_platform.community_cloud_api.logging import (
    COMMUNITY_LOGGING_POLICY_URN,
    CommunityCloudLogger,
    CommunityLoggingPolicy,
)
from codestrata_platform.community_cloud_api.payload_limits import (
    PAYLOAD_LIMIT_POLICY_URN,
    PayloadLimitPolicy,
)
from codestrata_platform.community_cloud_api.rate_limiting import (
    COMMUNITY_RATE_LIMIT_POLICY_URN,
    CommunityRateLimitPolicy,
)
from codestrata_platform.community_cloud_api.authentication import (
    COMMUNITY_AUTHENTICATION_POLICY_URN,
    CommunityAuthenticationPolicy,
)
from codestrata_platform.community_cloud_api.registry import RouteRegistry, RouteSpec
from codestrata_platform.community_cloud_api.telemetry import (
    COMMUNITY_TELEMETRY_POLICY_URN,
    CommunityTelemetryPolicy,
)

__all__ = [
    "API_PREFIX_V1",
    "API_SURFACE",
    "API_VERSION_V1",
    "COMMUNITY_AI_CAPABILITY_CATALOG_VERSION",
    "COMMUNITY_AI_MODEL_FAMILY_CATALOG_VERSION",
    "COMMUNITY_AI_PROVIDER_FAMILY_CATALOG_VERSION",
    "COMMUNITY_AI_USAGE_POLICY_URN",
    "COMMUNITY_AI_USAGE_POLICY_VERSION",
    "COMMUNITY_AI_USAGE_SCHEMA_VERSION",
    "COMMUNITY_ASSESSMENT_METADATA_POLICY_URN",
    "COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION",
    "COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION",
    "COMMUNITY_CLI_EVENT_POLICY_URN",
    "COMMUNITY_CLI_EVENT_POLICY_VERSION",
    "COMMUNITY_CLI_EVENT_SCHEMA_VERSION",
    "COMMUNITY_CLI_OPERATION_CATALOG_VERSION",
    "COMMUNITY_CLOUD_API_SCHEMA_VERSION",
    "COMMUNITY_EVENT_IDENTITY_POLICY_URN",
    "COMMUNITY_EVENT_IDENTITY_POLICY_VERSION",
    "COMMUNITY_EXTENSION_EVENT_POLICY_URN",
    "COMMUNITY_EXTENSION_EVENT_POLICY_VERSION",
    "COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION",
    "COMMUNITY_EXTENSION_OPERATION_CATALOG_VERSION",
    "COMMUNITY_LOGGING_POLICY_URN",
    "COMMUNITY_LOGGING_POLICY_VERSION",
    "COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION",
    "COMMUNITY_AUTHENTICATION_POLICY_URN",
    "COMMUNITY_AUTHENTICATION_POLICY_VERSION",
    "COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION",
    "COMMUNITY_RATE_LIMIT_POLICY_URN",
    "COMMUNITY_RATE_LIMIT_POLICY_VERSION",
    "COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION",
    "COMMUNITY_TELEMETRY_POLICY_URN",
    "COMMUNITY_TELEMETRY_POLICY_VERSION",
    "COMMUNITY_TELEMETRY_SCHEMA_VERSION",
    "CommunityAiUsagePolicy",
    "CommunityAssessmentMetadataPolicy",
    "CommunityCliEventPolicy",
    "CommunityCloudLogger",
    "CommunityEventIdentityPolicy",
    "CommunityExtensionEventPolicy",
    "CommunityLoggingPolicy",
    "CommunityAuthenticationPolicy",
    "CommunityRateLimitPolicy",
    "CommunityTelemetryPolicy",
    "PAYLOAD_LIMIT_POLICY_URN",
    "PayloadLimitPolicy",
    "RouteRegistry",
    "RouteSpec",
    "create_community_cloud_app",
]
