"""Slice 8.15 completion verification contract tests."""

from __future__ import annotations

from verification.community_data_lake_completion.contract import (
    COMMUNITY_DATA_LAKE_COMPLETION_ID,
    COMMUNITY_DATA_LAKE_COMPLETION_VERSION,
    SLICES_COMPLETED,
    default_contract,
)


def test_contract_schema_ids() -> None:
    contract = default_contract()
    assert contract.schema_name == COMMUNITY_DATA_LAKE_COMPLETION_ID
    assert contract.schema_version == COMMUNITY_DATA_LAKE_COMPLETION_VERSION
    assert contract.slices_completed == SLICES_COMPLETED
