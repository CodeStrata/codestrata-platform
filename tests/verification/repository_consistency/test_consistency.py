"""Tests for Slice 16.8 repository consistency validation."""

from __future__ import annotations

import json
from pathlib import Path

from verification.repository_consistency.contract import (
    OWNER_REGISTER_RELATIVE,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.repository_consistency.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.repository_consistency.runner import build_report, main


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_16_8 is True
    assert c.start_slice_16_9 is True
    assert c.start_slice_16_10 is True
    assert getattr(c, "start_epic_17", False) is True
    assert c.no_commit is True
    assert c.no_publish is True
    assert c.no_deploy is True


def test_policy_gates() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("start_slice_16_8", False) is True
    assert policy.get("start_slice_16_9", False) is True
    assert policy.get("start_slice_16_10", False) is True
    assert policy.get("start_epic_17", False) is True
    assert policy.get("schema") == "repository-consistency-policy:1.0"


def test_owner_register_present() -> None:
    root = monorepo_root_from_here()
    data = json.loads((root / OWNER_REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert data.get("schema") == "repository-owner-review-register:1.0"
    assert len(data.get("items", [])) >= 10
    assert data.get("rules", {}).get("no_silent_delete") is True


def test_epic_17_absent() -> None:
    root = monorepo_root_from_here()
    assert not (root / "reports/verification/sv17-2").exists()
    assert not (root / "verification/infrastructure_production").exists()


def test_build_report_and_determinism() -> None:
    root = monorepo_root_from_here()
    r1 = build_report(root)
    r2 = build_report(root)
    assert r1.schema == SCHEMA_NAME
    assert r1.schema_version == SCHEMA_VERSION
    assert r1.release_posture.get("start_slice_16_10", False) is False
    assert r1.release_posture.get("start_slice_16_9", False) is True
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())
    text = dict_to_canonical_json(r1.to_dict())
    assert "/Users/" not in text
    assert '"timestamp"' not in text.lower()


def test_runner_main() -> None:
    code = main()
    assert code in {0, 1}
    root = monorepo_root_from_here()
    report = root / "reports/verification/sv16-8/repository-consistency-verification.json"
    assert report.is_file()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["schema"] == SCHEMA_NAME
    assert data["slice"] == "16.8"
    assert data["verdict"] in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}
