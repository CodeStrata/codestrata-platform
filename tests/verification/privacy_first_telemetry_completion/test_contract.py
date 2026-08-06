"""Contract tests for Slice 9.15."""

from __future__ import annotations

from verification.privacy_first_telemetry_completion import (
    PRIVACY_FIRST_TELEMETRY_COMPLETION_ID,
    PRIVACY_FIRST_TELEMETRY_COMPLETION_VERSION,
)
from verification.privacy_first_telemetry_completion.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SLICES_COMPLETED,
    default_contract,
    monorepo_root_from_here,
)


def test_package_identity() -> None:
    assert PRIVACY_FIRST_TELEMETRY_COMPLETION_ID == (
        "sv9-15-privacy-first-telemetry-completion"
    )
    assert PRIVACY_FIRST_TELEMETRY_COMPLETION_VERSION == "1.0.0"
    assert SCHEMA_NAME == "privacy-first-telemetry-completion-verification"
    assert SCHEMA_VERSION == "1.0.0"
    assert len(SLICES_COMPLETED) == 15
    assert SLICES_COMPLETED[0] == "9.1"
    assert SLICES_COMPLETED[-1] == "9.15"


def test_contract_gates() -> None:
    contract = default_contract()
    assert contract.start_epic_10 is False
    assert contract.no_commit is True
    assert contract.no_tag is True
    assert contract.no_publish is True
    assert contract.no_deploy is True
    assert contract.no_shared_runtime_schema is True
    assert contract.assessment_schema_version == "1.2"


def test_monorepo_root() -> None:
    root = monorepo_root_from_here()
    assert (root / "engine" / "pyproject.toml").is_file()
    assert (root / "vscode-plugin" / "package.json").is_file()
    assert (root / "verification" / "privacy_first_telemetry").is_dir()
