"""Tests for Slice 15.4 ingestion verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_insights_ingestion.contract import (
    ACTIVATION_STATE,
    PACKAGE_ECOSYSTEMS,
    POLICY_ID,
    POLICY_RELATIVE,
    PROVIDER_FAMILIES,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.community_insights_ingestion.determinism import (
    reports_byte_identical,
)
from verification.community_insights_ingestion.inventory import load_json
from verification.community_insights_ingestion.reporting import write_report
from verification.community_insights_ingestion.runner import build_report
from verification.community_insights_ingestion.scenarios import INGESTION_SCENARIOS


def test_policy() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert policy["policy_id"] == POLICY_ID
    assert policy["policy_version"] == "1.0"
    assert policy["operational_activation_state"] == ACTIVATION_STATE
    assert policy["enable_ingestion_wire"] is False
    assert policy.get("start_slice_16_2", False) is False


def test_change_register_disposition() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    for cr in ("CR-15.3-001", "CR-15.3-002", "CR-15.3-003"):
        row = policy["change_register_disposition"][cr]
        assert row["status"] == "implemented_in_15_4"
        assert row["activated_in_contract"] is True
        assert row["activated_in_production_wire"] is False


def test_ecosystem_and_providers() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert tuple(policy["package_ecosystem"]["closed_vocabulary"]) == PACKAGE_ECOSYSTEMS
    assert tuple(policy["provider_family"]["canonical"]) == PROVIDER_FAMILIES
    assert policy["provider_family"]["openrouter_present"] is True


def test_scenarios_a_to_z() -> None:
    assert len(INGESTION_SCENARIOS) == 26
    assert INGESTION_SCENARIOS[0][0] == "A"
    assert INGESTION_SCENARIOS[-1][0] == "Z"


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.release_posture.get("start_slice_16_2", False) is False
    assert report.release_posture["enable_ingestion_wire"] is False
    path = write_report(monorepo, report)
    text = Path(path).read_text(encoding="utf-8")
    assert "timestamp" not in text.lower()
    assert "/Users/" not in text
    assert "sk-live" not in text


def test_determinism() -> None:
    monorepo = monorepo_root_from_here()
    a = build_report(monorepo).to_dict()
    b = build_report(monorepo).to_dict()
    assert reports_byte_identical(a, b)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
