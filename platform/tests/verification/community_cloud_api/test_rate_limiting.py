"""Rate-limit verification (policy 1.1)."""

from __future__ import annotations

from verification.community_cloud_api.rate_limiting import check_rate_limiting


def test_rate_limiting() -> None:
    results = check_rate_limiting()
    assert results
    assert all(item.ok for item in results), [r for r in results if not r.ok]
