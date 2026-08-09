"""Tests for Slice 17.5 infrastructure deployment verification."""

from __future__ import annotations

import json

from verification.community_cloud_infrastructure_deployment.contract import (
    CONTRACT_RELATIVE,
    EXPECTED_REGION,
    POLICY_RELATIVE,
    REGISTER_RELATIVE,
    SCHEMA_NAME,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_infrastructure_deployment.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.community_cloud_infrastructure_deployment.runner import build_report


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_5 is True
    assert c.start_slice_17_6 is True
    assert c.start_slice_17_7 is True
    assert c.production_ingestion_enabled is False
    assert c.writer_attached is False
    assert c.secrets_configured is False
    assert c.region == EXPECTED_REGION


def test_policy_and_register() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == "community-cloud-infrastructure-deployment-policy:1.0"
    assert policy.get("start_slice_17_5") is True
    assert policy.get("start_slice_17_6") is True
    assert policy.get("start_slice_17_7") is True
    assert policy.get("production_ingestion_enabled") is False
    register = json.loads((root / REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert register.get("schema") == "community-cloud-production-deployment-register:1.0"
    assert register.get("planned_resource_count") == 21
    assert register.get("ingestion_enabled") is False
    assert register.get("writer_attached") is False
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == "community-cloud-infrastructure-deployment-verification:1.0.0"
    assert contract.get("start_slice_17_5") is True
    assert contract.get("start_slice_17_6") is True
    assert contract.get("start_slice_17_7") is True
    assert (root / "verification/community_cloud_runtime_security").is_dir()
    assert (root / ".github/workflows/infrastructure-apply.yml").is_file()
    wf = (root / ".github/workflows/infrastructure-apply.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in wf
    assert "pull_request:" not in "\n".join(
        ln for ln in wf.splitlines() if not ln.lstrip().startswith("#")
    )


def test_build_report_fail_closed_when_not_deployed() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.epic17_boundary.get("start_slice_17_6") is True
    assert report.epic17_boundary.get("start_slice_17_7") is True
    assert report.policy.get("start_slice_17_5") is True
    assert report.policy.get("start_slice_17_6") is True
    assert report.policy.get("start_slice_17_7") is True
    # Until apply evidence exists, verdict must fail closed (not invent success).
    if not report.apply.get("deployed"):
        assert report.verdict == "FAIL"
        assert report.apply.get("actual_resource_count", 0) == 0
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
    assert report.writer.get("attached") is False
    assert report.secrets.get("secrets_configured") is False
    df = (root / "platform/deployment/community-cloud-api/Dockerfile").read_text(encoding="utf-8")
    assert "CODESTRATA_INGESTION_ENABLED=false" in df
