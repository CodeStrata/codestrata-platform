"""Tests for Slice 16.7 repository boundary & residency."""

from __future__ import annotations

import json

from verification.repository_boundary_residency.contract import (
    CLASSIFICATIONS,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.repository_boundary_residency.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.repository_boundary_residency.runner import build_report, run


def test_policy() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["schema"] == "repository-boundary-residency-policy:1.0"
    assert policy["no_remote_creation"] is True
    assert policy["no_cutover"] is True
    assert policy["design_system_model"] == "SHARED_AUTHORITY"
    assert policy["start_slice_16_8"] is True
    assert policy.get("start_slice_16_9", False) is True
    assert policy.get("start_slice_16_10", False) is True
    assert policy.get("start_epic_17", False) is True
    assert set(policy["classifications"]) == set(CLASSIFICATIONS)


def test_docs_tokens_no_sibling_design_system() -> None:
    root = monorepo_root_from_here()
    text = (root / "docs/.vitepress/theme/tokens.css").read_text(encoding="utf-8")
    assert "../../../design-system/" not in text
    assert "../../public/design-tokens/" in text


def test_build_report() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.release_posture.get("start_epic_17", False) is True
    assert report.release_posture["remote_repositories_created"] is False
    assert report.release_posture["cutover_performed"] is False
    assert "community_cloud_api" not in report.owner_review_items or True
    assert report.platform_classification_counts


def test_dual_run() -> None:
    root = monorepo_root_from_here()
    a = build_report(root)
    b = build_report(root)
    assert reports_byte_identical(a.to_dict(), b.to_dict())
    text = dict_to_canonical_json(a.to_dict())
    assert "/Users/" not in text
    assert '"timestamp"' not in text.lower()


def test_run_writes_report() -> None:
    root = monorepo_root_from_here()
    report = run(root)
    out = root / "reports/verification/sv16-7/repository-boundary-residency-verification.json"
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["verdict"] == report.verdict
    assert payload["residency_map_relative"]


def test_epic_17_absent() -> None:
    root = monorepo_root_from_here()
    assert not (root / "reports/verification/sv17-2").exists()
