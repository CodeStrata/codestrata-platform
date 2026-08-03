"""Bounded deployment configuration for Community Cloud production foundation."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEPLOYMENT_MODE_PRODUCTION_FOUNDATION = "production_foundation"
AUTHENTICATION_MODE_VERIFIER_UNAVAILABLE = "enabled_verifier_unavailable"
RATE_LIMIT_MODE_GATEWAY_PLUS_LOCAL = "api_gateway_plus_process_local"


@dataclass(frozen=True, slots=True)
class DeploymentSettings:
    """Safe, non-secret deployment settings loaded from explicit env names."""

    deployment_mode: str
    community_api_version: str
    authentication_enabled: bool
    rate_limit_enabled: bool
    ingestion_enabled: bool
    authentication_mode: str
    rate_limit_mode: str


def load_deployment_settings(
    environ: dict[str, str] | None = None,
) -> DeploymentSettings:
    """Load bounded deployment settings.

    Only known ``CODESTRATA_*`` keys are read. Missing values use fail-closed
    production-foundation defaults. Secrets are never loaded here.
    """

    env = environ if environ is not None else dict(os.environ)

    deployment_mode = (
        env.get("CODESTRATA_DEPLOYMENT_MODE") or DEPLOYMENT_MODE_PRODUCTION_FOUNDATION
    ).strip()
    if deployment_mode != DEPLOYMENT_MODE_PRODUCTION_FOUNDATION:
        raise ValueError(
            "unsupported CODESTRATA_DEPLOYMENT_MODE; "
            f"expected {DEPLOYMENT_MODE_PRODUCTION_FOUNDATION!r}"
        )

    api_version = (env.get("CODESTRATA_COMMUNITY_API_VERSION") or "1.0").strip()
    if api_version != "1.0":
        raise ValueError("unsupported CODESTRATA_COMMUNITY_API_VERSION")

    authentication_enabled = _parse_bool(
        env.get("CODESTRATA_AUTHENTICATION_ENABLED"), default=True
    )
    if not authentication_enabled:
        raise ValueError(
            "CODESTRATA_AUTHENTICATION_ENABLED must remain true for production foundation"
        )

    rate_limit_enabled = _parse_bool(
        env.get("CODESTRATA_RATE_LIMIT_ENABLED"), default=True
    )
    if not rate_limit_enabled:
        raise ValueError(
            "CODESTRATA_RATE_LIMIT_ENABLED must remain true for production foundation"
        )

    ingestion_enabled = _parse_bool(
        env.get("CODESTRATA_INGESTION_ENABLED"), default=False
    )
    if ingestion_enabled:
        raise ValueError(
            "CODESTRATA_INGESTION_ENABLED must remain false until durable sinks "
            "and a production verifier exist"
        )

    authentication_mode = (
        env.get("CODESTRATA_AUTHENTICATION_MODE")
        or AUTHENTICATION_MODE_VERIFIER_UNAVAILABLE
    ).strip()
    if authentication_mode != AUTHENTICATION_MODE_VERIFIER_UNAVAILABLE:
        raise ValueError("unsupported CODESTRATA_AUTHENTICATION_MODE")

    rate_limit_mode = (
        env.get("CODESTRATA_RATE_LIMIT_MODE") or RATE_LIMIT_MODE_GATEWAY_PLUS_LOCAL
    ).strip()
    if rate_limit_mode != RATE_LIMIT_MODE_GATEWAY_PLUS_LOCAL:
        raise ValueError("unsupported CODESTRATA_RATE_LIMIT_MODE")

    return DeploymentSettings(
        deployment_mode=deployment_mode,
        community_api_version=api_version,
        authentication_enabled=authentication_enabled,
        rate_limit_enabled=rate_limit_enabled,
        ingestion_enabled=ingestion_enabled,
        authentication_mode=authentication_mode,
        rate_limit_mode=rate_limit_mode,
    )


def _parse_bool(raw: str | None, *, default: bool) -> bool:
    if raw is None or raw.strip() == "":
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"invalid boolean environment value: {raw!r}")
