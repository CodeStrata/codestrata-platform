"""Safe deployment diagnostics (no secrets, no request data)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.deployment.settings import DeploymentSettings


def deployment_wiring_diagnostic(
    settings: DeploymentSettings,
    *,
    credential_verifier: str = "unavailable",
    event_sinks: str = "unavailable",
    event_identity_store: str = "unavailable",
    durable_ingestion: bool = False,
) -> dict[str, object]:
    """Return a privacy-safe summary of production foundation / ingestion wiring."""

    return {
        "deployment_mode": settings.deployment_mode,
        "community_api_version": settings.community_api_version,
        "authentication_enabled": settings.authentication_enabled,
        "authentication_mode": settings.authentication_mode,
        "rate_limit_enabled": settings.rate_limit_enabled,
        "rate_limit_mode": settings.rate_limit_mode,
        "ingestion_enabled": settings.ingestion_enabled,
        "ingestion_wire": settings.ingestion_wire,
        "data_lake_configured": bool(settings.data_lake_bucket),
        "credential_verifier": credential_verifier,
        "event_sinks": event_sinks,
        "event_identity_store": event_identity_store,
        "durable_ingestion": durable_ingestion,
        "distributed_rate_limit": False,
    }
