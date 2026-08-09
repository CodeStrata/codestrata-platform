"""Tests for Slice 17.7 production ingestion verification."""

from __future__ import annotations

import json

from verification.community_cloud_production_ingestion.contract import (
    CONTRACT_RELATIVE,
    EXPECTED_REGION,
    EXPECTED_STREAMS,
    POLICY_RELATIVE,
    REGISTER_RELATIVE,
    SCHEMA_NAME,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_production_ingestion.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.community_cloud_production_ingestion.runner import build_report


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_7 is True
    assert c.start_slice_17_8 is False
    assert c.production_ingestion_enabled is True
    assert c.client_consent_still_required is True
    assert c.writer_attached is True
    assert c.five_streams_enabled is True
    assert c.report_artifacts_in_lake is False
    assert c.region == EXPECTED_REGION


def test_policy_and_register() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == "community-cloud-production-ingestion-policy:1.0"
    assert policy.get("start_slice_17_7") is True
    assert policy.get("start_slice_17_8") is False
    assert policy.get("production_ingestion_enabled") is True
    assert policy.get("client_consent_still_required") is True
    assert policy.get("writer_attached") is True
    assert list(policy.get("ingestion_streams") or []) == list(EXPECTED_STREAMS)
    register = json.loads((root / REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert register.get("schema") == "community-cloud-production-ingestion-register:1.0"
    assert "writer_attachment_status" in register
    assert "stream_statuses" in register
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == "community-cloud-production-ingestion-verification:1.0.0"
    assert contract.get("start_slice_17_7") is True
    assert contract.get("start_slice_17_8") is False
    assert (root / "verification/community_cloud_production_ingestion").is_dir()


def test_build_report_limitations_without_operational_evidence() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.epic17_boundary.get("start_slice_17_7") is True
    assert report.epic17_boundary.get("start_slice_17_8") is False
    assert report.policy.get("start_slice_17_7") is True
    assert report.policy.get("production_ingestion_enabled") is True
    assert report.policy.get("report_artifacts_in_lake") is False
    if not report.writer_attachment.get("operational_evidence"):
        assert report.verdict == "PASS_WITH_LIMITATIONS"
        assert any("writer_attachment" in x or "activation" in x for x in report.limitations)
    text = dict_to_canonical_json(report.to_dict())
    assert "/Users/" not in text
    assert "arn:aws:" not in text
    assert '"timestamp"' not in text.lower()
    assert "s3://" not in text.lower()


def test_determinism() -> None:
    root = monorepo_root_from_here()
    r1 = build_report(root)
    r2 = build_report(root)
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())


def test_scenarios_present() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert letter in report.scenario_results


def test_slice_17_8_not_started() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.policy.get("start_slice_17_8") is False
    assert report.scenario_results.get("W") is True
