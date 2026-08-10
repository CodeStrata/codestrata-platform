"""Tests for Slice 17.16 Community report publishing verification."""

from __future__ import annotations

import json

from verification.community_report_publishing.contract import (
    CONTRACT_RELATIVE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    POLICY_SCHEMA,
    PUBLISHING_REGISTER_RELATIVE,
    PUBLISHING_REGISTER_SCHEMA,
    SCHEMA_NAME,
    STORAGE_REGISTER_RELATIVE,
    STORAGE_REGISTER_SCHEMA,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_report_publishing.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
    reports_byte_identical,
)
from verification.community_report_publishing.runner import build_report


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_16 is True
    assert c.start_slice_17_17 is True
    assert c.public_report_domain == "https://reports.codestrata.ai"


def test_policy_and_register_schema() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == POLICY_SCHEMA
    for key, expected in POLICY_REQUIRED_VALUES.items():
        assert policy.get(key) == expected

    publishing_register = json.loads((root / PUBLISHING_REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert publishing_register.get("schema") == PUBLISHING_REGISTER_SCHEMA
    assert len(publishing_register.get("entries") or []) >= 2

    storage_register = json.loads((root / STORAGE_REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert storage_register.get("schema") == STORAGE_REGISTER_SCHEMA
    assert len(storage_register.get("entries") or []) >= 3

    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == SCHEMA_NAME
    assert contract.get("start_slice_17_16") is True
    assert contract.get("start_slice_17_17") is True
    assert (root / "verification/community_report_publishing").is_dir()


def test_build_report_runs() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.slice == "17.16"
    assert report.suite_id == "sv17-16"
    assert report.epic17_boundary.get("start_slice_17_16") is True
    assert report.epic17_boundary.get("start_slice_17_17") is True
    assert report.policy.get("start_slice_17_16") is True
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
    assert "s3://" not in text


def test_scenarios_present() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert letter in report.scenario_results


def test_slice_17_17_started_and_17_18_not() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.epic17_boundary.get("start_slice_17_17") is True
    assert report.scenario_results.get("A") is True
    assert report.scenario_results.get("W") is True
    assert (root / "verification/community_telemetry_consent").is_dir()
    assert not (root / "verification/community_production_slice_17_18").exists()
