"""Tests for Slice 14.8 visualization system."""

from __future__ import annotations

import json

from verification.visualization_system.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV148_OUTPUT_RELATIVE,
    monorepo_root_from_here,
)
from verification.visualization_system.runner import build_report, write_report


def test_policy_and_contract_present() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["policy_id"] == POLICY_ID
    assert policy["policy_version"] == "1.0"
    assert policy["start_slice_15_7"] is False
    assert policy["scoring_change_allowed"] is False
    assert policy["zero_findings_implies_health"] is False
    viz = json.loads(
        (root / "design-system/contracts/visualization.json").read_text(encoding="utf-8")
    )
    assert viz["schema"] == "codestrata-visualization-contract"
    assert "universal_codestrata_score" in viz["forbidden_scores"]


def test_status_badge_not_assessed_guard() -> None:
    root = monorepo_root_from_here()
    renderer = (
        root / "engine/src/codestrata/reporting/html_v2/renderer.py"
    ).read_text(encoding="utf-8")
    assert "status-badge-not-assessed" in renderer
    # Import and exercise mapping without changing domain enums.
    import sys

    sys.path.insert(0, str(root / "engine/src"))
    from codestrata.reporting.html_v2.renderer import _status_badge_class

    assert "not-assessed" in _status_badge_class("Not assessed")
    assert "succeeded" in _status_badge_class("Assessed")
    assert "partial" in _status_badge_class("Partially assessed")
    assert "failed" in _status_badge_class("Failed")


def test_build_and_write_report_twice_byte_identical() -> None:
    root = monorepo_root_from_here()
    report_a = build_report(root)
    path_a = write_report(root, report_a)
    text_a = path_a.read_bytes()
    report_b = build_report(root)
    path_b = write_report(root, report_b)
    text_b = path_b.read_bytes()
    assert path_a == root / SV148_OUTPUT_RELATIVE / REPORT_JSON
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
    from verification.visualization_system.contract import FORBIDDEN_15_7_PATHS

    for relative in FORBIDDEN_15_7_PATHS:
        assert not (root / relative).exists(), relative
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["start_slice_15_7"] is False
    assert policy["navigation_ia_change_allowed"] is False
