"""Tests for Slice 17.24 Community Insights Production Auth."""

from __future__ import annotations

import json

from verification.community_insights_production_auth.contract import (
    CONTRACT_RELATIVE,
    EXPECTED_17_24_PACKAGE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SLICE_17_25_PACKAGE_CANDIDATES,
    SUITE_ID,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_insights_production_auth.determinism import reports_byte_identical
from verification.community_insights_production_auth.helpers import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_insights_production_auth.runner import build_report, write_report


def test_contract_boundary() -> None:
    c = default_contract()
    assert c.start_slice_17_24 is True
    assert c.start_slice_17_25 is False
    assert SCHEMA_NAME == "community-insights-production-auth-verification"
    assert SCHEMA_VERSION == "1.0.0"
    assert SUITE_ID == "sv17-24"
    assert POLICY_REQUIRED_VALUES["start_slice_17_24"] is True
    assert POLICY_REQUIRED_VALUES["start_slice_17_25"] is False
    assert EXPECTED_17_24_PACKAGE == "verification/community_insights_production_auth"
    assert "verification/community_epic17_completion" in SLICE_17_25_PACKAGE_CANDIDATES
    assert "verification/community_docs_reconciliation" in SLICE_17_25_PACKAGE_CANDIDATES
    assert "verification/community_release_epic" in SLICE_17_25_PACKAGE_CANDIDATES


def test_policy_and_contract_files() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    for key, expected in POLICY_REQUIRED_VALUES.items():
        assert policy.get(key) == expected, key
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("$id", "").startswith(SCHEMA_NAME) or contract.get("title")
    assert (root / EXPECTED_17_24_PACKAGE).is_dir()
    for cand in SLICE_17_25_PACKAGE_CANDIDATES:
        assert not (root / cand).exists()


def test_build_report() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.slice == "17.24"
    assert report.suite_id == SUITE_ID
    assert report.epic17_boundary["start_slice_17_24"] is True
    assert report.epic17_boundary["start_slice_17_25"] is False
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}
    text = dict_to_canonical_json(report.to_dict())
    assert "/Users/" not in text
    assert "timestamp" not in text
    assert report_text_is_safe(text)


def test_scenarios_a_to_z() -> None:
    report = build_report(monorepo_root_from_here())
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert letter in report.scenario_results
    assert report.scenario_results.get("Y") is True


def test_determinism_and_write() -> None:
    root = monorepo_root_from_here()
    r1 = build_report(root)
    r2 = build_report(root)
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())
    path = write_report(root, r2)
    assert path.name == "community-insights-production-auth-verification.json"
    assert "sv17-24" in path.as_posix()
    text = path.read_text(encoding="utf-8")
    assert "timestamp" not in text
    assert "/Users/" not in text
    assert report_text_is_safe(text)


def test_report_text_is_safe() -> None:
    report = build_report(monorepo_root_from_here())
    text = dict_to_canonical_json(report.to_dict())
    assert report_text_is_safe(text)
