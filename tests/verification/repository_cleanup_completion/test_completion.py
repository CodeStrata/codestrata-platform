"""Tests for Slice 16.10 Epic 16 completion."""

from __future__ import annotations

import json

from verification.repository_cleanup_completion.contract import (
    CONTRACT_RELATIVE,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.repository_cleanup_completion.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.repository_cleanup_completion.runner import build_report, main


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_16_10 is True
    assert c.start_epic_17 is True
    assert c.start_slice_17_2 is False
    assert c.epic_complete is True
    assert c.no_publish is True


def test_policy_gates() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("start_slice_16_10") is True
    assert policy.get("start_epic_17") is True
    assert policy.get("start_slice_17_2") is False
    assert policy.get("epic_complete") is True
    assert policy.get("slice_count") == 10
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == "repository-cleanup-completion-verification:1.0.0"


def test_slice_17_2_absent() -> None:
    root = monorepo_root_from_here()
    assert not (root / "reports/verification/sv17-2").exists()
    assert not (root / "verification/infrastructure_production").exists()


def test_build_report_matrix_and_safety() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.release_posture.get("start_epic_17") is True
    assert report.release_posture.get("start_slice_17_2") is False
    assert report.release_posture.get("epic_16_complete") is True
    assert len(report.slice_completion_matrix) == 10
    text = dict_to_canonical_json(report.to_dict())
    assert "/Users/" not in text
    assert '"timestamp"' not in text.lower()


def test_runner_main_and_determinism() -> None:
    code = main()
    assert code in {0, 1}
    root = monorepo_root_from_here()
    path = root / "reports/verification/sv16-10/repository-cleanup-completion-verification.json"
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["slice"] == "16.10"
    assert data["verdict"] in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}
    r1 = build_report(root)
    r2 = build_report(root)
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())
