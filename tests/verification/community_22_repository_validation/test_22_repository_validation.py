"""Tests for Slice 17.13 verification package."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_22_repository_validation.catalog import (
    CatalogSelectionError,
    load_release_validation_repositories,
)
from verification.community_22_repository_validation.contract import (
    CONTRACT_RELATIVE,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    REPOSITORY_TARGET,
    RESULT_REGISTER_RELATIVE,
    SUITE_REGISTER_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_22_repository_validation.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.community_22_repository_validation.runner import build_report
from verification.community_22_repository_validation.security import (
    classify_text,
    register_entry_is_safe,
    validate_public_clone_url,
)


def test_contract_defaults() -> None:
    c = default_contract()
    assert c.start_slice_17_13 is True
    assert c.start_slice_17_14 is False
    assert c.repository_target == REPOSITORY_TARGET


def test_policy_files_exist_and_parse() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == POLICY_SCHEMA
    assert policy.get("start_slice_17_13") is True
    assert policy.get("start_slice_17_14") is False
    assert policy.get("repository_target") == REPOSITORY_TARGET
    assert policy.get("data_lake_report_storage") is False

    suite_register = json.loads((root / SUITE_REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert suite_register.get("schema") == "community-validation-suite-register:1.0"
    assert suite_register.get("suite_id") == "sv17-13"

    result_register = json.loads((root / RESULT_REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert result_register.get("schema") == "community-validation-repository-result-register:1.0"
    safe_fields = result_register.get("safe_fields") or []
    assert "repository_validation_id" in safe_fields
    assert "limitations" in safe_fields
    forbidden = result_register.get("forbidden_fields") or []
    assert "aws_account_id" in forbidden
    assert "s3_uri" in forbidden

    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("start_slice_17_13") is True
    assert contract.get("start_slice_17_14") is False


def test_catalog_returns_exactly_22() -> None:
    root = monorepo_root_from_here()
    repos = load_release_validation_repositories(root)
    assert len(repos) == REPOSITORY_TARGET
    ids = [r.repository_id for r in repos]
    assert ids == sorted(ids)
    assert len(set(ids)) == REPOSITORY_TARGET


def test_catalog_rejects_cherry_picking() -> None:
    root = monorepo_root_from_here()
    repos = load_release_validation_repositories(root)
    subset = (repos[0].repository_id,)
    try:
        load_release_validation_repositories(root, repository_ids=subset)
        raise AssertionError("expected CatalogSelectionError")
    except CatalogSelectionError:
        pass


def test_catalog_selection_deterministic() -> None:
    root = monorepo_root_from_here()
    r1 = load_release_validation_repositories(root)
    r2 = load_release_validation_repositories(root)
    assert [r.repository_id for r in r1] == [r.repository_id for r in r2]


def test_build_report_deterministic() -> None:
    root = monorepo_root_from_here()
    r1 = build_report(root, skip_execute=True)
    r2 = build_report(root, skip_execute=True)
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())
    assert r1.catalog_count == REPOSITORY_TARGET
    assert r1.suite_execution_status == "not_executed"
    assert r1.epic17_boundary.get("start_slice_17_14") is False


def test_scenarios_negative_codes_a_to_z_exist() -> None:
    root = monorepo_root_from_here()
    report = build_report(root, skip_execute=True)
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert letter in report.scenario_results


def test_security_preflight_does_not_leak_secrets() -> None:
    secret_sample = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"
    labels = classify_text(secret_sample)
    assert labels
    ok, _ = validate_public_clone_url("https://github.com/org/repo")
    assert ok
    ok, _ = validate_public_clone_url(f"https://user:{secret_sample}@github.com/org/repo")
    assert not ok
    safe, _ = register_entry_is_safe(
        {
            "repository_validation_id": "demo",
            "assessment_status": "not_executed",
            "limitations": [],
        }
    )
    assert safe
    unsafe, detail = register_entry_is_safe({"pat": "hidden"})
    assert not unsafe
    assert "forbidden" in detail


def test_build_report_no_path_or_token_leaks() -> None:
    root = monorepo_root_from_here()
    report = build_report(root, skip_execute=True)
    text = dict_to_canonical_json(report.to_dict())
    assert "/Users/" not in text
    assert "/home/" not in text
    assert "arn:aws:" not in text
    assert "ghp_" not in text
    assert "github_pat_" not in text
    assert "s3://" not in text
