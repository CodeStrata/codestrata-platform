"""SV.15 contract tests."""

from __future__ import annotations

from verification.deterministic_outputs.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    TARGET_REPOSITORY_COUNT,
    default_contract,
)


def test_contract_constants() -> None:
    c = default_contract()
    assert c.schema_name == SCHEMA_NAME == "deterministic-output-verification"
    assert c.schema_version == SCHEMA_VERSION == "1.0.0"
    assert c.target_repository_count == TARGET_REPOSITORY_COUNT == 22
    assert c.start_sv16 is False
    assert c.redesign_id_schemes is False
    assert c.broad_normalization is False
    assert c.full_22_reassess_by_default is False
