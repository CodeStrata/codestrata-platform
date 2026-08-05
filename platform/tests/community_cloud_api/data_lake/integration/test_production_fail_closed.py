"""Production fail-closed integration tests (Slice 8.14)."""

from __future__ import annotations

from verification.community_data_lake.scenarios import check_production_fail_closed

from .assertions import assert_all_ok


def test_production_fail_closed() -> None:
    assert_all_ok(check_production_fail_closed(), label="production_fail_closed")
