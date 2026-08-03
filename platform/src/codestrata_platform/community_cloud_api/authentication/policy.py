"""Authentication policy factory."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.authentication.models import (
    COMMUNITY_AUTHENTICATION_POLICY_URN,
    CommunityAuthenticationPolicy,
)

ACTIVE_AUTHENTICATION_POLICY = COMMUNITY_AUTHENTICATION_POLICY_URN


def default_authentication_policy() -> CommunityAuthenticationPolicy:
    return CommunityAuthenticationPolicy.default()


def assert_supported_authentication_policy(
    policy: CommunityAuthenticationPolicy,
) -> CommunityAuthenticationPolicy:
    if policy.policy_version != COMMUNITY_AUTHENTICATION_POLICY_URN:
        raise ValueError(f"unsupported authentication policy: {policy.policy_version}")
    return policy


def validate_authentication_policy(
    policy: CommunityAuthenticationPolicy,
) -> CommunityAuthenticationPolicy:
    return assert_supported_authentication_policy(policy)
