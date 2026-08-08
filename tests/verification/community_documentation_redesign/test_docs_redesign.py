"""Tests for Slice 14.2 community documentation redesign verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_documentation_redesign.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.community_documentation_redesign.runner import build_report, write_report


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.design_system_consumed is True
    assert report.community_only_scope is True
    assert report.release_posture.get("slice_14_3_started") is False
    path = write_report(monorepo, report)
    text = Path(path).read_text(encoding="utf-8")
    assert "timestamp" not in text
    assert "/Users/" not in text


def test_runner_deterministic() -> None:
    monorepo = monorepo_root_from_here()
    a = build_report(monorepo).to_dict()
    b = build_report(monorepo).to_dict()
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
