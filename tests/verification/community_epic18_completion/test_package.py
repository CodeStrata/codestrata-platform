"""Smoke tests for Slice 18.8 Epic 18 completion verification."""

from __future__ import annotations

import json

from verification.community_epic18_completion.contract import (
    CONTRACT_RELATIVE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SUITE_ID,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_epic18_completion.determinism import reports_byte_identical
from verification.community_epic18_completion.helpers import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_epic18_completion.runner import build_report, write_report


def test_contract_boundary() -> None:
    c = default_contract()
    assert c.start_slice_18_8 is True
    assert c.start_release_readiness_epic is False
    assert SCHEMA_NAME == "community-epic18-completion-verification"
    assert SCHEMA_VERSION == "1.0.0"
    assert SUITE_ID == "sv18-8"
    assert POLICY_REQUIRED_VALUES["epic18_transparency_work_complete"] is True
    assert POLICY_REQUIRED_VALUES["no_cli_publish"] is True
    assert POLICY_REQUIRED_VALUES["start_release_readiness_epic"] is False


def test_policy_and_contract_files() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    for key, expected in POLICY_REQUIRED_VALUES.items():
        assert policy.get(key) == expected, key
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert "community-epic18-completion-verification" in contract.get("$id", "")


def test_build_report_smoke() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.slice == "18.8"
    assert report.suite_id == SUITE_ID
    assert report.epic18_boundary["start_slice_18_8"] is True
    assert report.epic18_boundary["start_release_readiness_epic"] is False
    assert report.freeze_confirmations["epic19_not_started"] is True
    assert report.claim_inventory.get("total") == 70
    assert report.epic_verdict in {
        "EPIC_COMPLETE",
        "EPIC_COMPLETE_WITH_DOCUMENTED_LIMITATIONS",
        "EPIC_BLOCKED",
    }
    text = dict_to_canonical_json(report.to_dict())
    assert "/Users/" not in text
    assert "timestamp" not in text
    assert "cscc_v1_" not in text or "cscc_v1_[redacted]" in text
    assert report_text_is_safe(text)
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}


def test_determinism_and_write() -> None:
    root = monorepo_root_from_here()
    r1 = build_report(root)
    r2 = build_report(root)
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())
    path = write_report(root, r2)
    assert path.name == "community-epic18-completion-verification.json"
    assert "sv18-8" in path.as_posix()
    text = path.read_text(encoding="utf-8")
    assert "timestamp" not in text
    assert "/Users/" not in text
    assert report_text_is_safe(text)


def test_runner_import() -> None:
    from verification.community_epic18_completion.runner import main

    assert callable(main)
