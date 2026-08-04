"""Authentication verification."""

from __future__ import annotations

from verification.community_cloud_api.authentication import check_authentication


def test_authentication(verification_app) -> None:
    results = check_authentication(verification_app)
    assert results
    assert all(item.ok for item in results), [r for r in results if not r.ok]
