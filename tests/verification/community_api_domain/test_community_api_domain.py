"""Tests for Slice 17.14 Community API domain verification."""

from __future__ import annotations

import json

from verification.community_api_domain.contract import (
    CONTRACT_RELATIVE,
    DOMAIN_REGISTER_RELATIVE,
    DOMAIN_REGISTER_SCHEMA,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    ROUTE_CLASSIFICATIONS,
    ROUTE_REGISTER_RELATIVE,
    ROUTE_REGISTER_SCHEMA,
    SCHEMA_NAME,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_api_domain.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
    reports_byte_identical,
)
from verification.community_api_domain.runner import build_report


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_14 is True
    assert c.start_slice_17_15 is False
    assert c.public_api_base == "https://api.codestrata.ai"


def test_policy_and_register_schema() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == POLICY_SCHEMA
    assert policy.get("start_slice_17_14") is True
    assert policy.get("start_slice_17_15") is False

    domain_register = json.loads((root / DOMAIN_REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert domain_register.get("schema") == DOMAIN_REGISTER_SCHEMA
    assert len(domain_register.get("entries") or []) >= 1

    route_register = json.loads((root / ROUTE_REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert route_register.get("schema") == ROUTE_REGISTER_SCHEMA
    routes = route_register.get("routes") or []
    assert routes
    for route in routes:
        assert route.get("classification") in ROUTE_CLASSIFICATIONS

    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == SCHEMA_NAME
    assert contract.get("start_slice_17_14") is True
    assert contract.get("start_slice_17_15") is False
    assert (root / "verification/community_api_domain").is_dir()


def test_build_report_runs() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.slice == "17.14"
    assert report.suite_id == "sv17-14"
    assert report.epic17_boundary.get("start_slice_17_14") is True
    assert report.epic17_boundary.get("start_slice_17_15") is False
    assert report.policy.get("start_slice_17_14") is True
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}


def test_determinism_dual_run() -> None:
    root = monorepo_root_from_here()
    r1 = build_report(root)
    r2 = build_report(root)
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())


def test_no_path_or_token_leaks_in_canonical_json() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    text = dict_to_canonical_json(report.to_dict())
    safe, _reason = report_text_is_safe(text)
    assert safe
    assert "/Users/" not in text
    assert "/home/" not in text
    assert "arn:aws:" not in text
    assert "execute-api." not in text


def test_scenarios_present() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert letter in report.scenario_results


def test_slice_17_15_not_started() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.epic17_boundary.get("start_slice_17_15") is False
    assert report.scenario_results.get("Q") is True
