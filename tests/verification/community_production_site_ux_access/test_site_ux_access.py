"""Tests for Slice 17.11 production site UX and access verification."""

from __future__ import annotations

import json

from verification.community_production_site_ux_access.contract import (
    CONTRACT_RELATIVE,
    EXPECTED_AUTH_ROOT_CAUSE,
    POLICY_RELATIVE,
    REGISTER_RELATIVE,
    SCHEMA_NAME,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_production_site_ux_access.determinism import (
    FORBIDDEN_REPORT_SUBSTRINGS,
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.community_production_site_ux_access.runner import build_report


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_11 is True
    assert c.start_slice_17_12 is True
    assert getattr(c, "start_slice_17_13", False) is False
    assert c.package_id == "community-production-site-ux-access"
    assert c.package_version == "1.0.0"
    assert c.insights_auth_root_cause == EXPECTED_AUTH_ROOT_CAUSE
    assert c.insights_password_rotation_performed is False


def test_policy_and_register_schema() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == "community-production-site-ux-access-policy:1.0"
    assert policy.get("start_slice_17_11") is True
    assert policy.get("start_slice_17_12") is True
    assert policy.get("start_slice_17_13") is False
    assert policy.get("docs_repo_visibility") == "private"
    assert policy.get("docs_site_public") is True
    assert policy.get("insights_password_rotation_performed") is False
    register = json.loads((root / REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert register.get("schema") == "community-production-site-ux-access-register:1.0"
    assert register.get("start_slice_17_11") is True
    assert register.get("start_slice_17_12") is True
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == "community-production-site-ux-access-verification:1.0.0"
    assert contract.get("start_slice_17_11") is True
    assert contract.get("start_slice_17_12") is True
    assert (root / "verification/community_production_site_ux_access").is_dir()
    mirror = root / "insights/policies/community_production_site_ux_access_policy.json"
    assert mirror.is_file()
    assert mirror.read_bytes() == (root / POLICY_RELATIVE).read_bytes()


def test_build_report_runs() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.slice == "17.11"
    assert report.policy.get("start_slice_17_11") is True
    assert report.policy.get("start_slice_17_12") is True
    assert report.policy.get("start_slice_17_13", False) is False
    assert report.epic17_boundary.get("start_slice_17_12") is True
    assert report.epic17_boundary.get("start_slice_17_13", False) is False
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}


def test_determinism_dual_run() -> None:
    root = monorepo_root_from_here()
    r1 = build_report(root)
    r2 = build_report(root)
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())


def test_no_forbidden_secret_substrings_in_report() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    text = dict_to_canonical_json(report.to_dict())
    for needle in FORBIDDEN_REPORT_SUBSTRINGS:
        assert needle.lower() not in text.lower()
    assert "/Users/" not in text
    assert "/home/" not in text
    assert "arn:aws:" not in text


def test_scenarios_present() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    for letter in "ABCDEFGHIJKLMN":
        assert letter in report.scenario_results
