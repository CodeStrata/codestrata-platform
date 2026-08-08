"""Tests for Slice 14.5 VS Code visual experience verification."""

from __future__ import annotations

import json

from verification.vscode_visual_experience.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV145_OUTPUT_RELATIVE,
    monorepo_root_from_here,
)
from verification.vscode_visual_experience.runner import build_report, write_report


def test_policy_file_present() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["policy_id"] == POLICY_ID
    assert policy["policy_version"] == "1.0"
    assert policy["start_slice_14_6"] is False
    assert policy["extension_version"] == "0.2.0"
    assert policy["website_css_injection_allowed"] is False


def test_build_and_write_report_twice_byte_identical() -> None:
    root = monorepo_root_from_here()
    report_a = build_report(root)
    path_a = write_report(root, report_a)
    text_a = path_a.read_bytes()
    report_b = build_report(root)
    path_b = write_report(root, report_b)
    text_b = path_b.read_bytes()
    assert path_a == root / SV145_OUTPUT_RELATIVE / REPORT_JSON
    assert text_a == text_b
    payload = json.loads(text_a.decode("utf-8"))
    assert payload["schema_name"] == SCHEMA_NAME
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["verdict"] in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert payload["failed_checks"] == 0
    assert b"/Users/" not in text_a
    assert report_a.native_host_boundary_status == "pass"
    assert report_a.marketplace_boundary_status == "pass"


def test_activity_svg_uses_current_color() -> None:
    root = monorepo_root_from_here()
    svg = (root / "vscode-plugin/media/codestrata-activity.svg").read_text(encoding="utf-8")
    assert "currentColor" in svg
    assert "#D97706" not in svg
    assert "#d98a3d" not in svg.lower()
