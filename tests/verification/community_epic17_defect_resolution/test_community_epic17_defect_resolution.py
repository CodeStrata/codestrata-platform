"""Tests for Slice 17.22 verification package."""

from __future__ import annotations

from verification.community_epic17_defect_resolution.contract import (
    EXPECTED_17_23_PACKAGE,
    POLICY_REQUIRED_VALUES,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SLICE_17_24_PACKAGE_CANDIDATES,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_epic17_defect_resolution.runner import build_report


def test_contract_boundary() -> None:
    c = default_contract()
    assert c.start_slice_17_22 is True
    assert c.start_slice_17_23 is True
    assert c.start_slice_17_24 is False
    assert SCHEMA_NAME == "community-epic17-defect-resolution-verification"
    assert SCHEMA_VERSION == "1.0.0"
    assert POLICY_REQUIRED_VALUES["feature_freeze"] is True
    assert POLICY_REQUIRED_VALUES["start_slice_17_23"] is True
    assert POLICY_REQUIRED_VALUES["start_slice_17_24"] is False
    assert EXPECTED_17_23_PACKAGE == "verification/community_status_report_registry"
    assert "verification/community_production_slice_17_24" in SLICE_17_24_PACKAGE_CANDIDATES


def test_build_report() -> None:
    report = build_report(monorepo_root_from_here())
    assert report.slice == "17.22"
    assert report.epic17_boundary["start_slice_17_23"] is True
    assert report.epic17_boundary["start_slice_17_24"] is False
    assert report.scenario_results.get("Y") is True
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}
    text = str(report.to_dict())
    assert "/Users/" not in text
    assert "OPENAI_API_KEY=" not in text
