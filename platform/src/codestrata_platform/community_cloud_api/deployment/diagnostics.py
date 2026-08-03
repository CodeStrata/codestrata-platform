"""Safe deployment diagnostics (no secrets, no request data)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.deployment.settings import DeploymentSettings


def deployment_wiring_diagnostic(settings: DeploymentSettings) -> dict[str, object]:
    """Return a privacy-safe summary of production foundation wiring."""

    return {
        "deployment_mode": settings.deployment_mode,
        "community_api_version": settings.community_api_version,
        "authentication_enabled": settings.authentication_enabled,
        "authentication_mode": settings.authentication_mode,
        "rate_limit_enabled": settings.rate_limit_enabled,
        "rate_limit_mode": settings.rate_limit_mode,
        "ingestion_enabled": settings.ingestion_enabled,
        "credential_verifier": "unavailable",
        "event_sinks": "unavailable",
        "event_identity_store": "unavailable",
        "durable_ingestion": False,
        "distributed_rate_limit": False,
    }
