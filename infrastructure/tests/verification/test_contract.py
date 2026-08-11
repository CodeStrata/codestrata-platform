"""SV.9 contract constants."""

from __future__ import annotations

from infrastructure.verification.contract import (
    AUTHENTICATION_MODE,
    DEPLOYMENT_MODE,
    PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_ID,
    PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_VERSION,
    REQUIRED_OPENTOFU,
)


def test_contract_constants() -> None:
    assert (
        PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_ID
        == "platform-deployment-foundation-verification"
    )
    assert PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_VERSION == "1.0.0"
    assert DEPLOYMENT_MODE == "production_ingestion"
    assert AUTHENTICATION_MODE == "enabled_secrets_manager_verifier"
    assert REQUIRED_OPENTOFU == ">= 1.6.0"
