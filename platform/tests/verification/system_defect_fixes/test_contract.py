"""SV.13 contract tests."""

from __future__ import annotations

from verification.system_defect_fixes.contract import (
    AFFECTED_REPOSITORY_IDS,
    DEFECT_ID,
    SCHEMA_VERSION,
    TARGET_REPOSITORY_COUNT,
    default_contract,
)


def test_contract_constants() -> None:
    c = default_contract()
    assert c.defect_id == DEFECT_ID
    assert c.schema_version == SCHEMA_VERSION
    assert c.target_repository_count == TARGET_REPOSITORY_COUNT
    assert c.start_sv14 is False
    assert c.weaken_privacy is False
    assert c.repository_specific_allowlist is False
    assert c.known_issues_bypass is False
    assert set(AFFECTED_REPOSITORY_IDS) == {"dubbo", "juice-shop", "nodegoat"}
