"""Tests for Slice 17.10 production recovery verification."""

from __future__ import annotations

import json

from verification.community_cloud_production_recovery.contract import (
    CLASSIFICATION_RELATIVE,
    CONTRACT_RELATIVE,
    FIXTURES_RELATIVE,
    POLICY_RELATIVE,
    REGISTER_RELATIVE,
    SCHEMA_NAME,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_production_recovery.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.community_cloud_production_recovery.helpers import evaluate_destructive_gate, read_json
from verification.community_cloud_production_recovery.runner import build_report


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_10 is True
    assert c.start_slice_17_11 is True
    assert c.start_slice_17_12 is True
    assert getattr(c, "start_slice_17_13", False) is False
    assert c.production_recovery_ready is True
    assert c.destructive_plan_gate is True
    assert c.data_lake_destroy_forbidden is True
    assert c.remote_state_destroy_forbidden is True
    assert c.final_zero_drift is True
    assert c.package_id == "community-cloud-production-recovery"
    assert c.package_version == "1.0.0"


def test_policy_register_classification_schema() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == "community-cloud-production-recovery-policy:1.0"
    assert policy.get("start_slice_17_10") is True
    assert policy.get("start_slice_17_11") is True
    assert policy.get("start_slice_17_12") is True
    assert policy.get("start_slice_17_13") is False
    assert policy.get("production_recovery_ready") is True
    assert policy.get("publish_allowed") is False
    assert policy.get("tag_allowed") is False
    assert policy.get("commit_required") is False
    assert policy.get("redesign_infrastructure_allowed") is False
    register = json.loads((root / REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert register.get("schema") == "community-cloud-production-recovery-register:1.0"
    assert register.get("start_slice_17_10") is True
    assert register.get("start_slice_17_11") is True
    assert register.get("start_slice_17_12") is True
    assert len(register.get("entries") or []) >= 10
    classification = json.loads((root / CLASSIFICATION_RELATIVE).read_text(encoding="utf-8"))
    assert classification.get("schema") == "community-cloud-resource-recovery-classification:1.0"
    components = {c["component"] for c in classification.get("components") or []}
    for name in (
        "Lambda",
        "API Gateway",
        "ECR",
        "CloudWatch log group",
        "IAM policies",
        "Secrets",
        "Data Lake S3",
        "remote-state S3",
        "GitHub OIDC",
    ):
        assert name in components
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == "community-cloud-production-recovery-verification:1.0.0"
    assert contract.get("start_slice_17_10") is True
    assert contract.get("start_slice_17_11") is True
    assert contract.get("start_slice_17_12") is True
    mirror = root / "insights/policies/community_cloud_production_recovery_policy.json"
    assert mirror.is_file()
    assert mirror.read_bytes() == (root / POLICY_RELATIVE).read_bytes()


def test_destructive_gate_fixtures() -> None:
    root = monorepo_root_from_here()
    fixtures = root / FIXTURES_RELATIVE
    destroy = evaluate_destructive_gate(read_json(fixtures / "plan_destroy.json"))
    replace = evaluate_destructive_gate(read_json(fixtures / "plan_replace.json"))
    inplace = evaluate_destructive_gate(read_json(fixtures / "plan_inplace_update.json"))
    assert destroy["blocked"] is True
    assert replace["blocked"] is True
    assert inplace["blocked"] is False
    assert inplace["allowed"] is True


def test_build_report_runs() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.slice == "17.10"
    assert report.epic17_boundary.get("start_slice_17_10") is True
    assert report.epic17_boundary.get("start_slice_17_11") is True
    assert report.epic17_boundary.get("start_slice_17_12") is True
    assert report.epic17_boundary.get("start_slice_17_13", False) is False
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}
    assert report.destructive_gate.get("destroy_blocked") is True
    assert report.destructive_gate.get("replace_blocked") is True
    assert report.destructive_gate.get("inplace_allowed") is True


def test_determinism_dual_run() -> None:
    root = monorepo_root_from_here()
    r1 = build_report(root)
    r2 = build_report(root)
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())


def test_no_path_or_token_leaks_in_canonical_json() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    text = dict_to_canonical_json(report.to_dict())
    assert "/Users/" not in text
    assert "/home/" not in text
    assert "arn:aws:" not in text
    assert '"timestamp"' not in text.lower()
    assert "ghp_" not in text
    assert "github_pat_" not in text


def test_scenarios_present() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert letter in report.scenario_results


def test_slice_17_13_not_started() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.epic17_boundary.get("start_slice_17_11") is True
    assert report.epic17_boundary.get("start_slice_17_12") is True
    assert report.epic17_boundary.get("start_slice_17_13", False) is False
    assert report.scenario_results.get("S") is True
