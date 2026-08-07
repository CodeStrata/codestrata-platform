"""Unit tests for Slice 13.3 installation verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_cli_installation.contract import (
    APPROACH_DECISION,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.vscode_cli_installation.runner import build_report, write_report


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.approach_decision == APPROACH_DECISION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    path = write_report(monorepo, report)
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "timestamp" not in json.dumps(payload)
    assert "/Users/" not in json.dumps(payload)
    assert "pip install" not in json.dumps(payload)
