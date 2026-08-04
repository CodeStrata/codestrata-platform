"""Client-type authorization matching."""

from __future__ import annotations

from verification.community_cloud_api.authentication import check_client_matching


def test_client_matching(verification_app) -> None:
    results = check_client_matching(verification_app)
    assert results
    assert all(item.ok for item in results), [r for r in results if not r.ok]
