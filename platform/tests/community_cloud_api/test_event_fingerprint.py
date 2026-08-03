"""Payload fingerprint tests."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.event_identity import (
    CommunityEventIdentityPolicy,
    FingerprintError,
    compute_payload_fingerprint,
)


def test_fingerprint_stable_and_order_invariant() -> None:
    left = compute_payload_fingerprint({"b": 2, "a": 1, "tags": ["x", "y"]})
    right = compute_payload_fingerprint({"tags": ["x", "y"], "a": 1, "b": 2})
    assert left == right
    assert left.startswith("fp:")
    assert len(left) == 3 + 64


def test_list_order_preserved_material_change() -> None:
    a = compute_payload_fingerprint({"tags": ["x", "y"]})
    b = compute_payload_fingerprint({"tags": ["y", "x"]})
    assert a != b


def test_material_value_change_changes_fingerprint() -> None:
    a = compute_payload_fingerprint({"event_type": "cli.started", "count": 1})
    b = compute_payload_fingerprint({"event_type": "cli.started", "count": 2})
    assert a != b


def test_excluded_transport_metadata_ignored() -> None:
    base = {"event_type": "cli.started", "label": "ok"}
    with_transport = {
        **base,
        "request_id": "req-1",
        "retry_count": 3,
        "received_at": "2026-01-01T00:00:00Z",
        "transport_metadata": {"x": 1},
        "server_metadata": {"y": 2},
    }
    assert compute_payload_fingerprint(base) == compute_payload_fingerprint(with_transport)


def test_secret_like_rejected_before_hashing() -> None:
    with pytest.raises(FingerprintError):
        compute_payload_fingerprint(
            {"note": "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----"}
        )
    with pytest.raises(FingerprintError):
        compute_payload_fingerprint({"note": "Bearer supersecrettokenvalue"})


def test_unsupported_types_rejected() -> None:
    with pytest.raises(FingerprintError):
        compute_payload_fingerprint({"x": object()})  # type: ignore[dict-item]


def test_policy_exclusion_cannot_drop_identity_fields() -> None:
    with pytest.raises(ValueError):
        CommunityEventIdentityPolicy(fingerprint_excluded_fields=("event_type",))
