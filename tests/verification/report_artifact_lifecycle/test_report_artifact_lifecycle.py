"""Tests for Slice 17.15 report artifact lifecycle verification."""

from __future__ import annotations

import json

from verification.report_artifact_lifecycle.contract import (
    CONTRACT_RELATIVE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    POLICY_SCHEMA,
    REGISTER_RELATIVE,
    REGISTER_SCHEMA,
    SCHEMA_NAME,
    default_contract,
    monorepo_root_from_here,
)
from verification.report_artifact_lifecycle.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
    reports_byte_identical,
)
from verification.report_artifact_lifecycle.runner import build_report


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_15 is True
    assert c.start_slice_17_16 is True


def test_policy_and_register_schema() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == POLICY_SCHEMA
    for key, expected in POLICY_REQUIRED_VALUES.items():
        assert policy.get(key) == expected, f"policy.{key}"

    register = json.loads((root / REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert register.get("schema") == REGISTER_SCHEMA
    assert len(register.get("entries") or []) >= 1

    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == SCHEMA_NAME
    assert contract.get("start_slice_17_15") is True
    assert contract.get("start_slice_17_16") is True
    assert (root / "verification/report_artifact_lifecycle").is_dir()


def test_build_report_runs() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.slice == "17.15"
    assert report.suite_id == "sv17-15"
    assert report.policy.get("start_slice_17_15") is True
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


def test_scenarios_present() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert letter in report.scenario_results


def test_hard_fail_gates() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("start_slice_17_16") is True
    assert policy.get("telemetry_data_lake_uses_report_retention") is False
    assert policy.get("assessment_versions_per_repository") <= 2
    assert policy.get("run_ids_are_metadata") is True
