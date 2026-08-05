"""Privacy contract integration tests (Slice 8.14)."""

from __future__ import annotations

from verification.community_data_lake.safety import check_privacy

from .assertions import assert_all_ok


def test_privacy_contract() -> None:
    assert_all_ok(check_privacy(), label="privacy")
