"""Contract tests for Slice 9.14."""

from __future__ import annotations

from verification.privacy_first_telemetry import (
    PRIVACY_FIRST_TELEMETRY_VERIFICATION_ID,
    PRIVACY_FIRST_TELEMETRY_VERIFICATION_VERSION,
)
from verification.privacy_first_telemetry.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)


def test_package_identity() -> None:
    assert PRIVACY_FIRST_TELEMETRY_VERIFICATION_ID == (
        "sv9-14-cross-client-telemetry-privacy"
    )
    assert PRIVACY_FIRST_TELEMETRY_VERIFICATION_VERSION == "1.0.0"
    assert SCHEMA_NAME == "cross-client-telemetry-privacy-verification"
    assert SCHEMA_VERSION == "1.0.0"


def test_contract_gates() -> None:
    contract = default_contract()
    assert contract.start_slice_915 is False
    assert contract.no_shared_runtime_schema is True
    assert contract.no_http_default is True
    assert contract.no_vscode_http is True
    assert contract.no_cursor_telemetry is True
    assert contract.no_installation_identity is True
    assert contract.no_persisted_consent is True
    assert contract.assessment_schema_version == "1.2"


def test_monorepo_root() -> None:
    root = monorepo_root_from_here()
    assert (root / "engine" / "pyproject.toml").is_file()
    assert (root / "vscode-plugin" / "package.json").is_file()
