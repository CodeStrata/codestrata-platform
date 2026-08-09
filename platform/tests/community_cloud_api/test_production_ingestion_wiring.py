"""Additional production wiring tests for Slice 17.7 ingestion enablement gates."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.authentication import (
    UnavailableCommunityCredentialVerifier,
)
from codestrata_platform.community_cloud_api.deployment import (
    create_production_foundation_app,
    load_deployment_settings,
)


def test_load_settings_allows_ingestion_when_bucket_and_wire() -> None:
    settings = load_deployment_settings(
        {
            "CODESTRATA_INGESTION_ENABLED": "true",
            "CODESTRATA_INGESTION_WIRE": "true",
            "CODESTRATA_DATA_LAKE_BUCKET": "codestrata-community-data-lake-production",
        }
    )
    assert settings.ingestion_enabled is True
    assert settings.ingestion_wire is True
    assert settings.data_lake_bucket == "codestrata-community-data-lake-production"


def test_load_settings_allows_ingestion_via_s3_adapter_flag() -> None:
    settings = load_deployment_settings(
        {
            "CODESTRATA_INGESTION_ENABLED": "true",
            "CODESTRATA_DATA_LAKE_ADAPTER": "s3",
            "CODESTRATA_DATA_LAKE_BUCKET": "codestrata-community-data-lake-production",
        }
    )
    assert settings.ingestion_enabled is True
    assert settings.ingestion_wire is True


def test_load_settings_rejects_ingestion_without_bucket() -> None:
    with pytest.raises(ValueError, match="DATA_LAKE_BUCKET"):
        load_deployment_settings(
            {
                "CODESTRATA_INGESTION_ENABLED": "true",
                "CODESTRATA_INGESTION_WIRE": "true",
            }
        )


def test_load_settings_rejects_ingestion_without_wire() -> None:
    with pytest.raises(ValueError, match="INGESTION_WIRE|DATA_LAKE_ADAPTER"):
        load_deployment_settings(
            {
                "CODESTRATA_INGESTION_ENABLED": "true",
                "CODESTRATA_DATA_LAKE_BUCKET": "codestrata-community-data-lake-production",
            }
        )


def test_load_settings_allows_production_ingestion_mode() -> None:
    settings = load_deployment_settings(
        {
            "CODESTRATA_DEPLOYMENT_MODE": "production_ingestion",
            "CODESTRATA_INGESTION_ENABLED": "true",
            "CODESTRATA_INGESTION_WIRE": "true",
            "CODESTRATA_DATA_LAKE_BUCKET": "codestrata-community-data-lake-production",
            "CODESTRATA_AUTHENTICATION_MODE": "enabled_aws_credentials",
        }
    )
    assert settings.deployment_mode == "production_ingestion"
    assert settings.ingestion_enabled is True


def test_load_settings_rejects_ingestion_mode_without_flag() -> None:
    with pytest.raises(ValueError, match="production_ingestion requires"):
        load_deployment_settings(
            {
                "CODESTRATA_DEPLOYMENT_MODE": "production_ingestion",
                "CODESTRATA_INGESTION_ENABLED": "false",
            }
        )


def test_foundation_mode_still_works_with_ingestion_false() -> None:
    app = create_production_foundation_app(settings=load_deployment_settings({}))
    runtime = app.state.community_cloud_authentication_runtime
    assert isinstance(runtime.verifier, UnavailableCommunityCredentialVerifier)
    diagnostic = app.state.community_cloud_deployment_diagnostic
    assert diagnostic["durable_ingestion"] is False
    assert diagnostic["credential_verifier"] == "unavailable"


def test_wiring_ingestion_true_without_bucket_fails_closed() -> None:
    # Settings loader already rejects missing bucket; wiring also guards.
    with pytest.raises(ValueError, match="DATA_LAKE_BUCKET"):
        load_deployment_settings(
            {
                "CODESTRATA_INGESTION_ENABLED": "true",
                "CODESTRATA_INGESTION_WIRE": "true",
                "CODESTRATA_DATA_LAKE_BUCKET": "",
            }
        )
