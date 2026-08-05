"""Epic 8 production unwired posture tests (Slice 8.15)."""

from __future__ import annotations

from verification.community_data_lake_completion.production import check_production


def test_production_fail_closed_and_unwired() -> None:
    failures = [item for item in check_production() if not item.ok]
    assert failures == []
