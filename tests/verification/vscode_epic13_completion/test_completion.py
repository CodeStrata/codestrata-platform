"""Unit tests for Slice 13.15 Epic 13 completion verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_epic13_completion.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    TOTAL_SLICES,
    monorepo_root_from_here,
)
from verification.vscode_epic13_completion.determinism import reports_byte_identical
from verification.vscode_epic13_completion.policy_registry import build_policy_registry
from verification.vscode_epic13_completion.runner import build_report, write_report
from verification.vscode_epic13_completion.schema_registry import build_schema_registry
from verification.vscode_epic13_completion.slice_matrix import SLICE_TITLES
from verification.vscode_epic13_completion.scenarios import (
    COMPLETION_SCENARIOS,
    NEGATIVE_COMPLETION_CHECKS,
)


def test_slice_matrix_titles() -> None:
    assert len(SLICE_TITLES) == TOTAL_SLICES
    assert SLICE_TITLES["13.15"] == "Epic Completion Verification"


def test_policy_registry_shape() -> None:
    monorepo = monorepo_root_from_here()
    rows = build_policy_registry(monorepo)
    epic13 = [r for r in rows if r["family"] == "epic13_slice"]
    assert len(epic13) == 14
    assert all(r["policy_version"] == "1.0" for r in epic13)


def test_schema_registry_includes_completion() -> None:
    rows = build_schema_registry()
    names = {r["schema_name"] for r in rows}
    assert SCHEMA_NAME in names
    assert "assessment" in names


def test_scenarios_a_to_z() -> None:
    assert len(COMPLETION_SCENARIOS) == 26
    assert COMPLETION_SCENARIOS[0][0] == "A"
    assert COMPLETION_SCENARIOS[-1][0] == "Z"
    assert len(NEGATIVE_COMPLETION_CHECKS) == 26


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.completed_slices == TOTAL_SLICES
    assert report.total_slices == TOTAL_SLICES
    assert report.extension_version == "0.2.0"
    assert report.release_posture.get("start_epic_14") is False
    assert report.release_posture.get("marketplace_published") is False
    assert report.release_posture.get("commit_created") is False
    assert report.release_posture.get("epic_13_complete") is True
    assert report.active_editor_inventory == ["vscode"]
    path = write_report(monorepo, report)
    text = Path(path).read_text(encoding="utf-8")
    assert "timestamp" not in text
    assert "/Users/" not in text
    assert "file://" not in text


def test_runner_deterministic() -> None:
    monorepo = monorepo_root_from_here()
    a = build_report(monorepo).to_dict()
    b = build_report(monorepo).to_dict()
    assert reports_byte_identical(a, b)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
