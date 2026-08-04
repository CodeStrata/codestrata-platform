"""Route inventory checks."""

from __future__ import annotations

from verification.community_cloud_api.endpoints import check_route_inventory


def test_route_inventory(verification_app) -> None:
    results = check_route_inventory(verification_app)
    assert results
    assert all(item.ok for item in results)
