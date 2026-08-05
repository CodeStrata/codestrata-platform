"""Storage factory mode integration tests (Slice 8.14)."""

from __future__ import annotations

from verification.community_data_lake.storage import check_storage_factory

from .assertions import assert_all_ok


def test_storage_factory_modes() -> None:
    assert_all_ok(check_storage_factory(), label="storage_factory")
