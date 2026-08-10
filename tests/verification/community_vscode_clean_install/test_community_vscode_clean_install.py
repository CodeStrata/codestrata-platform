"""Tests for Slice 17.21 verification package."""

from __future__ import annotations

from verification.community_vscode_clean_install.contract import (
    POLICY_REQUIRED_VALUES,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_vscode_clean_install.runner import build_report


def test_contract_boundary() -> None:
    c = default_contract()
    assert c.start_slice_17_21 is True
    assert c.start_slice_17_22 is True
    assert c.start_slice_17_23 is False
    assert SCHEMA_NAME == "community-vscode-clean-install-verification"
    assert SCHEMA_VERSION == "1.0.0"
    assert POLICY_REQUIRED_VALUES["marketplace_publish"] is False
    assert POLICY_REQUIRED_VALUES["api_authority"] == "https://api.codestrata.ai"
    assert POLICY_REQUIRED_VALUES["start_slice_17_22"] is True


def test_build_report_runs() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema == SCHEMA_NAME
    assert report.epic17_boundary["start_slice_17_22"] is True
    assert report.epic17_boundary["start_slice_17_23"] is False
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}
    assert report.failed_checks == 0 or report.verdict == "FAIL"
    text = str(report.to_dict())
    assert "/Users/" not in text
