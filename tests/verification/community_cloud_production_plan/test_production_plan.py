"""Tests for Slice 17.4 production plan verification."""

from __future__ import annotations

import json

from verification.community_cloud_production_plan.contract import (
    CONTRACT_RELATIVE,
    EXPECTED_REGION,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_production_plan.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.community_cloud_production_plan.runner import build_report


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_4 is True
    assert c.start_slice_17_5 is True
    assert c.start_slice_17_6 is True
    assert c.start_slice_17_7 is True
    assert c.plan_only is True
    assert c.product_apply is False
    assert c.region == EXPECTED_REGION
    assert c.production_ingestion_enabled is False


def test_policy() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == "community-cloud-production-plan-policy:1.0"
    assert policy.get("start_slice_17_4") is True
    assert policy.get("start_slice_17_5") is True
    assert policy.get("start_slice_17_6") is True
    assert policy.get("start_slice_17_7") is True
    assert policy.get("plan_only") is True
    assert policy.get("product_apply") is False
    assert policy.get("production_ingestion_enabled") is False
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == "community-cloud-production-plan-verification:1.0.0"
    assert contract.get("start_slice_17_5") is True
    assert contract.get("start_slice_17_6") is True
    assert contract.get("start_slice_17_7") is True
    assert (root / "verification/community_cloud_runtime_security").is_dir()
    assert (root / ".github/workflows/infrastructure-plan.yml").is_file()


def test_build_report_safe() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.epic17_boundary.get("start_slice_17_5") is True
    assert report.epic17_boundary.get("start_slice_17_6") is True
    assert report.epic17_boundary.get("start_slice_17_7") is True
    assert report.policy.get("start_slice_17_5") is True
    assert report.policy.get("start_slice_17_6") is True
    assert report.policy.get("start_slice_17_7") is True
    text = dict_to_canonical_json(report.to_dict())
    assert "/Users/" not in text
    assert "arn:aws:" not in text
    assert '"timestamp"' not in text.lower()


def test_determinism() -> None:
    root = monorepo_root_from_here()
    r1 = build_report(root)
    r2 = build_report(root)
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())


def test_start_slice_17_6_gate_open() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.policy.get("start_slice_17_6") is True
    assert report.policy.get("start_slice_17_7") is True
    assert (root / "verification/community_cloud_runtime_security").is_dir()
    wf = (root / ".github/workflows/infrastructure-plan.yml").read_text(encoding="utf-8").lower()
    assert "tofu apply" not in "\n".join(
        ln for ln in wf.splitlines() if not ln.lstrip().startswith("#")
    )
