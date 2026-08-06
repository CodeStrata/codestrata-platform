"""Contract/schema tests for Slice 10.9."""

from __future__ import annotations

from verification.anonymous_analytics_completion.contract import (
    EPIC,
    EXPECTED_SLICE_COUNT,
    PRIVACY_EXPECTED_CHECKS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)


def test_contract_tokens() -> None:
    contract = default_contract()
    assert contract.schema_name == SCHEMA_NAME
    assert contract.schema_version == SCHEMA_VERSION
    assert contract.epic == EPIC == "10"
    assert contract.expected_slice_count == EXPECTED_SLICE_COUNT == 9
    assert contract.start_epic_11 is False
    assert contract.no_commit is True
    assert contract.no_tag is True
    assert contract.no_publish is True
    assert contract.no_deploy is True
    assert contract.no_shared_runtime_schema is True
    assert contract.assessment_schema_version == "1.2"


def test_privacy_expected_checks_matches_live_1_0_8() -> None:
    assert PRIVACY_EXPECTED_CHECKS == 157


def test_monorepo_root_resolves() -> None:
    root = monorepo_root_from_here()
    assert (root / "engine").is_dir()
    assert (root / "vscode-plugin").is_dir()
    assert (root / "verification" / "anonymous_analytics_privacy").is_dir()
    assert (root / "verification" / "anonymous_analytics_completion").is_dir()
