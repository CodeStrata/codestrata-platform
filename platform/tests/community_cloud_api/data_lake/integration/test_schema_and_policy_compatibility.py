"""Schema and policy compatibility integration tests (Slice 8.14)."""

from __future__ import annotations

from verification.community_data_lake.scenarios import check_schema_versions

from .assertions import assert_all_ok


def test_schema_and_policy_compatibility() -> None:
    assert_all_ok(check_schema_versions(), label="schema_versions")
