"""Tests for Slice 16.5 repository dependency & build cleanup."""

from __future__ import annotations

import json

from verification.repository_dependency_build_cleanup.contract import (
    CLASSIFICATIONS,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.repository_dependency_build_cleanup.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.repository_dependency_build_cleanup.runner import build_report, run


def test_policy() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["schema"] == "repository-dependency-build-cleanup-policy:1.0"
    assert policy["no_forced_framework_modernization"] is True
    assert policy["no_storage_cleanup"] is True
    assert policy["start_slice_16_6"] is True
    assert policy.get("start_slice_16_7", False) is True
    assert policy.get("start_slice_16_8", False) is True
    assert policy.get("start_slice_16_9", False) is True
    assert policy.get("start_slice_16_10", False) is True
    assert policy.get("start_epic_17", False) is False
    assert set(policy["classifications"]) == set(CLASSIFICATIONS)


def test_vscode_local_vsce() -> None:
    root = monorepo_root_from_here()
    pkg = json.loads((root / "vscode-plugin/package.json").read_text(encoding="utf-8"))
    assert "@vscode/vsce" in pkg["devDependencies"]
    assert "ovsx" in pkg["devDependencies"]
    assert "npx --yes @vscode/vsce" not in pkg["scripts"]["package"]
    assert "npx --yes ovsx" not in pkg["scripts"]["publish:ovsx:dry"]


def test_insights_no_chart_aws() -> None:
    root = monorepo_root_from_here()
    pkg = json.loads((root / "insights/package.json").read_text(encoding="utf-8"))
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    assert "@types/node" in deps
    assert not any("chart" in k.lower() or "recharts" in k.lower() for k in deps)
    assert not any("aws-sdk" in k.lower() for k in deps)
    assert "typecheck" in pkg["scripts"]


def test_build_report() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.release_posture.get("start_epic_17", False) is False
    assert report.release_posture["npm_audit_fix_force_used"] is False
    assert report.version_authority["engine"] == "0.2.0"
    assert report.version_authority["vscode"] == "0.2.0"


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
    out = root / "reports/verification/sv16-5/repository-dependency-build-cleanup-verification.json"
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["verdict"] == report.verdict
    assert payload["dependency_register_relative"]


def test_epic_17_absent() -> None:
    root = monorepo_root_from_here()
    assert not (root / "reports/verification/sv17-1").exists()
