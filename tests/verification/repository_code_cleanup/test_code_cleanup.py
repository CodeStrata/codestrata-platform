"""Tests for Slice 16.3 repository code cleanup."""

from __future__ import annotations

import json

from verification.repository_code_cleanup.contract import (
    CLASSIFICATIONS,
    POLICY_RELATIVE,
    REMOVED_PATHS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.repository_code_cleanup.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.repository_code_cleanup.runner import build_report, run


def test_policy() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["schema"] == "repository-code-cleanup-policy:1.0"
    assert policy["evidence_required_deletion"] is True
    assert policy["production_ingestion_enabled"] is False
    assert policy.get("start_slice_16_4", False) is True
    assert policy.get("start_slice_16_5", False) is True
    assert policy.get("start_slice_16_6", False) is True
    assert policy.get("start_slice_16_7", False) is True
    assert policy.get("start_slice_16_8", False) is True
    assert policy.get("start_slice_16_9", False) is True
    assert policy.get("start_slice_16_10", False) is True
    assert policy.get("start_epic_17", False) is True
    assert set(policy["classifications"]) == set(CLASSIFICATIONS)


def test_removed_paths_absent() -> None:
    root = monorepo_root_from_here()
    for rel in REMOVED_PATHS:
        assert not (root / rel).exists(), rel


def test_build_report() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.release_posture.get("start_epic_17", False) is True
    assert report.release_posture["production_ingestion_enabled"] is False
    assert report.cleanup_register
    assert report.residency_register
    assert "OWNER_REVIEW_REQUIRED" in report.classification_counts or any(
        r["classification"] == "OWNER_REVIEW_REQUIRED" for r in report.cleanup_register
    )


def test_dual_run() -> None:
    root = monorepo_root_from_here()
    a = build_report(root)
    b = build_report(root)
    assert reports_byte_identical(a.to_dict(), b.to_dict())
    text = dict_to_canonical_json(a.to_dict())
    assert "/Users/" not in text
    assert "timestamp" not in text.lower()


def test_run_writes_report() -> None:
    root = monorepo_root_from_here()
    report = run(root)
    out = root / "reports/verification/sv16-3/repository-code-cleanup-verification.json"
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["verdict"] == report.verdict
    assert payload["removed_paths"]


def test_slice_16_5_absent() -> None:
    root = monorepo_root_from_here()
    assert not (root / "reports/verification/sv17-2").exists()
    assert not (root / "cursor-plugin").exists()
