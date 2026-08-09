"""Tests for Slice 16.1 repository inventory verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.repository_inventory.contract import (
    CLASSIFICATIONS,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.repository_inventory.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.repository_inventory.runner import build_report, run


def test_policy_exists_and_audit_only() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["schema"] == "repository-cleanup-policy:1.0"
    assert policy["audit_only"] is True
    assert policy["start_slice_16_2"] is True
    assert policy.get("start_slice_16_5", False) is True
    assert policy.get("start_slice_16_6", False) is True
    assert policy.get("start_slice_16_7", False) is True
    assert policy.get("start_slice_16_8", False) is True
    assert policy.get("start_slice_16_9", False) is True
    assert policy.get("start_slice_16_10", False) is True
    assert policy.get("start_epic_17", False) is True
    assert policy["delete_forbidden_in_16_1"] is True
    assert set(policy["classifications"]) == set(CLASSIFICATIONS)


def test_build_report_pass_with_limitations() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.release_posture["cleanup_performed"] is False
    assert report.release_posture.get("start_epic_17", False) is True
    assert report.inventory_summary["entry_count"] > 0
    assert "engine" in report.area_counts
    assert sum(report.classification_counts.values()) >= report.inventory_summary["entry_count"]


def test_dual_run_byte_identical(tmp_path: Path) -> None:
    root = monorepo_root_from_here()
    a = build_report(root)
    b = build_report(root)
    assert reports_byte_identical(a.to_dict(), b.to_dict())
    text = dict_to_canonical_json(a.to_dict())
    assert "/Users/" not in text
    assert '"timestamp"' not in text.lower()


def test_run_writes_sv16_1_report() -> None:
    root = monorepo_root_from_here()
    report = run(root)
    out = root / "reports/verification/sv16-1/repository-inventory-verification.json"
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == SCHEMA_NAME
    assert payload["verdict"] == report.verdict
    assert "duplicate_candidates" in payload
    assert "stale_candidates" in payload
    assert "delete_candidates" in payload
    assert "archive_candidates" in payload
    assert "owner_review_items" in payload
    assert payload["release_posture"]["files_deleted"] is False


def test_slice_16_5_not_started() -> None:
    root = monorepo_root_from_here()
    assert not (root / "reports/verification/sv17-2").exists()
