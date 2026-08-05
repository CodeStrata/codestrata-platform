"""Infrastructure contract integration tests (Slice 8.14)."""

from __future__ import annotations

from verification.community_data_lake.infrastructure import check_infrastructure_static

from .assertions import assert_all_ok


def test_infrastructure_contract() -> None:
    assert_all_ok(check_infrastructure_static(), label="infrastructure")
