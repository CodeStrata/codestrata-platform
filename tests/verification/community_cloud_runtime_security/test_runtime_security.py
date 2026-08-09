"""Tests for Slice 17.6 runtime security verification."""

from __future__ import annotations

import json

from verification.community_cloud_runtime_security.contract import (
    CONTRACT_RELATIVE,
    EXPECTED_PASSWORD_SECRET_ID,
    EXPECTED_REGION,
    EXPECTED_SESSION_SECRET_ID,
    EXPECTED_WRITER_STATUS,
    POLICY_RELATIVE,
    REGISTER_RELATIVE,
    SCHEMA_NAME,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_runtime_security.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.community_cloud_runtime_security.runner import build_report


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_6 is True
    assert c.start_slice_17_7 is True
    assert c.production_ingestion_enabled is False
    assert c.secrets_configured is True
    assert c.provider_credentials_configured is False
    assert c.writer_attached is False
    assert c.region == EXPECTED_REGION


def test_policy_and_register() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == "community-cloud-runtime-security-policy:1.0"
    assert policy.get("start_slice_17_6") is True
    assert policy.get("start_slice_17_7") is True
    assert policy.get("secrets_configured") is True
    assert policy.get("production_ingestion_enabled") is False
    assert policy.get("provider_credentials_configured") is False
    assert EXPECTED_PASSWORD_SECRET_ID in (policy.get("secret_identifiers") or [])
    register = json.loads((root / REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert register.get("schema") == "community-cloud-runtime-security-register:1.0"
    assert register.get("writer_attachment_status") == EXPECTED_WRITER_STATUS
    assert register.get("secret_value_storage") == "secrets_manager_only"
    assert EXPECTED_SESSION_SECRET_ID in (register.get("secret_identifiers") or [])
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == "community-cloud-runtime-security-verification:1.0.0"
    assert contract.get("start_slice_17_6") is True
    assert contract.get("start_slice_17_7") is True
    assert (root / "verification/community_cloud_runtime_security").is_dir()


def test_build_report_limitations_without_operational_evidence() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.epic17_boundary.get("start_slice_17_6") is True
    assert report.epic17_boundary.get("start_slice_17_7") is True
    assert report.policy.get("start_slice_17_6") is True
    assert report.policy.get("start_slice_17_7") is True
    assert report.writer_policy.get("attached") is False
    if not report.evidence.get("secrets_evidence_present"):
        assert report.verdict == "PASS_WITH_LIMITATIONS"
        assert any("secrets_operational" in x for x in report.limitations)
    text = dict_to_canonical_json(report.to_dict())
    assert "/Users/" not in text
    assert "arn:aws:" not in text
    assert '"timestamp"' not in text.lower()


def test_determinism() -> None:
    root = monorepo_root_from_here()
    r1 = build_report(root)
    r2 = build_report(root)
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())


def test_ingestion_and_writer_remain_off() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.ingestion.get("enabled") is False
    assert report.writer_policy.get("attached") is False
    assert report.provider_boundary.get("provider_credentials_configured") is False
