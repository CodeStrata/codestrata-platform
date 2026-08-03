"""Endpoint integration helpers (no production routes in Slice 7.6)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from codestrata_platform.community_cloud_api.event_identity.decisions import classify_retry
from codestrata_platform.community_cloud_api.event_identity.models import (
    CommunityEventIdentityPolicy,
    EventIdentityScope,
    RetryDecision,
    StoredEventIdentity,
)
from codestrata_platform.community_cloud_api.event_identity.ports import (
    EventIdentityLookup,
    EventIdentityRecorder,
)


def evaluate_event_identity(
    *,
    scope: EventIdentityScope,
    payload: Mapping[str, Any],
    lookup: EventIdentityLookup | None,
    policy: CommunityEventIdentityPolicy | None = None,
) -> RetryDecision:
    """Classify retry state for a future ingestion endpoint."""

    return classify_retry(
        scope=scope,
        payload=dict(payload),
        lookup=lookup,
        policy=policy,
    )


def record_if_first_seen(
    *,
    decision: RetryDecision,
    scope: EventIdentityScope,
    recorder: EventIdentityRecorder,
    policy: CommunityEventIdentityPolicy | None = None,
) -> None:
    """Record identity only for first_seen decisions (test/helper use)."""

    active = policy or CommunityEventIdentityPolicy.default()
    if decision.status.value != "first_seen":
        return
    recorder.record(
        StoredEventIdentity(
            event_key=decision.event_key,
            payload_fingerprint=decision.payload_fingerprint,
            event_type=scope.event_type,
            client_type=scope.client_type,
            identity_policy_version=active.policy_version,
        )
    )
