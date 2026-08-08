"""Tests for Slice 14.1 visual design system verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.visual_design_system.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.visual_design_system.runner import build_report, write_report


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.release_posture.get("slice_14_2_started") is False
    assert report.release_posture.get("product_redesign_performed") is False
    assert report.slice_14_2_absence_status == "pass"
    assert report.no_redesign_status == "pass"
    path = write_report(monorepo, report)
    text = Path(path).read_text(encoding="utf-8")
    assert "timestamp" not in text
    assert "/Users/" not in text


def test_runner_deterministic() -> None:
    monorepo = monorepo_root_from_here()
    a = build_report(monorepo).to_dict()
    b = build_report(monorepo).to_dict()
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_token_catalog_matches_live_website() -> None:
    monorepo = monorepo_root_from_here()
    catalog = json.loads(
        (monorepo / "design-system/tokens/catalog.json").read_text(encoding="utf-8")
    )
    assert catalog["colors"]["canvas"] == "#f4f6f3"
    assert catalog["colors"]["teal_dark"] == "#0f5d54"
    assert catalog["colors"]["rust"] == "#a04b17"
    assert "Space Grotesk" in catalog["typography"]["font_display"]
