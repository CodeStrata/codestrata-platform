"""Tests for Slice 14.3 assessment HTML report redesign verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.assessment_report_redesign.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV143_OUTPUT_RELATIVE,
    monorepo_root_from_here,
)
from verification.assessment_report_redesign.runner import build_report, write_report


def test_policy_file_present() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["policy_id"] == POLICY_ID
    assert policy["policy_version"] == "1.0"
    assert policy["start_slice_14_4"] is False
    assert policy["assessment_schema_version"] == "1.2"


def test_build_and_write_report_twice_byte_identical(tmp_path: Path) -> None:
    root = monorepo_root_from_here()
    report_a = build_report(root, tmp_path / "a")
    path_a = write_report(root, report_a)
    text_a = path_a.read_bytes()

    report_b = build_report(root, tmp_path / "b")
    path_b = write_report(root, report_b)
    text_b = path_b.read_bytes()

    assert path_a == root / SV143_OUTPUT_RELATIVE / REPORT_JSON
    assert text_a == text_b
    payload = json.loads(text_a.decode("utf-8"))
    assert payload["schema_name"] == SCHEMA_NAME
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["verdict"] in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert payload["failed_checks"] == 0
    assert "timestamp" not in text_a.decode("utf-8")
    assert b"/Users/" not in text_a
    assert report_a.design_policy_status == "pass"
    assert report_a.schema_boundary_status == "pass"
    assert report_a.eir_boundary_status == "pass"


def test_design_system_alignment_still_holds(tmp_path: Path) -> None:
    from codestrata.reporting.html_v2 import HtmlReportRenderer, build_html_report_view_model
    from codestrata.reporting.html_v2.styles import REPORT_CSS
    from verification.assessment_report_redesign.fixtures import synthetic_report_input

    assert "--cs-teal: #16756a" in REPORT_CSS
    assert "#b06a24" not in REPORT_CSS
    html = HtmlReportRenderer().render(
        build_html_report_view_model(synthetic_report_input(tmp_path))
    )
    assert "report-shell" in html
    assert "report-product-bar" in html
    assert 'id="cover"' in html
    assert "fonts.googleapis" not in html.lower()
