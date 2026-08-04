"""Community Cloud determinism tests."""

from __future__ import annotations

from verification.deterministic_outputs.community_cloud import check_community_cloud


def test_community_cloud() -> None:
    checks = check_community_cloud()
    assert all(c.ok for c in checks), [(c.name, c.detail) for c in checks if not c.ok]
