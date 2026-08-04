"""Payload-limit verification (policy 1.0)."""

from __future__ import annotations

from verification.community_cloud_api.validation import check_payload_limits


def test_payload_limits() -> None:
    results = check_payload_limits()
    assert results
    assert all(item.ok for item in results), [r for r in results if not r.ok]
