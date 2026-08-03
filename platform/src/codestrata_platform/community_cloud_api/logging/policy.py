"""Community Cloud logging policy factory."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.logging.models import (
    COMMUNITY_LOGGING_POLICY_URN,
    CommunityLoggingPolicy,
)

ACTIVE_COMMUNITY_LOGGING_POLICY = COMMUNITY_LOGGING_POLICY_URN


def default_logging_policy() -> CommunityLoggingPolicy:
    return CommunityLoggingPolicy.default()


def assert_supported_logging_policy(
    policy: CommunityLoggingPolicy,
) -> CommunityLoggingPolicy:
    if policy.policy_version != COMMUNITY_LOGGING_POLICY_URN:
        raise ValueError(f"unsupported logging policy: {policy.policy_version}")
    return policy
