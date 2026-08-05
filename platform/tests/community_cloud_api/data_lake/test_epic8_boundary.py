"""Epic 8 ownership boundary tests (Slice 8.15)."""

from __future__ import annotations

from verification.community_data_lake_completion.boundaries import check_boundaries


def test_epic8_boundary_checks_pass() -> None:
    failures = [item for item in check_boundaries() if not item.ok]
    assert failures == []
