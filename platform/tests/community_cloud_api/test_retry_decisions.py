"""Retry decision, conflict error, and lookup-port tests."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.errors import ERROR_EVENT_IDENTITY_CONFLICT
from codestrata_platform.community_cloud_api.event_identity import (
    EventIdentityScope,
    IdempotencyOutcome,
    InMemoryEventIdentityStore,
    RetryStatus,
    StoredEventIdentity,
    build_event_identity_conflict_error,
    build_event_key,
    classify_retry,
    compute_payload_fingerprint,
    default_event_identity_policy,
    record_if_first_seen,
)
from codestrata_platform.community_cloud_api.serialization import dumps_stable


def _scope(**overrides: str) -> EventIdentityScope:
    base = dict(
        api_version="v1",
        client_type="cli",
        event_type="cli.started",
        event_id="evt-retry-0001",
    )
    base.update(overrides)
    return EventIdentityScope(**base)


def test_unavailable_without_lookup() -> None:
    decision = classify_retry(
        scope=_scope(),
        payload={"event_type": "cli.started", "label": "a"},
        lookup=None,
    )
    assert decision.status is RetryStatus.UNAVAILABLE
    assert decision.future_outcome() is None


def test_first_seen_exact_and_conflicting() -> None:
    store = InMemoryEventIdentityStore()
    payload = {"event_type": "cli.started", "label": "a"}
    first = classify_retry(scope=_scope(), payload=payload, lookup=store)
    assert first.status is RetryStatus.FIRST_SEEN
    assert first.future_outcome() is IdempotencyOutcome.ACCEPTED
    record_if_first_seen(decision=first, scope=_scope(), recorder=store)

    exact = classify_retry(
        scope=_scope(),
        payload={"label": "a", "event_type": "cli.started"},
        lookup=store,
    )
    assert exact.status is RetryStatus.EXACT_RETRY
    assert exact.future_outcome() is IdempotencyOutcome.ALREADY_ACCEPTED

    conflict = classify_retry(
        scope=_scope(),
        payload={"event_type": "cli.started", "label": "b"},
        lookup=store,
    )
    assert conflict.status is RetryStatus.CONFLICTING_RETRY
    assert conflict.future_outcome() is IdempotencyOutcome.CONFLICT
    assert conflict.existing_payload_fingerprint == first.payload_fingerprint


def test_memory_store_rejects_conflicting_record() -> None:
    store = InMemoryEventIdentityStore()
    key = build_event_key(_scope())
    fp = compute_payload_fingerprint({"event_type": "cli.started", "label": "a"})
    identity = StoredEventIdentity(
        event_key=key,
        payload_fingerprint=fp,
        event_type="cli.started",
        client_type="cli",
        identity_policy_version=default_event_identity_policy().policy_version,
    )
    store.record(identity)
    try:
        store.record(
            StoredEventIdentity(
                event_key=key,
                payload_fingerprint=compute_payload_fingerprint(
                    {"event_type": "cli.started", "label": "b"}
                ),
                event_type="cli.started",
                client_type="cli",
                identity_policy_version=default_event_identity_policy().policy_version,
            )
        )
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_conflict_error_safe_and_deterministic() -> None:
    left = build_event_identity_conflict_error(
        api_version="v1",
        safe_event_reference="evt-aaaaaaaaaaaa",
    )
    right = build_event_identity_conflict_error(
        api_version="v1",
        safe_event_reference="evt-aaaaaaaaaaaa",
    )
    assert dumps_stable(left) == dumps_stable(right)
    body = left.to_stable_dict()
    assert body["error"]["code"] == ERROR_EVENT_IDENTITY_CONFLICT
    assert "fingerprint" not in dumps_stable(left).decode()
    assert "evt-retry" not in dumps_stable(left).decode()
    assert body["meta"]["http_status"] == 409
