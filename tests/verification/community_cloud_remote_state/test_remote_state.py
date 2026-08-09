"""Tests for Slice 17.2 remote-state bootstrap."""

from __future__ import annotations

import json

from verification.community_cloud_remote_state.contract import (
    CONTRACT_RELATIVE,
    EXPECTED_REGION,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_remote_state.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.community_cloud_remote_state.runner import build_report


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_2 is True
    assert c.start_slice_17_3 is True
    assert c.region == EXPECTED_REGION
    assert c.use_lockfile is True
    assert c.dynamodb_required is False


def test_policy_and_source() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == "community-cloud-remote-state-policy:1.0"
    assert policy.get("region") == "us-west-2"
    assert policy.get("use_lockfile") is True
    assert policy.get("dynamodb_required") is False
    assert (root / "verification/community_cloud_runtime_security").is_dir()
    assert policy.get("start_slice_17_4") is True
    assert policy.get("start_slice_17_5") is True
    assert policy.get("start_slice_17_6") is True
    assert policy.get("start_slice_17_7") is True
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == "community-cloud-remote-state-verification:1.0.0"
    example = (root / "infrastructure/production/backend.hcl.example").read_text(encoding="utf-8")
    assert "use_lockfile = true" in example
    assert "dynamodb_table" not in example
    assert "us-west-2" in example


def test_build_report_safe() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.epic17_boundary.get("start_slice_17_3") is True
    assert report.epic17_boundary.get("start_slice_17_4") is True
    assert report.epic17_boundary.get("start_slice_17_5") is True
    assert report.epic17_boundary.get("start_slice_17_6") is True
    assert report.epic17_boundary.get("start_slice_17_7") is True
    assert report.recovery_classification
    text = dict_to_canonical_json(report.to_dict())
    assert "/Users/" not in text
    assert "arn:aws:" not in text
    assert '"timestamp"' not in text.lower()


def test_determinism() -> None:
    root = monorepo_root_from_here()
    r1 = build_report(root)
    r2 = build_report(root)
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())
