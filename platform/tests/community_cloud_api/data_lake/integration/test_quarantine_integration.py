"""Quarantine integration tests (Slice 8.14)."""

from __future__ import annotations

from verification.community_data_lake.quarantine import (
    check_quarantine_fake_s3,
    check_quarantine_in_memory,
)

from .assertions import assert_all_ok


def test_quarantine_in_memory() -> None:
    assert_all_ok(check_quarantine_in_memory(), label="quarantine_in_memory")


def test_quarantine_fake_s3() -> None:
    assert_all_ok(check_quarantine_fake_s3(), label="quarantine_fake_s3")
