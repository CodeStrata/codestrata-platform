"""SV.14 contract tests."""

from __future__ import annotations

from verification.cross_schema_compatibility.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    TARGET_REPOSITORY_COUNT,
    default_contract,
)


def test_contract_constants() -> None:
    c = default_contract()
    assert c.schema_name == SCHEMA_NAME == "cross-schema-compatibility-verification"
    assert c.schema_version == SCHEMA_VERSION == "1.0.0"
    assert c.target_repository_count == TARGET_REPOSITORY_COUNT == 22
    assert c.start_sv15 is False
    assert c.redesign_schemas is False
    assert c.speculative_aliases is False
    assert c.migrate_stored_artifacts is False
