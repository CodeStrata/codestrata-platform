"""Production-foundation wiring for Community Cloud Lambda deployment."""

from __future__ import annotations

from fastapi import FastAPI

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.authentication import (
    UnavailableCommunityCredentialVerifier,
    default_authentication_policy,
)
from codestrata_platform.community_cloud_api.deployment.diagnostics import (
    deployment_wiring_diagnostic,
)
from codestrata_platform.community_cloud_api.deployment.settings import (
    DeploymentSettings,
    load_deployment_settings,
)
from codestrata_platform.community_cloud_api.rate_limiting import (
    default_rate_limit_policy,
)


def create_production_foundation_app(
    *,
    settings: DeploymentSettings | None = None,
) -> FastAPI:
    """Build the Community Cloud app for production infrastructure foundation.

    Explicit fail-closed wiring:

    - authentication enabled with unavailable verifier (no credentials)
    - rate limiting enabled (process-local store retained as defense-in-depth)
    - all event sinks default to unavailable
    - event identity lookup/recorder remain unset (fail-closed)
    - no test adapters, no-op sinks, or hardcoded tokens

    Health remains operational. Ingestion returns 503 without durable backends.
    """

    active = settings or load_deployment_settings()
    if active.ingestion_enabled:
        raise RuntimeError("ingestion must remain disabled for production foundation")
    if not active.authentication_enabled:
        raise RuntimeError("authentication must remain enabled")
    if not active.rate_limit_enabled:
        raise RuntimeError("rate limiting must remain enabled")

    app = create_community_cloud_app(
        authentication_policy=default_authentication_policy(),
        credential_verifier=UnavailableCommunityCredentialVerifier(),
        rate_limit_policy=default_rate_limit_policy(),
        # Sinks and identity ports intentionally omitted → unavailable/fail-closed.
        # rate_limit_store omitted → process-local InMemoryRateLimitStore.
    )
    app.state.community_cloud_deployment_settings = active
    app.state.community_cloud_deployment_diagnostic = deployment_wiring_diagnostic(active)
    return app
