"""Retry / event-identity verification."""

from __future__ import annotations

from verification.community_cloud_api.retries import check_retries


def test_retries(verification_app) -> None:
    results = check_retries(verification_app)
    assert results
    assert all(item.ok for item in results), [r for r in results if not r.ok]
