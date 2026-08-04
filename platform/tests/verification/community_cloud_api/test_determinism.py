"""Determinism verification."""

from __future__ import annotations

from verification.community_cloud_api.determinism import check_determinism


def test_determinism() -> None:
    results = check_determinism()
    assert results
    assert all(item.ok for item in results), [r for r in results if not r.ok]
