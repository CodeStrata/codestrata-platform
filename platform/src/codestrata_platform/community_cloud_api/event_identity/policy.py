"""Event-identity policy factory."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.event_identity.models import (
    COMMUNITY_EVENT_IDENTITY_POLICY_URN,
    CommunityEventIdentityPolicy,
)

ACTIVE_EVENT_IDENTITY_POLICY = COMMUNITY_EVENT_IDENTITY_POLICY_URN


def default_event_identity_policy() -> CommunityEventIdentityPolicy:
    return CommunityEventIdentityPolicy.default()


def assert_supported_event_identity_policy(
    policy: CommunityEventIdentityPolicy,
) -> CommunityEventIdentityPolicy:
    if policy.policy_token != COMMUNITY_EVENT_IDENTITY_POLICY_URN:
        raise ValueError(f"unsupported event identity policy: {policy.policy_token}")
    return policy
