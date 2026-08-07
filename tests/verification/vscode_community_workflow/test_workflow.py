"""Focused tests for Slice 13.1 VS Code Community workflow verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_community_workflow.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    WORKFLOW_COMMANDS,
    WORKFLOW_POLICY_ID,
)
from verification.vscode_community_workflow.runner import build_report, run

ROOT = Path(__file__).resolve().parents[3]


def test_workflow_package_present() -> None:
    root = ROOT / "vscode-plugin/src/communityWorkflow"
    assert (root / "policy.ts").is_file()
    assert (root / "orchestration.ts").is_file()
    text = (root / "policy.ts").read_text(encoding="utf-8")
    assert WORKFLOW_POLICY_ID in text


def test_commands_in_package_json() -> None:
    data = json.loads((ROOT / "vscode-plugin/package.json").read_text(encoding="utf-8"))
    assert data["version"] == "0.2.0"
    cmds = {c["command"] for c in data["contributes"]["commands"]}
    assert set(WORKFLOW_COMMANDS).issubset(cmds)


def test_extension_wires_session() -> None:
    text = (ROOT / "vscode-plugin/src/extension.ts").read_text(encoding="utf-8")
    assert "CommunityWorkflowSession" in text
    assert "recordCliInvocation" in text
    assert "markProgressClosed" in text


def test_no_cursor_plugin() -> None:
    assert not (ROOT / "cursor-plugin").exists()


def test_slice_13_2_absent() -> None:
    assert not (ROOT / "verification/vscode_cli_detection").exists()


def test_runner_passes() -> None:
    report = build_report(ROOT)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0, [c.name for c in report.checks if not c.ok]
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}


def test_dual_run_deterministic() -> None:
    r1 = run(ROOT)
    r2 = run(ROOT)
    assert r1.to_dict() == r2.to_dict()
    path = ROOT / "reports/verification/sv13-1/vscode-community-workflow-verification.json"
    assert path.is_file()
    blob = path.read_text(encoding="utf-8")
    assert "/Users/" not in blob
    assert "AKIA" not in blob
