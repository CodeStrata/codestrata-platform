"""SV.9 verification contract tests."""

from __future__ import annotations

from verification.community_data_lake.contract import (
    COMMUNITY_DATA_LAKE_VERIFICATION_ID,
    COMMUNITY_DATA_LAKE_VERIFICATION_VERSION,
    default_contract,
)


def test_contract_schema_ids() -> None:
    contract = default_contract()
    assert contract.verification_id == COMMUNITY_DATA_LAKE_VERIFICATION_ID
    assert contract.schema_version == COMMUNITY_DATA_LAKE_VERIFICATION_VERSION
    assert COMMUNITY_DATA_LAKE_VERIFICATION_ID == "community-data-lake-verification"
