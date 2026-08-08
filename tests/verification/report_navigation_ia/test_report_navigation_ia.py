"""Tests for Slice 14.9 report navigation and information architecture."""

from __future__ import annotations

import json
import re
from collections import Counter

from verification.report_navigation_ia.checks import (
    render_assessment_html,
    render_eir_html,
)
from verification.report_navigation_ia.contract import (
    ASSESSMENT_LEGACY_ALIASES,
    ASSESSMENT_SECTION_ORDER,
    EIR_SECTION_ORDER,
    IA_CONTRACT,
    POLICY_ID,
    POLICY_RELATIVE,
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV149_OUTPUT_RELATIVE,
    monorepo_root_from_here,
)
from verification.report_navigation_ia.runner import build_report, write_report

_ID_RE = re.compile(r'(?<![\w-])id="([^"]+)"')
_HREF_RE = re.compile(r'href="#([^"]+)"')
_HEADING_RE = re.compile(r"<h([1-6])\b")


def _levels(html: str) -> list[int]:
    return [int(value) for value in _HEADING_RE.findall(html)]


def test_policy_and_contract_present() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["policy_id"] == POLICY_ID
    assert policy["policy_version"] == "1.0"
    assert policy["schema_change_allowed"] is False
    assert policy["section_reorder_allowed"] is False
    assert policy["navigation_javascript_allowed"] is False
    assert policy["global_breadcrumbs_allowed"] is False
    assert policy["start_slice_15_7"] is False

    ia = json.loads((root / IA_CONTRACT).read_text(encoding="utf-8"))
    assert ia["schema"] == "codestrata-report-information-architecture-contract"
    assert sorted(ia["hierarchy_levels"], key=int) == [str(index) for index in range(7)]
    assert ia["products_remain_distinct"] is True


def test_assessment_hierarchy_and_navigation() -> None:
    html = render_assessment_html()
    ids = Counter(_ID_RE.findall(html))
    assert not [key for key, count in ids.items() if count > 1]
    assert not [href for href in _HREF_RE.findall(html) if href not in ids]
    levels = _levels(html)
    assert levels.count(1) == 1
    assert not [
        (levels[i - 1], levels[i]) for i in range(1, len(levels)) if levels[i] > levels[i - 1] + 1
    ]
    positions = [html.find(f'id="{anchor}"') for anchor in ASSESSMENT_SECTION_ORDER]
    present = [index for index in positions if index >= 0]
    assert present == sorted(present)
    assert 0 <= html.find('id="executive-summary"') < html.find('id="assessment-results"')


def test_eir_hierarchy_and_navigation() -> None:
    root = monorepo_root_from_here()
    html = render_eir_html(root)
    ids = Counter(_ID_RE.findall(html))
    assert not [key for key, count in ids.items() if count > 1]
    assert not [href for href in _HREF_RE.findall(html) if href not in ids]
    levels = _levels(html)
    assert levels.count(1) == 1
    positions = [html.find(f'id="section-{key}"') for key in EIR_SECTION_ORDER]
    assert all(index >= 0 for index in positions)
    assert positions == sorted(positions)
    assert "<script" not in html.lower()


def test_stable_anchors_and_legacy_aliases_preserved() -> None:
    root = monorepo_root_from_here()
    heads = (
        root / "engine/src/codestrata/reporting/html_v2/assessment_heads.py"
    ).read_text(encoding="utf-8")
    for alias in ASSESSMENT_LEGACY_ALIASES:
        assert alias in heads
    ia = json.loads((root / IA_CONTRACT).read_text(encoding="utf-8"))
    assert set(ia["assessment_report"]["legacy_anchor_aliases"]) == set(ASSESSMENT_LEGACY_ALIASES)


def test_products_remain_distinct() -> None:
    root = monorepo_root_from_here()
    assessment = render_assessment_html()
    eir = render_eir_html(root)
    assert 'id="section-capability"' not in assessment
    assert "Repository Drill-Downs" not in assessment
    assert 'id="assessment-results"' not in eir
    assert 'id="technical-appendix"' not in eir


def test_build_and_write_report_twice_byte_identical() -> None:
    root = monorepo_root_from_here()
    path_a = write_report(root, build_report(root))
    text_a = path_a.read_bytes()
    path_b = write_report(root, build_report(root))
    text_b = path_b.read_bytes()
    assert path_a == root / SV149_OUTPUT_RELATIVE / REPORT_JSON
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
    from verification.report_navigation_ia.contract import FORBIDDEN_15_7_PATHS

    for relative in FORBIDDEN_15_7_PATHS:
        assert not (root / relative).exists(), relative
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy["start_slice_15_7"] is False
    assert policy["universal_asset_change_allowed"] is False
