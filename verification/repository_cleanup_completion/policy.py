"""Completion policy checks."""

from __future__ import annotations

from pathlib import Path

from verification.repository_cleanup_completion.contract import (
    CONTRACT_RELATIVE,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
)
from verification.repository_cleanup_completion.helpers import add_check, load_json
from verification.repository_cleanup_completion.models import CheckResult, Defect


def check_completion_policy(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / POLICY_RELATIVE
    add_check(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    if not path.is_file():
        return checks, defects, {}
    policy = load_json(path)
    add_check(checks, defects, "policy:schema", policy.get("schema") == POLICY_SCHEMA, str(policy.get("schema")), "policy")
    add_check(checks, defects, "policy:epic_complete", policy.get("epic_complete") is True, str(policy.get("epic_complete")), "policy")
    add_check(checks, defects, "policy:slice_count_10", policy.get("slice_count") == 10, str(policy.get("slice_count")), "policy")
    add_check(
        checks,
        defects,
        "policy:start_slice_16_10_true",
        policy.get("start_slice_16_10", False) is True,
        str(policy.get("start_slice_16_10")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:start_epic_17_true",
        policy.get("start_epic_17", False) is True,
        str(policy.get("start_epic_17")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:start_slice_17_2_true",
        policy.get("start_slice_17_2", False) is True,
        str(policy.get("start_slice_17_2")),
        "policy",
        classification="slice_17_4_started",
    )
    for key in (
        "repository_inventory_complete",
        "documentation_cleanup_complete",
        "code_cleanup_complete",
        "asset_design_cleanup_complete",
        "dependency_build_cleanup_complete",
        "storage_generated_cleanup_complete",
        "boundary_residency_complete",
        "repository_consistency_complete",
        "package_release_validation_complete",
        "public_private_boundaries_valid",
        "generated_artifact_hygiene_valid",
        "standalone_exports_valid",
        "owner_review_items_explicit",
        "repository_cleanup_complete",
    ):
        add_check(checks, defects, f"policy:{key}", policy.get(key) is True, str(policy.get(key)), "policy")
    for key in (
        "repository_cutover_performed",
        "remote_repositories_created",
        "published",
        "deployed",
        "commit_created",
        "tag_created",
        "production_deployment_complete",
        "transparency_documentation_complete",
        "v0_2_0_release_complete",
        "production_ingestion_enabled",
    ):
        add_check(checks, defects, f"policy:{key}_false", policy.get(key) is False, str(policy.get(key)), "policy")
    mirror = monorepo / "insights/policies/repository_cleanup_completion_policy.json"
    add_check(
        checks,
        defects,
        "policy:insights_mirror_identical",
        mirror.is_file() and mirror.read_bytes() == path.read_bytes(),
        "insights mirror",
        "policy",
    )
    cpath = monorepo / CONTRACT_RELATIVE
    add_check(checks, defects, "contract:exists", cpath.is_file(), CONTRACT_RELATIVE, "policy")
    return checks, defects, policy
