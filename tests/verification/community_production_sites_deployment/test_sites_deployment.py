"""Tests for Slice 17.8 production sites deployment verification."""

from __future__ import annotations

import json

from verification.community_production_sites_deployment.contract import (
    CONTRACT_RELATIVE,
    EXPECTED_REPOS,
    EXPORT_TARGETS,
    OIDC_TRANSITIONAL_SUBJECTS,
    POLICY_RELATIVE,
    REGISTER_RELATIVE,
    SCHEMA_NAME,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_production_sites_deployment.determinism import (
    dict_to_canonical_json,
    reports_byte_identical,
)
from verification.community_production_sites_deployment.runner import build_report


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_8 is True
    assert c.start_slice_17_9 is True
    assert c.start_slice_17_10 is True
    assert c.start_slice_17_11 is True
    assert c.start_slice_17_12 is True
    assert getattr(c, "start_slice_17_13", False) is False
    assert c.package_id == "community-production-sites-deployment"
    assert c.package_version == "1.0.0"


def test_policy_and_register_schema() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == "community-production-sites-repository-deployment-policy:1.0"
    assert policy.get("start_slice_17_8") is True
    assert policy.get("start_slice_17_9") is True
    assert policy.get("start_slice_17_10") is True
    assert policy.get("start_slice_17_11") is True
    assert policy.get("start_slice_17_12") is True
    assert policy.get("start_slice_17_13") is False
    assert list((policy.get("export_authority") or {}).get("targets") or []) == list(EXPORT_TARGETS)
    repos = policy.get("repositories") or {}
    for expected in EXPECTED_REPOS:
        key = (
            "infrastructure"
            if expected["name"].endswith("infrastructure")
            else "insights"
            if expected["name"].endswith("insights")
            else "docs"
        )
        assert repos[key]["visibility"] == expected["visibility"]
        assert repos[key]["owner"] == expected["owner"]
    register = json.loads((root / REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert register.get("schema") == "community-production-repository-register:1.0"
    assert len(register.get("entries") or []) == 3
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == "community-production-sites-deployment-verification:1.0.0"
    assert contract.get("start_slice_17_8") is True
    assert contract.get("start_slice_17_9") is True
    assert contract.get("start_slice_17_10") is True
    assert contract.get("start_slice_17_11") is True
    assert contract.get("start_slice_17_12") is True
    assert (root / "verification/community_production_sites_deployment").is_dir()
    mirror = root / "insights/policies/community_production_sites_repository_deployment_policy.json"
    assert mirror.is_file()
    assert mirror.read_bytes() == (root / POLICY_RELATIVE).read_bytes()


def test_build_report_runs() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.slice == "17.8"
    assert report.epic17_boundary.get("start_slice_17_8") is True
    assert report.epic17_boundary.get("start_slice_17_9") is True
    assert report.epic17_boundary.get("start_slice_17_10") is True
    assert report.epic17_boundary.get("start_slice_17_11") is True
    assert report.epic17_boundary.get("start_slice_17_12") is True
    assert report.epic17_boundary.get("start_slice_17_13", False) is False
    assert report.policy.get("start_slice_17_8") is True
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}
    if not report.evidence.get("present"):
        assert report.verdict == "PASS_WITH_LIMITATIONS"


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
    assert report.scenario_results.get("W") is True


def test_oidc_dual_subjects_in_policy() -> None:
    root = monorepo_root_from_here()
    trust = json.loads(
        (root / "platform/policies/codestrata_github_oidc_trust_policy.json").read_text(encoding="utf-8")
    )
    patterns = trust.get("allowed_subject_patterns") or []
    for subject in OIDC_TRANSITIONAL_SUBJECTS:
        assert subject in patterns
