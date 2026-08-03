"""Version and surface constants for the Community Cloud API."""

from __future__ import annotations

API_SURFACE = "community_cloud"
API_VERSION_V1 = "v1"
SUPPORTED_API_VERSIONS: tuple[str, ...] = (API_VERSION_V1,)
DEFAULT_API_VERSION = API_VERSION_V1
API_ROOT_PREFIX = "/api"
API_PREFIX_V1 = f"{API_ROOT_PREFIX}/{API_VERSION_V1}"

# Foundation contract version (independent of assessment / EIR schemas).
COMMUNITY_CLOUD_API_SCHEMA_VERSION = "1.0"

# Request validation policy (independent of API contract / assessment / EIR).
COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION = "1.0"
MAX_VALIDATION_ERROR_DETAILS = 20

# Payload limit policy version string fragment (full urn in payload_limits.models).
COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION = "1.0"

# Structured logging policy version fragment (full urn in logging.models).
COMMUNITY_LOGGING_POLICY_VERSION = "1.0"

# Event identity policy version fragment (full urn in event_identity.models).
COMMUNITY_EVENT_IDENTITY_POLICY_VERSION = "1.0"

# Telemetry envelope / policy versions (independent of API contract).
COMMUNITY_TELEMETRY_SCHEMA_VERSION = "1.0"
COMMUNITY_TELEMETRY_POLICY_VERSION = "1.0"

# Assessment metadata envelope / policy versions.
COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION = "1.0"
COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION = "1.0"

# CLI event envelope / policy / catalog versions.
COMMUNITY_CLI_EVENT_SCHEMA_VERSION = "1.0"
COMMUNITY_CLI_EVENT_POLICY_VERSION = "1.0"
COMMUNITY_CLI_OPERATION_CATALOG_VERSION = "1.0"

# Extension event envelope / policy / catalog versions.
COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION = "1.0"
COMMUNITY_EXTENSION_EVENT_POLICY_VERSION = "1.0"
COMMUNITY_EXTENSION_OPERATION_CATALOG_VERSION = "1.0"

# AI usage envelope / policy / catalog versions.
COMMUNITY_AI_USAGE_SCHEMA_VERSION = "1.0"
COMMUNITY_AI_USAGE_POLICY_VERSION = "1.0"
COMMUNITY_AI_CAPABILITY_CATALOG_VERSION = "1.0"
COMMUNITY_AI_PROVIDER_FAMILY_CATALOG_VERSION = "1.0"
COMMUNITY_AI_MODEL_FAMILY_CATALOG_VERSION = "1.0"

# Rate-limit policy version fragment (full urn in rate_limiting.models).
COMMUNITY_RATE_LIMIT_POLICY_VERSION = "1.1"

# Authentication policy / credential format versions.
COMMUNITY_AUTHENTICATION_POLICY_VERSION = "1.0"
COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION = "1"

JSON_MEDIA_TYPE = "application/json"
API_VERSION_HEADER = "X-Community-Cloud-API-Version"
REQUEST_ID_HEADER = "X-Request-Id"

ALLOWED_METHODS_WITHOUT_BODY = frozenset({"GET", "HEAD", "OPTIONS", "DELETE"})
ALLOWED_METHODS_WITH_JSON_BODY = frozenset({"POST", "PUT", "PATCH"})
SUPPORTED_METHODS = ALLOWED_METHODS_WITHOUT_BODY | ALLOWED_METHODS_WITH_JSON_BODY
