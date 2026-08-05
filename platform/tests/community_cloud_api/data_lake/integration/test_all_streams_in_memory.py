"""In-memory accepted-stream integration tests (Slice 8.14)."""

from __future__ import annotations

from verification.community_data_lake.streams import check_accepted_streams_in_memory

from .assertions import assert_all_ok


def test_all_streams_in_memory() -> None:
    assert_all_ok(check_accepted_streams_in_memory(), label="in_memory_streams")
