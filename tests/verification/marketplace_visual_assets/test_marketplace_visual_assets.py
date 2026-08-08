"""Tests for Slice 14.6 Marketplace visual assets verification."""

from __future__ import annotations

import json

from verification.marketplace_visual_assets.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV146_OUTPUT_RELATIVE,
    monorepo_root_from_here,
)
from verification.marketplace_visual_assets.runner import build_report, write_report


def test_policy_file_present() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["policy_id"] == POLICY_ID
    assert policy["policy_version"] == "1.0"
    assert policy["start_slice_14_7"] is False
    assert policy["extension_version"] == "0.2.0"
    assert policy["legacy_amber_allowed"] is False
    assert policy["universal_logo_authority_change_allowed"] is False


def test_gallery_assets_present_and_sized() -> None:
    root = monorepo_root_from_here()
    media = root / "vscode-plugin" / "media"
    assert (media / "codestrata-icon.png").is_file()
    assert (media / "screenshot-assessment.png").is_file()
    assert not (media / "screenshot-findings.png").exists()
    pkg = json.loads((root / "vscode-plugin" / "package.json").read_text(encoding="utf-8"))
    assert pkg["galleryBanner"]["color"] == "#f4f6f3"
    assert pkg["galleryBanner"]["theme"] == "light"
    assert pkg["version"] == "0.2.0"


def test_build_and_write_report_twice_byte_identical() -> None:
    root = monorepo_root_from_here()
    report_a = build_report(root)
    path_a = write_report(root, report_a)
    text_a = path_a.read_bytes()
    report_b = build_report(root)
    path_b = write_report(root, report_b)
    text_b = path_b.read_bytes()
    assert path_a == root / SV146_OUTPUT_RELATIVE / REPORT_JSON
    assert text_a == text_b
    payload = json.loads(text_a.decode("utf-8"))
    assert payload["schema_name"] == SCHEMA_NAME
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["verdict"] in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert payload["failed_checks"] == 0
    assert b"/Users/" not in text_a
    assert b"timestamp" not in text_a
    assert report_a.icon_status == "pass"
    assert report_a.commercial_boundary_status == "pass"


def test_slice_14_7_not_started() -> None:
    root = monorepo_root_from_here()
    assert not (root / "verification" / "marketplace_publish").exists()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["start_slice_14_7"] is False
