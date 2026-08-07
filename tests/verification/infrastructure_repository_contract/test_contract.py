"""Tests for Slice 12.5 Infrastructure repository contract verification."""

from __future__ import annotations

from pathlib import Path

from verification.infrastructure_repository_contract.contract import (
    REPOSITORY_NAME,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.infrastructure_repository_contract.determinism import report_digest
from verification.infrastructure_repository_contract.repository_policy import (
    default_infrastructure_repository_policy,
)
from verification.infrastructure_repository_contract.runner import (
    build_report,
    run_infrastructure_repository_contract_verification,
)


def test_policy_defaults() -> None:
    policy = default_infrastructure_repository_policy()
    assert policy.repository_name == REPOSITORY_NAME
    assert policy.visibility == "private"
    assert policy.git_operations_allowed is False
    assert policy.aws_operations_allowed is False
    assert policy.state_export_allowed is False
    assert policy.dual_authoring_allowed is False
    assert "github.com/" not in str(policy.to_stable_dict())


def test_build_report_contract() -> None:
    report = build_report(monorepo_root_from_here())
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.repository_name == REPOSITORY_NAME
    assert report.repository_visibility == "private"
    assert report.destination_layout_decision.startswith("approach_a")
    assert "modules/community-cloud-api" in report.validation_roots
    assert report.implementation_requirements_for_12_6
    assert report.verification_requirements_for_12_7


def test_runner_twice_byte_identical(tmp_path: Path) -> None:
    root = monorepo_root_from_here()
    a_dir = tmp_path / "a"
    b_dir = tmp_path / "b"
    a = run_infrastructure_repository_contract_verification(output_dir=a_dir, monorepo=root)
    b = run_infrastructure_repository_contract_verification(output_dir=b_dir, monorepo=root)
    assert a.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert b.verdict == a.verdict
    assert report_digest(a) == report_digest(b)
    ja = (a_dir / "infrastructure-repository-contract-verification.json").read_bytes()
    jb = (b_dir / "infrastructure-repository-contract-verification.json").read_bytes()
    assert ja == jb


def test_no_exporter_package_started() -> None:
    root = monorepo_root_from_here()
    assert not (root / "verification" / "infrastructure_repository_export").exists()
    assert not (root / "codestrata-infrastructure").exists()
