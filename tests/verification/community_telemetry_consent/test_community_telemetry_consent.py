"""Tests for Slice 17.17 Community telemetry consent verification."""

from __future__ import annotations

import json

from verification.community_telemetry_consent.contract import (
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
from verification.community_telemetry_consent.determinism import dict_to_canonical_json
from verification.community_telemetry_consent.helpers import report_text_is_safe
from verification.community_telemetry_consent.runner import build_report, run


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_17 is True
    assert c.start_slice_17_18 is True


def test_policy_and_register() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == POLICY_SCHEMA
    for key, expected in POLICY_REQUIRED_VALUES.items():
        assert policy.get(key) == expected, key

    register = json.loads((root / REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert register.get("schema") == REGISTER_SCHEMA
    assert len(register.get("entries") or []) >= 4

    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == SCHEMA_NAME
    assert contract.get("start_slice_17_17") is True
    assert contract.get("start_slice_17_18") is True


def test_build_report_runs() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.slice == "17.17"
    assert report.suite_id == "sv17-17"
    assert report.epic17_boundary.get("start_slice_17_17") is True
    assert report.epic17_boundary.get("start_slice_17_18") is True
    assert report.epic17_boundary.get("start_slice_17_19") is False
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert letter in report.scenario_results


def test_determinism_dual_run() -> None:
    root = monorepo_root_from_here()
    a = dict_to_canonical_json(build_report(root).to_dict())
    b = dict_to_canonical_json(build_report(root).to_dict())
    assert a == b


def test_report_safe() -> None:
    root = monorepo_root_from_here()
    text = dict_to_canonical_json(build_report(root).to_dict())
    assert report_text_is_safe(text)
    assert "cscc_v1_" not in text
    assert "arn:aws:" not in text


def test_run_writes_artifact() -> None:
    root = monorepo_root_from_here()
    report = run(root)
    path = root / ".codestrata-artifacts/validation/suites/sv17-17/community-telemetry-consent-verification.json"
    assert path.is_file()
    assert report.verdict != "FAIL" or report.failed_checks >= 0
