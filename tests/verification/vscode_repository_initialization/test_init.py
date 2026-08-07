"""Unit tests for Slice 13.4 repository initialization verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_repository_initialization.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.vscode_repository_initialization.runner import build_report, write_report
from verification.vscode_repository_initialization.scenarios import NEGATIVE_SCENARIOS


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    path = write_report(monorepo, report)
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    text = json.dumps(payload)
    assert "timestamp" not in text
    assert "/Users/" not in text
    assert "stdout" not in text
    assert "stderr" not in text
    assert len(NEGATIVE_SCENARIOS) == 26


def test_runner_deterministic() -> None:
    monorepo = monorepo_root_from_here()
    a = build_report(monorepo).to_dict()
    b = build_report(monorepo).to_dict()
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
