"""Unit tests for Slice 13.2 CLI discovery verification package."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_cli_discovery.contract import (
    DISCOVERY_POLICY_ID,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.vscode_cli_discovery.runner import build_report, write_report


def test_build_report_pass_with_limitations() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert "explicit_configuration" in report.candidate_source_inventory
    path = write_report(monorepo, report)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_name"] == SCHEMA_NAME
    assert "timestamp" not in json.dumps(payload)
    assert "/Users/" not in json.dumps(payload)
    assert DISCOVERY_POLICY_ID  # policy id constant exists


def test_report_directory() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    assert path.parent.name == "sv13-2"
    assert Path(path).is_file()
