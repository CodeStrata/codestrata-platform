"""Authentication policy tests."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.authentication import (
    COMMUNITY_AUTHENTICATION_POLICY_URN,
    CommunityAuthenticationPolicy,
)


def test_stable_policy_token_and_version() -> None:
    policy = CommunityAuthenticationPolicy.default()
    assert policy.policy_version == COMMUNITY_AUTHENTICATION_POLICY_URN
    assert policy.policy_token() == COMMUNITY_AUTHENTICATION_POLICY_URN
    assert COMMUNITY_AUTHENTICATION_POLICY_URN.endswith(":1.0")


def test_health_public_ingestion_protected() -> None:
    policy = CommunityAuthenticationPolicy.default()
    assert policy.is_public_route("health.get")
    for route in policy.protected_route_ids:
        assert policy.is_protected_route(route)
    assert "health.get" not in policy.protected_route_ids


def test_invalid_classification_rejected() -> None:
    with pytest.raises(ValueError):
        CommunityAuthenticationPolicy(public_route_ids=("telemetry.ingest",))
    with pytest.raises(ValueError):
        CommunityAuthenticationPolicy(credential_min_length=5)


def test_deterministic_serialization() -> None:
    assert (
        CommunityAuthenticationPolicy.default().to_stable_dict()
        == CommunityAuthenticationPolicy.default().to_stable_dict()
    )


def test_explicit_disabled_mode() -> None:
    policy = CommunityAuthenticationPolicy(enabled=False)
    assert policy.enabled is False
    assert policy.policy_version == COMMUNITY_AUTHENTICATION_POLICY_URN
