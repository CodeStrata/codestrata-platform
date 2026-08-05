"""Determinism integration tests (Slice 8.14)."""

from __future__ import annotations

from verification.community_data_lake.determinism import check_determinism

from .assertions import assert_all_ok


def test_determinism() -> None:
    assert_all_ok(check_determinism(), label="determinism")
