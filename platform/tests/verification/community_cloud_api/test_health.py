"""Health endpoint verification."""

from __future__ import annotations

from verification.community_cloud_api.endpoints import check_health


def test_health(verification_app) -> None:
    results = check_health(verification_app)
    assert results
    assert all(item.ok for item in results)
