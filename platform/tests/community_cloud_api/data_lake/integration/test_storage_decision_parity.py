"""Storage decision parity integration tests (Slice 8.14)."""

from __future__ import annotations

from verification.community_data_lake.storage import check_adapter_parity_matrix

from .assertions import assert_all_ok


def test_storage_decision_parity() -> None:
    checks, matrix = check_adapter_parity_matrix()
    assert_all_ok(checks, label="adapter_matrix")
    assert set(matrix) == {"unavailable", "in_memory", "fake_s3"}
