"""Tests for Slice 17.1 CI/CD architecture."""

from __future__ import annotations

import json

from verification.community_cloud_cicd_architecture.contract import (
    CONTRACT_RELATIVE,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_cicd_architecture.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.community_cloud_cicd_architecture.runner import build_report, main


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_1 is True
    assert c.start_slice_17_2 is True
    assert c.production_actions_allowed is False
    assert c.aws_resources_created is False
    assert c.long_lived_aws_keys_allowed is False


def test_policy_and_registers() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == "community-cloud-cicd-policy:1.0"
    assert policy.get("start_slice_17_1") is True
    assert policy.get("start_slice_17_2") is True
    assert policy.get("environment_strategy") == "production_only"
    assert policy.get("lambda_update_strategy") == "ecr_immutable_image_uri_update"
    assert policy.get("vs_code_cli_publication_epic") == 19
    rs = policy.get("remote_state") or {}
    assert rs.get("backend_type") == "s3"
    assert rs.get("locking_method") == "s3_native_lockfile"
    assert rs.get("use_lockfile") is True
    assert rs.get("dynamodb_locking_required") is False
    assert rs.get("dynamodb_table_required") is False
    assert rs.get("community_data_lake_bucket_reuse") is False
    example = (root / "infrastructure/production/backend.tf.example").read_text(encoding="utf-8")
    assert "use_lockfile" in example
    assert "dynamodb_table" not in example
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == "community-cloud-cicd-architecture-verification:1.0.0"
    assert (root / "platform/policies/codestrata_cicd_architecture.json").is_file()
    assert (root / "platform/policies/codestrata_deployment_component_register.json").is_file()
    assert (root / "platform/docs/deployment/community-cloud-cicd-architecture.md").is_file()


def test_slice_17_6_present_and_ci_safe() -> None:
    root = monorepo_root_from_here()
    assert (root / "reports/verification/sv17-6").exists() or (
        root / "verification/community_cloud_runtime_security"
    ).is_dir()
    assert (root / "verification/community_cloud_production_ingestion").is_dir()
    ci = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8").lower()
    assert "tofu apply" not in ci
    assert "uses: aws-actions/configure-aws-credentials" not in ci
    assert (root / ".github/workflows/infrastructure-apply.yml").is_file()
    assert (root / ".github/workflows/infrastructure-plan.yml").is_file()
    plan_wf = (root / ".github/workflows/infrastructure-plan.yml").read_text(encoding="utf-8").lower()
    # Forbid apply commands; allow prose that forbids mutation.
    assert "run: tofu apply" not in plan_wf
    assert "run: terraform apply" not in plan_wf
    assert "tofu apply -auto-approve" not in plan_wf
    assert "plan_only=true" in plan_wf or "plan-only" in plan_wf
    apply_wf = (root / ".github/workflows/infrastructure-apply.yml").read_text(encoding="utf-8")
    active = "\n".join(ln for ln in apply_wf.splitlines() if not ln.lstrip().startswith("#"))
    assert "workflow_dispatch:" in apply_wf
    assert "pull_request:" not in active


def test_build_report() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.epic17_boundary.get("start_slice_17_2") is True
    assert report.policy.get("aws_resources_created") is False
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}
    text = dict_to_canonical_json(report.to_dict())
    assert "/Users/" not in text
    assert '"timestamp"' not in text.lower()
    # After Slice 17.2, scenario W/X semantics are gated by epic17_boundary + policy flags.
    assert report.scenario_results.get("W") is True
    assert report.scenario_results.get("X") is True
    # Core architecture scenarios must still pass
    for letter in "ABCDGHIJKLMNOQRSTUVYZ":
        assert report.scenario_results.get(letter) is True, letter


def test_runner_and_determinism() -> None:
    code = main()
    assert code in {0, 1}
    root = monorepo_root_from_here()
    path = root / "reports/verification/sv17-1/community-cloud-cicd-architecture-verification.json"
    assert path.is_file()
    r1 = build_report(root)
    r2 = build_report(root)
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())
