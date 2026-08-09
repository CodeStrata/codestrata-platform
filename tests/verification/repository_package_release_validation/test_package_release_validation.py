"""Tests for Slice 16.9 package & release artifact validation."""

from __future__ import annotations

import json
from pathlib import Path

from verification.repository_package_release_validation.contract import (
    CONTRACT_RELATIVE,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.repository_package_release_validation.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.repository_package_release_validation.runner import build_report, main


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_16_9 is True
    assert c.start_slice_16_10 is True
    assert getattr(c, "start_epic_17", False) is True
    assert c.no_publish is True
    assert c.no_deploy is True
    assert c.no_commit is True


def test_policy_and_contract_files() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("start_slice_16_9", False) is True
    assert policy.get("start_slice_16_10", False) is True
    assert policy.get("start_epic_17", False) is True
    assert policy.get("schema") == "repository-package-release-validation-policy:1.0"
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == "repository-package-release-validation-verification:1.0.0"


def test_epic_17_absent() -> None:
    root = monorepo_root_from_here()
    assert not (root / "reports/verification/sv17-2").exists()
    assert not (root / "verification/infrastructure_production").exists()
    assert not (root / "verification/release_readiness").exists()


def test_build_report_safety() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.release_posture.get("start_epic_17", False) is True
    assert report.release_posture.get("no_publish") is True
    text = dict_to_canonical_json(report.to_dict())
    assert "/Users/" not in text
    assert '"timestamp"' not in text.lower()


def test_runner_main() -> None:
    code = main()
    assert code in {0, 1}
    root = monorepo_root_from_here()
    report = root / "reports/verification/sv16-9/repository-package-release-validation-verification.json"
    assert report.is_file()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["schema"] == SCHEMA_NAME
    assert data["slice"] == "16.9"
    assert data["verdict"] in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}
