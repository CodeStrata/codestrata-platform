"""Tests for Slice 14.13 cross-surface visual consistency."""

from __future__ import annotations

import json

from verification.cross_surface_visual_consistency.contract import (
    FORBIDDEN_15_7_PATHS,
    LEGACY_AMBER_HEX,
    POLICY_ID,
    POLICY_RELATIVE,
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1413_OUTPUT_RELATIVE,
    monorepo_root_from_here,
)
from verification.cross_surface_visual_consistency.runner import build_report, write_report


def test_policy_and_contract_present() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["policy_id"] == POLICY_ID
    assert policy["policy_version"] == "1.0"
    assert policy["prohibited"]["start_slice_15_7"] is True
    assert (root / "design-system/contracts/cross-surface-consistency.json").is_file()


def test_matrix_no_violations() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    violations = [c for c in report.consistency_matrix if c.value == "violation"]
    assert not violations, violations


def test_amber_absent_from_public_and_swagger_tokens() -> None:
    root = monorepo_root_from_here()
    public = (root / "docs/public/design-tokens/tokens.css").read_text(encoding="utf-8")
    swagger = (
        root / "platform/api/openapi/swagger/design-tokens/tokens.css"
    ).read_text(encoding="utf-8")
    assert LEGACY_AMBER_HEX.lower() not in public.lower()
    assert LEGACY_AMBER_HEX.lower() not in swagger.lower()


def test_assessment_product_bar_mark() -> None:
    root = monorepo_root_from_here()
    renderer = (
        root / "engine/src/codestrata/reporting/html_v2/renderer.py"
    ).read_text(encoding="utf-8")
    styles = (
        root / "engine/src/codestrata/reporting/html_v2/styles.py"
    ).read_text(encoding="utf-8")
    assert "report-product-mark" in renderer
    assert "report-product-mark" in styles


def test_slice_14_14_not_started() -> None:
    root = monorepo_root_from_here()
    for relative in FORBIDDEN_15_7_PATHS:
        assert not (root / relative).exists(), relative


def test_build_and_write_report_twice_byte_identical() -> None:
    root = monorepo_root_from_here()
    report_a = build_report(root)
    path_a = write_report(root, report_a)
    text_a = path_a.read_bytes()
    report_b = build_report(root)
    path_b = write_report(root, report_b)
    text_b = path_b.read_bytes()
    assert path_a == root / SV1413_OUTPUT_RELATIVE / REPORT_JSON
    assert text_a == text_b
    payload = json.loads(text_a.decode("utf-8"))
    assert payload["schema_name"] == SCHEMA_NAME
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["verdict"] in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert payload["failed_checks"] == 0
    assert b"/Users/" not in text_a
    assert b"timestamp" not in text_a.lower()
