"""Tests for Slice 14.7 cross-surface presentation."""

from __future__ import annotations

import json

from verification.cross_surface_presentation.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV147_OUTPUT_RELATIVE,
    monorepo_root_from_here,
)
from verification.cross_surface_presentation.runner import build_report, write_report


def test_policy_and_contracts_present() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["policy_id"] == POLICY_ID
    assert policy["policy_version"] == "1.0"
    assert policy["start_slice_14_13"] is True
    assert policy["start_epic_15"] is False
    assert policy["design_system_bump_required"] is False
    assert (root / "design-system/contracts/presentation.json").is_file()
    assert (root / "design-system/contracts/components.json").is_file()
    assert (root / "design-system/contracts/consumer-mappings.json").is_file()
    assert (root / "design-system/contracts/report-information-architecture.json").is_file()


def test_design_system_version_unchanged() -> None:
    root = monorepo_root_from_here()
    catalog = json.loads(
        (root / "design-system/tokens/catalog.json").read_text(encoding="utf-8")
    )
    assert catalog["schema_version"] == "1.0.0"


def test_build_and_write_report_twice_byte_identical() -> None:
    root = monorepo_root_from_here()
    report_a = build_report(root)
    path_a = write_report(root, report_a)
    text_a = path_a.read_bytes()
    report_b = build_report(root)
    path_b = write_report(root, report_b)
    text_b = path_b.read_bytes()
    assert path_a == root / SV147_OUTPUT_RELATIVE / REPORT_JSON
    assert text_a == text_b
    payload = json.loads(text_a.decode("utf-8"))
    assert payload["schema_name"] == SCHEMA_NAME
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["verdict"] in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert payload["failed_checks"] == 0
    assert b"/Users/" not in text_a
    assert b"timestamp" not in text_a


def test_slice_14_14_not_started() -> None:
    root = monorepo_root_from_here()
    from verification.cross_surface_presentation.contract import FORBIDDEN_EPIC_15_PATHS

    for relative in FORBIDDEN_EPIC_15_PATHS:
        assert not (root / relative).exists(), relative
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["navigation_standardization_complete"] is True
    assert policy["chart_standardization_complete"] is True
    assert policy["asset_standardization_complete"] is True
    assert policy["accessibility_final_validation_complete"] is True
    assert policy["start_slice_14_13"] is True
    assert policy["start_epic_15"] is False
