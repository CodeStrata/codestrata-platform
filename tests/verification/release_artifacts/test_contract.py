"""SV.16 contract tests."""

from __future__ import annotations

from verification.release_artifacts import RELEASE_ARTIFACTS_ID, RELEASE_ARTIFACTS_VERSION
from verification.release_artifacts.contract import (
    INTENDED_RELEASE_VERSION,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)


def test_package_identity() -> None:
    assert RELEASE_ARTIFACTS_ID == "sv16-release-artifact-verification"
    assert RELEASE_ARTIFACTS_VERSION == "1.0.0"
    assert SCHEMA_NAME == "release-artifact-verification"
    assert SCHEMA_VERSION == "1.0.0"


def test_contract_gates() -> None:
    contract = default_contract()
    assert contract.start_sv17 is False
    assert contract.no_tag is True
    assert contract.no_publish is True
    assert contract.no_deploy is True
    assert contract.no_tofu_apply is True
    assert contract.intended_release_version == INTENDED_RELEASE_VERSION


def test_monorepo_root() -> None:
    root = monorepo_root_from_here()
    assert (root / "engine" / "pyproject.toml").is_file()
    assert (root / "pyproject.toml").is_file()
