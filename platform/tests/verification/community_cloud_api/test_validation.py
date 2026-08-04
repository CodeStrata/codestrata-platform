"""Request validation verification."""

from __future__ import annotations

from verification.community_cloud_api.validation import check_validation


def test_validation(verification_app) -> None:
    results = check_validation(verification_app)
    assert results
    assert all(item.ok for item in results), [r for r in results if not r.ok]
