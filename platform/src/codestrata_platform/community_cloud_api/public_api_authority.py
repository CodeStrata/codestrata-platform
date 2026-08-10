"""Central Community Cloud production API base URL authority (Slice 17.14)."""

from __future__ import annotations

PUBLIC_API_HOSTNAME = "api.codestrata.ai"
PUBLIC_API_BASE_URL = "https://api.codestrata.ai"
PUBLIC_API_REGION = "us-west-2"

# Implementation detail only — never document as public contract.
EXECUTE_API_CLASSIFICATION = "IMPLEMENTATION_DETAIL"
EXECUTE_API_FALLBACK_CLASSIFICATION = "FALLBACK_IMPLEMENTATION_ENDPOINT"

# Canonical paths under the public authority.
HEALTH_PATH = "/api/v1/health"
TELEMETRY_PATH = "/api/v1/telemetry"
ASSESSMENT_METADATA_PATH = "/api/v1/assessment-metadata"
CLI_EVENTS_PATH = "/api/v1/cli-events"
EXTENSION_EVENTS_PATH = "/api/v1/extension-events"
AI_USAGE_PATH = "/api/v1/ai-usage"


def public_url(path: str) -> str:
    """Join public base URL with an absolute API path."""

    if not path.startswith("/"):
        raise ValueError("path must be absolute")
    return f"{PUBLIC_API_BASE_URL}{path}"


__all__ = [
    "AI_USAGE_PATH",
    "ASSESSMENT_METADATA_PATH",
    "CLI_EVENTS_PATH",
    "EXECUTE_API_CLASSIFICATION",
    "EXECUTE_API_FALLBACK_CLASSIFICATION",
    "EXTENSION_EVENTS_PATH",
    "HEALTH_PATH",
    "PUBLIC_API_BASE_URL",
    "PUBLIC_API_HOSTNAME",
    "PUBLIC_API_REGION",
    "TELEMETRY_PATH",
    "public_url",
]
