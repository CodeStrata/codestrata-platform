"""Tests for Slice 14.4 EIR redesign verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.engineering_intelligence_report_redesign.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV144_OUTPUT_RELATIVE,
    monorepo_root_from_here,
)
from verification.engineering_intelligence_report_redesign.runner import (
    build_report,
    write_report,
)


def test_policy_file_present() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["policy_id"] == POLICY_ID
    assert policy["policy_version"] == "1.0"
    assert policy["start_slice_14_5"] is False
    assert policy["html_template_presentation_version"] == "eir-static-html-v2"


def test_build_and_write_report_twice_byte_identical() -> None:
    root = monorepo_root_from_here()
    report_a = build_report(root)
    path_a = write_report(root, report_a)
    text_a = path_a.read_bytes()

    report_b = build_report(root)
    path_b = write_report(root, report_b)
    text_b = path_b.read_bytes()

    assert path_a == root / SV144_OUTPUT_RELATIVE / REPORT_JSON
    assert text_a == text_b
    payload = json.loads(text_a.decode("utf-8"))
    assert payload["schema_name"] == SCHEMA_NAME
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["verdict"] in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert payload["failed_checks"] == 0
    assert b"/Users/" not in text_a
    assert "timestamp" not in text_a.decode("utf-8")
    assert report_a.assessment_report_boundary_status == "pass"
    assert report_a.domain_boundary_status == "pass"


def test_eir_html_uses_design_system_and_shell() -> None:
    from codestrata_platform.intelligence_reporting.presentation.static_html.styles import (
        REPORT_CSS,
    )

    assert "DESIGN_TOKENS_CSS" in Path(
        "platform/src/codestrata_platform/intelligence_reporting/"
        "presentation/static_html/styles.py"
    ).read_text(encoding="utf-8") or "--cs-teal" in REPORT_CSS
    assert "--cs-teal: #16756a" in REPORT_CSS
    assert "#0f4c5c" not in REPORT_CSS
    assert "Georgia" not in REPORT_CSS
