"""Tests for Slice 16.2 repository documentation verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.repository_documentation.contract import (
    CLASSIFICATIONS,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.repository_documentation.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.repository_documentation.runner import build_report, run


def test_policy_and_guide() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["schema"] == "repository-documentation-policy:1.0"
    assert policy["documentation_only"] is True
    assert policy["product_version"] == "0.2.0"
    assert policy["start_slice_16_3"] is True
    assert policy.get("start_slice_16_4", False) is True
    assert policy.get("start_slice_16_5", False) is True
    assert policy.get("start_slice_16_6", False) is True
    assert policy.get("start_slice_16_7", False) is True
    assert policy.get("start_slice_16_8", False) is True
    assert policy.get("start_slice_16_9", False) is True
    assert policy.get("start_slice_16_10", False) is True
    assert policy.get("start_epic_17", False) is True
    assert set(policy["classifications"]) == set(CLASSIFICATIONS)
    assert (root / "platform/docs/repository-cleanup/community-documentation-cleanup.md").is_file()


def test_build_report() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.release_posture.get("start_epic_17", False) is True
    assert report.release_posture["historical_knowledge_deleted"] is False
    assert report.authoritative_document_registry["installation"] == "docs/getting-started/install.md"
    assert "0.2.0" in (root / "README.md").read_text(encoding="utf-8")


def test_dual_run_identical() -> None:
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
    out = root / "reports/verification/sv16-2/repository-documentation-verification.json"
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["verdict"] == report.verdict
    assert "documentation_inventory" in payload
    assert "authoritative_document_registry" in payload
    assert "broken_links" in payload


def test_slice_16_5_absent() -> None:
    root = monorepo_root_from_here()
    assert not (root / "reports/verification/sv17-2").exists()
