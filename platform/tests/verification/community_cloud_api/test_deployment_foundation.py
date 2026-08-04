"""Production-foundation fail-closed verification."""

from __future__ import annotations

from verification.community_cloud_api.deployment_foundation import (
    check_deployment_foundation,
)


def test_deployment_foundation() -> None:
    results = check_deployment_foundation()
    assert results
    assert all(item.ok for item in results), [r for r in results if not r.ok]
