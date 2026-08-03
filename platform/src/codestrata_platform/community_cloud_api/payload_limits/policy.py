"""Canonical payload-limit policy factory."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.payload_limits.models import (
    PAYLOAD_LIMIT_POLICY_URN,
    PayloadLimitPolicy,
)

# Stable export of the active policy urn for docs/tests.
ACTIVE_PAYLOAD_LIMIT_POLICY = PAYLOAD_LIMIT_POLICY_URN


def default_payload_limit_policy() -> PayloadLimitPolicy:
    """Return the sole Community Cloud payload-limit policy (v1.0)."""

    return PayloadLimitPolicy.default()


def assert_supported_policy(policy: PayloadLimitPolicy) -> PayloadLimitPolicy:
    if policy.policy_version != PAYLOAD_LIMIT_POLICY_URN:
        raise ValueError(f"unsupported payload limit policy: {policy.policy_version}")
    return policy
