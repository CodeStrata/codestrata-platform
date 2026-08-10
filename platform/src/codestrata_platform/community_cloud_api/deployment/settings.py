"""Bounded deployment configuration for Community Cloud production foundation."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEPLOYMENT_MODE_PRODUCTION_FOUNDATION = "production_foundation"
DEPLOYMENT_MODE_PRODUCTION_INGESTION = "production_ingestion"
ALLOWED_DEPLOYMENT_MODES = frozenset(
    {
        DEPLOYMENT_MODE_PRODUCTION_FOUNDATION,
        DEPLOYMENT_MODE_PRODUCTION_INGESTION,
    }
)
AUTHENTICATION_MODE_VERIFIER_UNAVAILABLE = "enabled_verifier_unavailable"
AUTHENTICATION_MODE_AWS_CREDENTIALS = "enabled_aws_credentials"
# Terraform/OpenTofu alias used by infrastructure module (same semantics).
AUTHENTICATION_MODE_SECRETS_MANAGER_VERIFIER = "enabled_secrets_manager_verifier"
ALLOWED_AUTHENTICATION_MODES = frozenset(
    {
        AUTHENTICATION_MODE_VERIFIER_UNAVAILABLE,
        AUTHENTICATION_MODE_AWS_CREDENTIALS,
        AUTHENTICATION_MODE_SECRETS_MANAGER_VERIFIER,
    }
)
RATE_LIMIT_MODE_GATEWAY_PLUS_LOCAL = "api_gateway_plus_process_local"
DEFAULT_COMMUNITY_CREDENTIALS_SECRET_ID = "codestrata/community/client-credentials"


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
    data_lake_bucket: str = ""
    ingestion_wire: bool = False
    data_lake_adapter: str = ""
    community_credentials_secret_id: str = DEFAULT_COMMUNITY_CREDENTIALS_SECRET_ID
    report_artifacts_bucket: str = ""
    report_publishing_enabled: bool = False


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
    if deployment_mode not in ALLOWED_DEPLOYMENT_MODES:
        raise ValueError(
            "unsupported CODESTRATA_DEPLOYMENT_MODE; "
            f"expected one of {sorted(ALLOWED_DEPLOYMENT_MODES)!r}"
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
    data_lake_bucket = (env.get("CODESTRATA_DATA_LAKE_BUCKET") or "").strip()
    ingestion_wire = _parse_bool(env.get("CODESTRATA_INGESTION_WIRE"), default=False)
    data_lake_adapter = (env.get("CODESTRATA_DATA_LAKE_ADAPTER") or "").strip().lower()
    wire_ready = ingestion_wire or data_lake_adapter == "s3"

    if ingestion_enabled:
        if not data_lake_bucket:
            raise ValueError(
                "CODESTRATA_INGESTION_ENABLED=true requires CODESTRATA_DATA_LAKE_BUCKET"
            )
        if not wire_ready:
            raise ValueError(
                "CODESTRATA_INGESTION_ENABLED=true requires CODESTRATA_INGESTION_WIRE=true "
                "or CODESTRATA_DATA_LAKE_ADAPTER=s3"
            )
    if (
        deployment_mode == DEPLOYMENT_MODE_PRODUCTION_INGESTION
        and not ingestion_enabled
    ):
        raise ValueError(
            "CODESTRATA_DEPLOYMENT_MODE=production_ingestion requires "
            "CODESTRATA_INGESTION_ENABLED=true"
        )

    community_credentials_secret_id = (
        env.get("CODESTRATA_COMMUNITY_CREDENTIALS_SECRET_ID")
        or DEFAULT_COMMUNITY_CREDENTIALS_SECRET_ID
    ).strip()
    if not community_credentials_secret_id:
        raise ValueError("CODESTRATA_COMMUNITY_CREDENTIALS_SECRET_ID must not be empty")

    default_auth_mode = (
        AUTHENTICATION_MODE_AWS_CREDENTIALS
        if ingestion_enabled
        else AUTHENTICATION_MODE_VERIFIER_UNAVAILABLE
    )
    authentication_mode = (
        env.get("CODESTRATA_AUTHENTICATION_MODE") or default_auth_mode
    ).strip()
    if authentication_mode not in ALLOWED_AUTHENTICATION_MODES:
        raise ValueError("unsupported CODESTRATA_AUTHENTICATION_MODE")
    # Normalize TF alias to the application canonical mode.
    if authentication_mode == AUTHENTICATION_MODE_SECRETS_MANAGER_VERIFIER:
        authentication_mode = AUTHENTICATION_MODE_AWS_CREDENTIALS
    if not ingestion_enabled and authentication_mode != AUTHENTICATION_MODE_VERIFIER_UNAVAILABLE:
        raise ValueError(
            "CODESTRATA_AUTHENTICATION_MODE must remain enabled_verifier_unavailable "
            "when ingestion is disabled"
        )

    rate_limit_mode = (
        env.get("CODESTRATA_RATE_LIMIT_MODE") or RATE_LIMIT_MODE_GATEWAY_PLUS_LOCAL
    ).strip()
    if rate_limit_mode != RATE_LIMIT_MODE_GATEWAY_PLUS_LOCAL:
        raise ValueError("unsupported CODESTRATA_RATE_LIMIT_MODE")

    report_artifacts_bucket = (env.get("CODESTRATA_REPORT_ARTIFACTS_BUCKET") or "").strip()
    report_publishing_enabled = _parse_bool(
        env.get("CODESTRATA_REPORT_PUBLISHING"),
        default=bool(report_artifacts_bucket),
    )
    if report_publishing_enabled and not report_artifacts_bucket:
        raise ValueError(
            "CODESTRATA_REPORT_PUBLISHING=true requires CODESTRATA_REPORT_ARTIFACTS_BUCKET"
        )

    return DeploymentSettings(
        deployment_mode=deployment_mode,
        community_api_version=api_version,
        authentication_enabled=authentication_enabled,
        rate_limit_enabled=rate_limit_enabled,
        ingestion_enabled=ingestion_enabled,
        authentication_mode=authentication_mode,
        rate_limit_mode=rate_limit_mode,
        data_lake_bucket=data_lake_bucket,
        ingestion_wire=wire_ready,
        data_lake_adapter=data_lake_adapter,
        community_credentials_secret_id=community_credentials_secret_id,
        report_artifacts_bucket=report_artifacts_bucket,
        report_publishing_enabled=report_publishing_enabled,
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
