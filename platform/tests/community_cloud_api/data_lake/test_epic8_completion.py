"""Epic 8 completion slice markers (Slice 8.15)."""

from __future__ import annotations

from verification.community_data_lake_completion.contract import (
    EPIC,
    SLICES_COMPLETED,
)


def test_epic_is_8() -> None:
    assert EPIC == "8"


def test_slices_completed_8_1_through_8_15() -> None:
    assert SLICES_COMPLETED == tuple(f"8.{index}" for index in range(1, 16))
    assert SLICES_COMPLETED[0] == "8.1"
    assert SLICES_COMPLETED[-1] == "8.15"
    assert len(SLICES_COMPLETED) == 15
