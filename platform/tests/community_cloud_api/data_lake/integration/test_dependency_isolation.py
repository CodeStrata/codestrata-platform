"""Dependency isolation integration tests (Slice 8.14)."""

from __future__ import annotations

from verification.community_data_lake.scenarios import check_dependency_isolation

from .assertions import assert_all_ok


def test_dependency_isolation() -> None:
    assert_all_ok(check_dependency_isolation(), label="dependency_isolation")
