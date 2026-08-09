"""Tests for Slice 17.3 GitHub OIDC."""

from __future__ import annotations

import json

from verification.community_cloud_github_oidc.contract import (
    CONTRACT_RELATIVE,
    EXPECTED_REGION,
    EXPECTED_ROLE,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_github_oidc.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.community_cloud_github_oidc.runner import build_report


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_3 is True
    assert c.start_slice_17_4 is True
    assert c.start_slice_17_5 is True
    assert c.start_slice_17_6 is True
    assert c.start_slice_17_7 is True
    assert c.region == EXPECTED_REGION
    assert c.long_lived_keys_allowed is False


def test_policy_and_source() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == "community-cloud-github-oidc-policy:1.0"
    assert policy.get("role_name") == EXPECTED_ROLE
    assert policy.get("start_slice_17_4") is True
    assert policy.get("start_slice_17_5") is True
    assert policy.get("start_slice_17_6") is True
    assert policy.get("start_slice_17_7") is True
    assert policy.get("dynamodb_access") is False
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == "community-cloud-github-oidc-verification:1.0.0"
    assert (root / ".github/workflows/aws-identity-check.yml").is_file()
    ci = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "id-token: write" not in ci
    assert (root / "verification/community_cloud_runtime_security").is_dir()


def test_build_report_safe() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.epic17_boundary.get("start_slice_17_5") is True
    assert report.epic17_boundary.get("start_slice_17_6") is True
    assert report.epic17_boundary.get("start_slice_17_7") is True
    text = dict_to_canonical_json(report.to_dict())
    assert "/Users/" not in text
    assert "arn:aws:" not in text
    assert '"timestamp"' not in text.lower()


def test_determinism() -> None:
    root = monorepo_root_from_here()
    r1 = build_report(root)
    r2 = build_report(root)
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())
