"""Tests for Slice 16.6 repository storage & generated cleanup."""

from __future__ import annotations

import json

from verification.repository_storage_generated_cleanup.contract import (
    CLASSIFICATIONS,
    POLICY_RELATIVE,
    PROTECTED_PATHS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.repository_storage_generated_cleanup.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.repository_storage_generated_cleanup.runner import build_report, run


def test_policy() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["schema"] == "repository-storage-generated-cleanup-policy:1.0"
    assert policy["no_repository_relocation"] is True
    assert policy["no_dependency_changes"] is True
    assert policy["start_slice_16_7"] is True
    assert policy.get("start_slice_16_8", False) is True
    assert policy.get("start_slice_16_9", False) is True
    assert policy.get("start_slice_16_10", False) is True
    assert policy.get("start_epic_17", False) is False
    assert set(policy["classifications"]) == set(CLASSIFICATIONS)


def test_protected_assets_present() -> None:
    root = monorepo_root_from_here()
    for rel in PROTECTED_PATHS:
        assert (root / rel).exists(), rel


def test_local_state_absent() -> None:
    root = monorepo_root_from_here()
    assert not (root / ".codestrata").exists()
    assert not (root / "engine/.codestrata").exists()
    assert not (root / ".export-staging").exists()
    assert not (root / "infrastructure/production/.terraform").exists()


def test_build_report() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.release_posture.get("start_epic_17", False) is False
    assert report.release_posture["dependencies_changed"] is False


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
    out = root / "reports/verification/sv16-6/repository-storage-generated-cleanup-verification.json"
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["verdict"] == report.verdict
    assert payload["artifact_register_relative"]


def test_epic_17_absent() -> None:
    root = monorepo_root_from_here()
    assert not (root / "reports/verification/sv17-1").exists()
