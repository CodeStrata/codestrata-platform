"""Retry decision classification."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.event_identity.fingerprint import (
    FingerprintError,
    compute_payload_fingerprint,
)
from codestrata_platform.community_cloud_api.event_identity.identifiers import (
    build_event_key,
    build_safe_event_reference,
)
from codestrata_platform.community_cloud_api.event_identity.models import (
    CommunityEventIdentityPolicy,
    EventIdentityScope,
    RetryDecision,
    RetryStatus,
)
from codestrata_platform.community_cloud_api.event_identity.ports import EventIdentityLookup


def classify_retry(
    *,
    scope: EventIdentityScope,
    payload: dict[str, object],
    lookup: EventIdentityLookup | None,
    policy: CommunityEventIdentityPolicy | None = None,
) -> RetryDecision:
    """Classify a submission against an optional authoritative lookup.

    Without a lookup, status is ``unavailable`` — never claim ``first_seen``.
    """

    active = policy or CommunityEventIdentityPolicy.default()
    event_key = build_event_key(scope, policy=active)
    safe_ref = build_safe_event_reference(event_key, policy=active)
    try:
        fingerprint = compute_payload_fingerprint(payload, policy=active)
    except FingerprintError:
        # Fingerprint failure is not a retry decision; callers validate first.
        raise

    if lookup is None:
        return RetryDecision(
            status=RetryStatus.UNAVAILABLE,
            event_key=event_key,
            payload_fingerprint=fingerprint,
            reason="lookup_unavailable",
            safe_event_reference=safe_ref,
            limitations=("no_authoritative_identity_store",),
        )

    try:
        existing = lookup.get(event_key)
    except Exception:  # noqa: BLE001 — identity store errors fail closed as unavailable
        return RetryDecision(
            status=RetryStatus.UNAVAILABLE,
            event_key=event_key,
            payload_fingerprint=fingerprint,
            reason="lookup_unavailable",
            safe_event_reference=safe_ref,
            limitations=("authoritative_identity_store_unavailable",),
        )
    if existing is None:
        return RetryDecision(
            status=RetryStatus.FIRST_SEEN,
            event_key=event_key,
            payload_fingerprint=fingerprint,
            reason="identity_not_found",
            safe_event_reference=safe_ref,
        )

    if existing.payload_fingerprint == fingerprint:
        return RetryDecision(
            status=RetryStatus.EXACT_RETRY,
            event_key=event_key,
            payload_fingerprint=fingerprint,
            existing_payload_fingerprint=existing.payload_fingerprint,
            reason="fingerprint_match",
            safe_event_reference=safe_ref,
        )

    return RetryDecision(
        status=RetryStatus.CONFLICTING_RETRY,
        event_key=event_key,
        payload_fingerprint=fingerprint,
        existing_payload_fingerprint=existing.payload_fingerprint,
        reason="fingerprint_mismatch",
        safe_event_reference=safe_ref,
    )
